"""
report_data_loader.py - Grounded Data Ingestion Layer (Layer 1) for Module D.

Loads reconciled dashboard data and raw operational CSV datasets, providing
time-window slicing (ISO weeks or full consolidated period) and sector-specific
analytical context payloads for the 5 business areas and general C-Level executive memo.
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import yaml


def load_config(config_path: str = "config/report_config.yaml") -> Dict[str, Any]:
    """Loads configuration yaml file."""
    if not os.path.exists(config_path):
        # Fallback to local
        alt_path = os.path.join(os.path.dirname(__file__), "config", "report_config.yaml")
        if os.path.exists(alt_path):
            config_path = alt_path
        else:
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_grounded_json(json_path: str = "dashboard/data/dashboard_data.json") -> Dict[str, Any]:
    """Loads audited dashboard JSON."""
    if not os.path.exists(json_path):
        alt_path = os.path.join(os.path.dirname(__file__), "dashboard", "data", "dashboard_data.json")
        if os.path.exists(alt_path):
            json_path = alt_path
        else:
            raise FileNotFoundError(f"Audited dashboard JSON not found at {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


class ReportDataLoader:
    """
    Ingests and provides structured data payloads filtered by timeframe (week / consolidated)
    and business sector (vendas, estoque, atendimento, marketing, clientes, all).
    """

    def __init__(
        self,
        base_dir: str = ".",
        json_path: str = "dashboard/data/dashboard_data.json",
        config_path: str = "config/report_config.yaml"
    ):
        self.base_dir = base_dir
        self.config = load_config(config_path)
        self.dashboard_data = load_grounded_json(json_path)

        # Lazy loaded DataFrames for performance
        self._df_vendas: Optional[pd.DataFrame] = None
        self._df_estoque: Optional[pd.DataFrame] = None
        self._df_atendimento: Optional[pd.DataFrame] = None
        self._df_clientes: Optional[pd.DataFrame] = None
        self._df_marketing: Optional[pd.DataFrame] = None
        self._available_weeks: Optional[List[str]] = None

    def _get_csv_path(self, filename: str) -> str:
        direct = os.path.join(self.base_dir, filename)
        if os.path.exists(direct):
            return direct
        treated = os.path.join(self.base_dir, "dados_tratados", filename)
        if os.path.exists(treated):
            return treated
        raise FileNotFoundError(f"CSV file '{filename}' not found in {self.base_dir} or dados_tratados/")

    @property
    def df_vendas(self) -> pd.DataFrame:
        if self._df_vendas is None:
            path = self._get_csv_path("vendas.csv")
            df = pd.read_csv(path)
            df["data_pedido"] = pd.to_datetime(df["data_pedido"])
            df["iso_week"] = df["data_pedido"].dt.strftime("%G-W%V")
            self._df_vendas = df
        return self._df_vendas

    @property
    def df_atendimento(self) -> pd.DataFrame:
        if self._df_atendimento is None:
            path = self._get_csv_path("atendimento.csv")
            df = pd.read_csv(path)
            df["data_abertura"] = pd.to_datetime(df["data_abertura"])
            df["iso_week"] = df["data_abertura"].dt.strftime("%G-W%V")
            self._df_atendimento = df
        return self._df_atendimento

    @property
    def df_marketing(self) -> pd.DataFrame:
        if self._df_marketing is None:
            path = self._get_csv_path("marketing.csv")
            df = pd.read_csv(path)
            df["data_inicio"] = pd.to_datetime(df["data_inicio"])
            df["data_fim"] = pd.to_datetime(df["data_fim"])
            self._df_marketing = df
        return self._df_marketing

    @property
    def df_estoque(self) -> pd.DataFrame:
        if self._df_estoque is None:
            path = self._get_csv_path("estoque.csv")
            self._df_estoque = pd.read_csv(path)
        return self._df_estoque

    @property
    def df_clientes(self) -> pd.DataFrame:
        if self._df_clientes is None:
            path = self._get_csv_path("clientes.csv")
            self._df_clientes = pd.read_csv(path)
        return self._df_clientes

    def get_available_weeks(self) -> List[str]:
        """Returns sorted list of all unique ISO weeks available in the sales dataset."""
        if self._available_weeks is None:
            weeks = sorted(self.df_vendas["iso_week"].unique().tolist())
            self._available_weeks = weeks
        return self._available_weeks

    def resolve_week(self, week_input: str) -> str:
        """
        Resolves aliases like 'latest', 'default', 'consolidated' or validates ISO week.
        """
        w = week_input.strip()
        available = self.get_available_weeks()
        if w.lower() in ("consolidated", "all", "periodo", "total"):
            return "consolidated"
        if w.lower() in ("latest", "last", "atual"):
            return available[-1] if available else "2024-W04"
        if w.lower() in ("default", "demo", "black_friday"):
            return self.config["historical_dataset"].get("default_demo_week", "2023-W47")

        if w not in available:
            # Check if week format matches YYYY-WNN
            import re
            if re.match(r"^\d{4}-W\d{2}$", w):
                return w
            raise ValueError(
                f"Invalid week '{week_input}'. Choose a valid ISO week (e.g., '2023-W47'), "
                f"'latest' or 'consolidated'."
            )
        return w

    def get_previous_week(self, week: str) -> Optional[str]:
        """Returns the chronological preceding week for WoW calculations."""
        if week == "consolidated":
            return None
        available = self.get_available_weeks()
        if week in available:
            idx = available.index(week)
            if idx > 0:
                return available[idx - 1]
        return None

    def get_vendas_data(self, week: str) -> Dict[str, Any]:
        """Computes sales sector metrics for given week or consolidated period."""
        if week == "consolidated":
            dre = self.dashboard_data["dre"]["summary"]
            return {
                "periodo": "Consolidado 13 Meses (Jan/2023 - Jan/2024)",
                "receita_bruta": float(dre["gross_revenue"]),
                "pedidos": int(dre["total_orders"]),
                "receita_liquida": float(self.dashboard_data["dre"]["waterfall_items"][2]["period_13m"]),
                "descontos": float(dre["discounts_total"]),
                "taxa_desconto_pct": float(dre["discounts_pct"]),
                "cmv": float(abs(self.dashboard_data["dre"]["waterfall_items"][3]["period_13m"])),
                "frete": float(abs(self.dashboard_data["dre"]["waterfall_items"][4]["period_13m"])),
                "margem_contribuicao": float(dre["contribution_margin"]),
                "margem_contribuicao_pct": float(dre["contribution_margin_pct"]),
                "ticket_medio": float(dre["gross_revenue"] / dre["total_orders"]),
                "devolucoes": 4127,
                "taxa_devolucao_pct": 14.87,
            }

        df = self.df_vendas[self.df_vendas["iso_week"] == week]
        pedidos = len(df)
        if pedidos == 0:
            return {
                "periodo": week,
                "receita_bruta": 0.0,
                "pedidos": 0,
                "receita_liquida": 0.0,
                "descontos": 0.0,
                "taxa_desconto_pct": 0.0,
                "cmv": 0.0,
                "frete": 0.0,
                "margem_contribuicao": 0.0,
                "margem_contribuicao_pct": 0.0,
                "ticket_medio": 0.0,
                "devolucoes": 0,
                "taxa_devolucao_pct": 0.0,
            }

        rec_bruta = float(df["receita_bruta"].sum())
        desconto = float(df["desconto_reais"].sum())
        rec_liq = float(df["receita_liquida"].sum())
        cmv = float(df["custo_produto"].sum())
        frete = float(df["custo_frete"].sum())
        margem = float(df["margem_contribuicao"].sum())
        devs = int(df["devolvido"].sum())

        return {
            "periodo": week,
            "receita_bruta": round(rec_bruta, 2),
            "pedidos": pedidos,
            "receita_liquida": round(rec_liq, 2),
            "descontos": round(desconto, 2),
            "taxa_desconto_pct": round((desconto / rec_bruta * 100.0) if rec_bruta > 0 else 0.0, 2),
            "cmv": round(cmv, 2),
            "frete": round(frete, 2),
            "margem_contribuicao": round(margem, 2),
            "margem_contribuicao_pct": round((margem / rec_bruta * 100.0) if rec_bruta > 0 else 0.0, 2),
            "ticket_medio": round(rec_bruta / pedidos if pedidos > 0 else 0.0, 2),
            "devolucoes": devs,
            "taxa_devolucao_pct": round((devs / pedidos * 100.0) if pedidos > 0 else 0.0, 2),
        }

    def get_estoque_data(self) -> Dict[str, Any]:
        """Provides inventory grounding figures (structural snapshot from audit)."""
        inv = self.dashboard_data["inventory"]
        return {
            "total_skus": inv["total_skus"],
            "unidades_fisicas": inv["total_physical_units"],
            "custo_total_fisico": inv["total_physical_cost"],
            "excesso_defensivo": inv["excess_defensive_cost"],
            "excesso_wacc_cost": inv.get("excess_stock_wacc_cost", round(inv["excess_defensive_cost"] * 0.18, 2)),
            "skus_descontinuados": inv["discontinued_skus"],
            "capital_descontinuado": inv["discontinued_capital"],
            "economia_wacc_18pct": inv["discontinued_wacc_saving_18pct"],
            "status_distribution": inv["status_distribution"],
            "category_distribution": inv["category_distribution"],
            "giro_anual": 0.022,
            "cobertura_anos": 45.0
        }

    def get_atendimento_data(self, week: str) -> Dict[str, Any]:
        """Computes customer service metrics for given week or consolidated period."""
        if week == "consolidated":
            cs = self.dashboard_data["customer_service"]
            cats = {c["categoria_normalizada"]: c for c in cs["categories"]}
            wismo = cats.get("Onde está meu pedido?", {})
            return {
                "periodo": "Consolidado 13 Meses",
                "total_tickets": cs["total_tickets"],
                "custo_total": cs["total_cost"],
                "wismo_tickets": wismo.get("tickets", 10765),
                "wismo_share_pct": wismo.get("share_pct", 30.04),
                "wismo_potencial_ia_pct": wismo.get("potencial_ia_pct", 90.0),
                "taxa_deflexao_global_pct": cs["deflection_rate_pct"],
                "economia_potencial_ia": cs["annual_savings"],
                "horas_poupadas": cs["human_hours_saved"],
                "categories": cs["categories"]
            }

        df = self.df_atendimento[self.df_atendimento["iso_week"] == week]
        tickets = len(df)
        if tickets == 0:
            return {
                "periodo": week,
                "total_tickets": 0,
                "custo_total": 0.0,
                "wismo_tickets": 0,
                "wismo_share_pct": 0.0,
                "csat_medio": 0.0,
                "frt_medio_minutos": 0.0
            }

        def clean_category(cat: str) -> str:
            c = str(cat).lower()
            if "pedido" in c or "rastre" in c:
                return "Onde está meu pedido?"
            elif "defeito" in c:
                return "Produto com defeito"
            elif "tamanho" in c:
                return "Troca de tamanho"
            return "Outros"

        df_cat = df["categoria_problema"].apply(clean_category)
        wismo_count = int((df_cat == "Onde está meu pedido?").sum())
        custo = float(df["custo_operacional_ticket"].sum())
        csat = float(df["nota_csat"].dropna().mean()) if not df["nota_csat"].dropna().empty else 0.0
        frt = float(df["tempo_primeira_resposta_minutos"].dropna().mean()) if not df["tempo_primeira_resposta_minutos"].dropna().empty else 0.0

        return {
            "periodo": week,
            "total_tickets": tickets,
            "custo_total": round(custo, 2),
            "wismo_tickets": wismo_count,
            "wismo_share_pct": round((wismo_count / tickets * 100.0) if tickets > 0 else 0.0, 2),
            "csat_medio": round(csat, 2),
            "frt_medio_minutos": round(frt, 1)
        }

    def get_marketing_data(self) -> Dict[str, Any]:
        """Provides marketing channels, ROAS and weighted CAC figures."""
        channels = self.dashboard_data["channels"]
        top_roas = max(channels, key=lambda c: c.get("roas", 0))
        top_cac = min([c for c in channels if c.get("cac_weighted")], key=lambda c: c.get("cac_weighted", 999))
        return {
            "channels": channels,
            "top_roas_canal": top_roas["canal"],
            "top_roas_valor": top_roas["roas"],
            "top_cac_canal": top_cac["canal"],
            "top_cac_valor": top_cac["cac_weighted"],
            "influenciador": [c for c in channels if c["canal"] == "Influenciador"][0],
            "tiktok": [c for c in channels if c["canal"] == "TikTok Ads"][0],
            "marketplace": [c for c in channels if c["canal"] == "Marketplace"][0],
            "google_ads": [c for c in channels if c["canal"] == "Google Ads"][0],
        }

    def get_clientes_data(self) -> Dict[str, Any]:
        """Provides RFM customer segmentation and Pareto LTV concentration data."""
        rfm = self.dashboard_data["customers_rfm"]
        return {
            "total_clientes": rfm["total_customers"],
            "total_ltv": rfm["total_ltv"],
            "pareto_top_20_ltv_share": rfm.get("pareto", {}).get("top_20_ltv_share_pct", 61.05),
            "segments": rfm["segments"],
            "champions": [s for s in rfm["segments"] if "camp" in s["segmento_rfm"].lower()][0],
            "loyal": [s for s in rfm["segments"] if "fiel" in s["segmento_rfm"].lower()][0],
        }

    def get_sector_payload(self, sector: str, week: str = "consolidated") -> Dict[str, Any]:
        """
        Consolidates metrics for the specified sector, calculating WoW if a week is given.
        """
        resolved_week = self.resolve_week(week)
        prev_week = self.get_previous_week(resolved_week)

        if sector == "vendas":
            current = self.get_vendas_data(resolved_week)
            previous = self.get_vendas_data(prev_week) if prev_week else None
            return {
                "sector": "vendas",
                "config": self.config["sectors"]["vendas"],
                "week": resolved_week,
                "prev_week": prev_week,
                "current": current,
                "previous": previous
            }

        elif sector == "estoque":
            return {
                "sector": "estoque",
                "config": self.config["sectors"]["estoque"],
                "week": resolved_week,
                "data": self.get_estoque_data()
            }

        elif sector == "atendimento":
            current = self.get_atendimento_data(resolved_week)
            previous = self.get_atendimento_data(prev_week) if prev_week else None
            return {
                "sector": "atendimento",
                "config": self.config["sectors"]["atendimento"],
                "week": resolved_week,
                "prev_week": prev_week,
                "current": current,
                "previous": previous
            }

        elif sector == "marketing":
            return {
                "sector": "marketing",
                "config": self.config["sectors"]["marketing"],
                "week": resolved_week,
                "data": self.get_marketing_data()
            }

        elif sector == "clientes":
            return {
                "sector": "clientes",
                "config": self.config["sectors"]["clientes"],
                "week": resolved_week,
                "data": self.get_clientes_data()
            }

        elif sector == "all":
            vendas = self.get_sector_payload("vendas", resolved_week)
            estoque = self.get_sector_payload("estoque", resolved_week)
            atendimento = self.get_sector_payload("atendimento", resolved_week)
            marketing = self.get_sector_payload("marketing", resolved_week)
            clientes = self.get_sector_payload("clientes", resolved_week)
            return {
                "sector": "all",
                "week": resolved_week,
                "prev_week": prev_week,
                "vendas": vendas,
                "estoque": estoque,
                "atendimento": atendimento,
                "marketing": marketing,
                "clientes": clientes,
                "dre": self.dashboard_data["dre"]["summary"],
                "ice_levers": self.dashboard_data.get("ice_levers", [])
            }

        else:
            raise ValueError(f"Unknown sector '{sector}'. Choose from: vendas, estoque, atendimento, marketing, clientes, all.")
