"""
weekly_analyzer.py - Analytical & Diagnostic Engine (Layer 2) for Module D.

Performs deterministic mathematical analysis:
1. Week-over-Week (WoW) variations and percentage changes.
2. Volume vs Price variance decomposition.
3. Automated anomaly detection against configurable strategic thresholds.
4. Risk classification (CRITICO, ALERTA, ESTAVEL, POSITIVO).
5. Grounded action levers mapping based on the Diagnóstico Final.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class AnomalyAlert:
    sector: str
    metric: str
    current_value: float
    threshold_value: float
    severity: str  # CRITICO, ALERTA, ESTAVEL, POSITIVO
    headline: str
    grounded_evidence: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GroundedLever:
    rank: int
    title: str
    sector: str
    primary_bottleneck: str
    grounded_metric: str
    origin_test: str
    strategic_mandate: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WeeklyAnalyzer:
    """
    Analyzes raw loader payloads and enriches them with analytical variations,
    anomaly diagnostics, and grounded lever alignments.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get("thresholds", {})

    def compute_wow(self, current_val: float, previous_val: Optional[float]) -> Dict[str, Any]:
        """Calculates absolute delta and percentage variation."""
        if previous_val is None or previous_val == 0.0:
            return {
                "absolute_delta": 0.0,
                "pct_change": 0.0,
                "direction": "stable",
                "has_previous": False
            }
        abs_delta = current_val - previous_val
        pct_change = (abs_delta / abs(previous_val)) * 100.0
        direction = "up" if abs_delta > 0 else ("down" if abs_delta < 0 else "stable")
        return {
            "absolute_delta": round(abs_delta, 2),
            "pct_change": round(pct_change, 2),
            "direction": direction,
            "has_previous": True
        }

    def analyze_vendas(self, vendas_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs analytical enrichment on sales metrics."""
        curr = vendas_payload["current"]
        prev = vendas_payload.get("previous")

        rec_wow = self.compute_wow(curr["receita_bruta"], prev["receita_bruta"] if prev else None)
        ped_wow = self.compute_wow(curr["pedidos"], prev["pedidos"] if prev else None)
        tm_wow = self.compute_wow(curr["ticket_medio"], prev["ticket_medio"] if prev else None)
        margem_wow = self.compute_wow(curr["margem_contribuicao_pct"], prev["margem_contribuicao_pct"] if prev else None)
        desc_wow = self.compute_wow(curr["taxa_desconto_pct"], prev["taxa_desconto_pct"] if prev else None)

        # Variance decomposition: Volume vs Ticket
        if prev and prev["pedidos"] > 0:
            delta_volume = (curr["pedidos"] - prev["pedidos"]) * prev["ticket_medio"]
            delta_price = curr["pedidos"] * (curr["ticket_medio"] - prev["ticket_medio"])
        else:
            delta_volume = 0.0
            delta_price = 0.0

        # Anomaly checks
        alerts: List[AnomalyAlert] = []
        desc_threshold = self.thresholds.get("discount_rate_alert_pct", 8.0)
        desc_critical = self.thresholds.get("discount_rate_critical_pct", 9.0)

        if curr["taxa_desconto_pct"] >= desc_critical:
            alerts.append(AnomalyAlert(
                sector="vendas",
                metric="taxa_desconto_pct",
                current_value=curr["taxa_desconto_pct"],
                threshold_value=desc_critical,
                severity="CRITICO",
                headline="Concessão crítica de descontos comerciais",
                grounded_evidence=f"Desconto atingiu {curr['taxa_desconto_pct']:.2f}% (limite crítico {desc_critical:.1f}%)."
            ))
        elif curr["taxa_desconto_pct"] >= desc_threshold:
            alerts.append(AnomalyAlert(
                sector="vendas",
                metric="taxa_desconto_pct",
                current_value=curr["taxa_desconto_pct"],
                threshold_value=desc_threshold,
                severity="ALERTA",
                headline="Erosão de margem por desconto acima do teto",
                grounded_evidence=f"Taxa de desconto de {curr['taxa_desconto_pct']:.2f}% superou o teto preventivo de {desc_threshold:.1f}%."
            ))

        # Grounded levers for sales
        levers = [
            GroundedLever(
                rank=2,
                title="Piso de Frete Mínimo (R$ 150) & Repasse de Frete em Marketplace",
                sector="vendas",
                primary_bottleneck="Subsídio abusivo de frete corroendo margem em pedidos de baixo ticket.",
                grounded_metric="741 transações em margem negativa identificadas no diagnóstico; frete atinge 4,55% da receita.",
                origin_test="Teste 1.2 (Margem por Canal & Faixa de Ticket) & Alavanca ICE #2",
                strategic_mandate="Extinguir frete grátis abaixo de R$ 150 e estancar transações deficitárias de canal terceiro."
            ),
            GroundedLever(
                rank=6,
                title="Calibragem de Desconto Comercial & Trava de Margem",
                sector="vendas",
                primary_bottleneck="Descontos promocionais excessivos em campanhas sazonais comprimindo a DRE.",
                grounded_metric="R$ 1.636.799,83 em descontos (7,97% da receita); pico de 9,55% na Black Friday.",
                origin_test="Teste 1.1 (DRE & Composição da Margem de Contribuição)",
                strategic_mandate="Instituir trava sistêmica de desconto máximo com alçada executiva obrigatória."
            )
        ]

        return {
            "metrics": curr,
            "previous_metrics": prev,
            "variations": {
                "receita": rec_wow,
                "pedidos": ped_wow,
                "ticket_medio": tm_wow,
                "margem_pct": margem_wow,
                "desconto_pct": desc_wow
            },
            "variance_decomposition": {
                "delta_volume_reais": round(delta_volume, 2),
                "delta_price_reais": round(delta_price, 2)
            },
            "alerts": [a.to_dict() for a in alerts],
            "levers": [l.to_dict() for l in levers]
        }

    def analyze_estoque(self, estoque_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs analytical enrichment on inventory metrics."""
        d = estoque_payload["data"]
        alerts: List[AnomalyAlert] = []

        if d["skus_descontinuados"] > 100:
            alerts.append(AnomalyAlert(
                sector="estoque",
                metric="skus_descontinuados",
                current_value=float(d["skus_descontinuados"]),
                threshold_value=100.0,
                severity="CRITICO",
                headline="Volume massivo de capital imobilizado em SKUs descontinuados",
                grounded_evidence=f"{d['skus_descontinuados']} SKUs descontinuados somam R$ {d['capital_descontinuado']:,.2f} parados em porta-paletes."
            ))

        levers = [
            GroundedLever(
                rank=1,
                title="Liquidação e Desova Acelerada dos 207 SKUs Descontinuados",
                sector="estoque",
                primary_bottleneck="207 SKUs sem reposição retendo capital parado e gerando custo financeiro de carregamento.",
                grounded_metric="R$ 17.714.096,89 de capital contábil imobilizado; custo de oportunidade WACC (18% a.a.) de R$ 3.188.537,44.",
                origin_test="Teste 2.1 (Giro de Estoque e Cobertura) & Alavanca ICE #1 (Score 72.0)",
                strategic_mandate="Campanha agressiva de desova via outlet próprio e lote B2B para converter mercadoria em liquidez imediata."
            ),
            GroundedLever(
                rank=7,
                title="Racionalização do Estoque de Segurança & Redução de Rupturas",
                sector="estoque",
                primary_bottleneck="800 SKUs em ruptura simultâneos a R$ 120M em estoque defensivo excedente.",
                grounded_metric="16,0% da grade em ruptura (800 SKUs) gerando perda estimada de demanda.",
                origin_test="Teste 2.2 (Ruptura e Disponibilidade de Grade)",
                strategic_mandate="Rebalancear pontos de pedido com base na velocidade real de giro e eliminar superestocagem."
            )
        ]

        return {
            "metrics": d,
            "alerts": [a.to_dict() for a in alerts],
            "levers": [l.to_dict() for l in levers]
        }

    def analyze_atendimento(self, sac_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs analytical enrichment on customer service metrics."""
        curr = sac_payload["current"]
        prev = sac_payload.get("previous")
        tickets_wow = self.compute_wow(curr["total_tickets"], prev["total_tickets"] if prev else None)
        wismo_wow = self.compute_wow(curr.get("wismo_tickets", 0), prev.get("wismo_tickets", 0) if prev else None)

        alerts: List[AnomalyAlert] = []
        wismo_threshold = self.thresholds.get("wismo_share_alert_pct", 25.0)
        wismo_share = curr.get("wismo_share_pct", 0.0)

        if wismo_share >= wismo_threshold:
            alerts.append(AnomalyAlert(
                sector="atendimento",
                metric="wismo_share_pct",
                current_value=wismo_share,
                threshold_value=wismo_threshold,
                severity="ALERTA",
                headline="Concentração desproporcional de chamados de rastreio de carga (WISMO)",
                grounded_evidence=f"Chamados 'Onde está meu pedido?' representam {wismo_share:.1f}% do volume SAC total (teto {wismo_threshold:.1f}%)."
            ))

        levers = [
            GroundedLever(
                rank=3,
                title="Automação Inteligente de SAC e Deflexão de Rastreio de Carga",
                sector="atendimento",
                primary_bottleneck="Atendentes humanos sobrecarregados com consultas mecânicas de rastreamento de entregas.",
                grounded_metric="10.765 tickets de 'Onde está meu pedido?' (30,04% do volume); 90% defletíveis via IA; FRT de 135 min para < 1 min.",
                origin_test="Teste 3.2 (Causas-Raiz de Suporte e Custo Operacional SAC) & Alavanca ICE #3",
                strategic_mandate="Implementar bot proativo em WhatsApp conectado a webhooks de transportadoras."
            ),
            GroundedLever(
                rank=4,
                title="Protocolo de Bloqueio e Quarentena para Fornecedores Críticos",
                sector="atendimento",
                primary_bottleneck="Defeitos de fabricação geram chamados recorrentes e devoluções custosas de clientes.",
                grounded_metric="1.039 devoluções por defeito (R$ 792k estornados) concentradas em 5 fornecedores de vestuário.",
                origin_test="Teste 1.3 (Falhas Operacionais Evitáveis) & Alavanca ICE #4",
                strategic_mandate="Notificar fornecedores reincidentes, exigir ressarcimento integral e suspender ordens de compra ativas."
            )
        ]

        return {
            "metrics": curr,
            "previous_metrics": prev,
            "variations": {
                "tickets": tickets_wow,
                "wismo": wismo_wow
            },
            "alerts": [a.to_dict() for a in alerts],
            "levers": [l.to_dict() for l in levers]
        }

    def analyze_marketing(self, mkt_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs analytical enrichment on paid media and acquisition."""
        d = mkt_payload["data"]
        alerts: List[AnomalyAlert] = []

        mp = d["marketplace"]
        if mp["frete_pct"] >= self.thresholds.get("marketplace_freight_alert_pct", 4.0):
            alerts.append(AnomalyAlert(
                sector="marketing",
                metric="marketplace_frete_pct",
                current_value=mp["frete_pct"],
                threshold_value=self.thresholds.get("marketplace_freight_alert_pct", 4.0),
                severity="ALERTA",
                headline="Custo de frete abusivo no Marketplace comprimindo margem",
                grounded_evidence=f"Frete consome {mp['frete_pct']:.2f}% da receita em Marketplace (5x acima dos canais proprietários)."
            ))

        levers = [
            GroundedLever(
                rank=5,
                title="Otimização de Portfólio de Canais e Realocação de Verba",
                sector="marketing",
                primary_bottleneck="Descompasso severo de eficiência: Marketplace e Google Ads drenam recursos de canais de alto retorno.",
                grounded_metric="Influenciador atinge ROAS 7.75x e CAC ponderado R$ 1,76; Marketplace opera com ROAS 3.02x e frete de 4,55%.",
                origin_test="Teste 3.1 (CAC, ROAS e Atribuição de Mídia) & Alavanca ICE #5",
                strategic_mandate="Migrar orçamento de canais saturados para Influenciadores e TikTok Ads com trava de retornos decrescentes."
            )
        ]

        return {
            "metrics": d,
            "alerts": [a.to_dict() for a in alerts],
            "levers": [l.to_dict() for l in levers]
        }

    def analyze_clientes(self, cli_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs analytical enrichment on customer segmentation and LTV."""
        d = cli_payload["data"]
        alerts: List[AnomalyAlert] = []

        top_20_share = d["pareto_top_20_ltv_share"]
        if top_20_share >= 60.0:
            alerts.append(AnomalyAlert(
                sector="clientes",
                metric="pareto_top_20_ltv_share",
                current_value=top_20_share,
                threshold_value=60.0,
                severity="POSITIVO",
                headline="Elevada concentração de valor nos clientes mais fiéis da base",
                grounded_evidence=f"Top 20% clientes concentram {top_20_share:.2f}% do LTV total (Champions + Loyal somam 56,0% do LTV com 25,8% da base)."
            ))

        levers = [
            GroundedLever(
                rank=8,
                title="Programa de Proteção VIP para Clientes Campeões & Fiéis",
                sector="clientes",
                primary_bottleneck="Clientes de altíssimo LTV recebendo os mesmos descontos e SLAs de clientes eventuais.",
                grounded_metric="25,8% dos clientes (Champions + Loyal) concentram 56,0% do LTV total da empresa.",
                origin_test="Teste 4.1 (Segmentação RFM e Concentração de LTV)",
                strategic_mandate="Blindar base de alto valor com atendimento prioritário, acesso antecipado a coleções e corte total de cupons generalistas."
            )
        ]

        return {
            "metrics": d,
            "alerts": [a.to_dict() for a in alerts],
            "levers": [l.to_dict() for l in levers]
        }

    def analyze_consolidated(self, all_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Produces overall executive synthesis combining all 5 sectors."""
        vendas = self.analyze_vendas(all_payload["vendas"])
        estoque = self.analyze_estoque(all_payload["estoque"])
        atendimento = self.analyze_atendimento(all_payload["atendimento"])
        marketing = self.analyze_marketing(all_payload["marketing"])
        clientes = self.analyze_clientes(all_payload["clientes"])

        all_alerts = (
            vendas["alerts"] + estoque["alerts"] +
            atendimento["alerts"] + marketing["alerts"] + clientes["alerts"]
        )

        all_levers = (
            estoque["levers"] + vendas["levers"] +
            atendimento["levers"] + marketing["levers"] + clientes["levers"]
        )
        all_levers.sort(key=lambda x: x["rank"])

        return {
            "week": all_payload["week"],
            "prev_week": all_payload["prev_week"],
            "vendas": vendas,
            "estoque": estoque,
            "atendimento": atendimento,
            "marketing": marketing,
            "clientes": clientes,
            "consolidated_alerts": all_alerts,
            "consolidated_levers": all_levers,
            "dre": all_payload["dre"],
            "ice_levers": all_payload["ice_levers"]
        }
