"""
report_renderer.py - Multi-format Presentation Layer (Layer 4) for Module D.

Renders analytical payloads into publication-grade HTML (using Jinja2 + executive CSS),
plain Markdown, and machine-readable JSON formats.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape


def fmt_brl(val: Optional[float]) -> str:
    if val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return "0,00%"
    return f"{val:.2f}%".replace(".", ",")


def fmt_int(val: Optional[int]) -> str:
    if val is None:
        return "0"
    return f"{val:,}".replace(",", ".")


def fmt_millions(val: Optional[float], prefix: str = "R$ ") -> str:
    if val is None:
        return f"{prefix}0,00M"
    return f"{prefix}{val / 1_000_000.0:.2f}M".replace(".", ",")


class ReportRenderer:
    """
    Orchestrates Jinja2 rendering for HTML, and handles Markdown and JSON outputs.
    """

    def __init__(self, templates_dir: str = "templates", static_dir: str = "static"):
        if not os.path.exists(templates_dir):
            alt_path = os.path.join(os.path.dirname(__file__), "templates")
            if os.path.exists(alt_path):
                templates_dir = alt_path
        self.templates_dir = templates_dir
        self.static_dir = static_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"])
        )

    def _get_embedded_css(self) -> str:
        css_path = os.path.join(self.static_dir, "report.css")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                return f"<style>\n{f.read()}\n</style>"
        return ""

    def _format_dict_values(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Creates copy of dictionary and injects formatted strings with _fmt suffix."""
        res = dict(d)
        for k, v in d.items():
            if isinstance(v, (int, float)):
                # Specific monetary exceptions that contain 'pct' in the name
                if k in ("economia_wacc_18pct", "excesso_wacc_cost"):
                    res[f"{k}_fmt"] = fmt_brl(float(v))
                elif "pct" in k or "taxa" in k or "share" in k:
                    res[f"{k}_fmt"] = fmt_pct(float(v))
                elif "pedidos" in k or "tickets" in k or "skus" in k or "unidades" in k or "clientes" in k:
                    res[f"{k}_fmt"] = fmt_int(int(v))
                elif "roas" in k:
                    res[f"{k}_fmt"] = f"{float(v):.2f}x"
                else:
                    res[f"{k}_fmt"] = fmt_brl(float(v))
            elif isinstance(v, dict):
                res[k] = self._format_dict_values(v)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                res[k] = [self._format_dict_values(item) for item in v]
        return res

    def render_html(
        self,
        sector: str,
        analytical_payload: Dict[str, Any],
        narrative_payload: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Renders standalone, self-contained publication HTML."""
        generated_at = time.strftime("%d/%m/%Y às %H:%M:%S")
        template_name = "memo_all.html" if sector == "all" else f"sector_{sector}.html"
        template = self.env.get_template(template_name)

        if sector == "all":
            dre_fmt = self._format_dict_values(narrative_payload["dre"])
            context = {
                "page_title": f"Memorando Executivo C-Level ({analytical_payload['week']}) · Vértice Retail",
                "week_label": analytical_payload["week"],
                "generated_at": generated_at,
                "sector_name": "Consolidado Executivo C-Level",
                "sector_color": "#6366f1",
                "report_headline": narrative_payload["headline"],
                "report_subtitle": "Diagnóstico Integrado dos 5 Setores, Matriz de Alavancas e Análise de DRE",
                "executive_synthesis": narrative_payload["executive_synthesis"],
                "dre": dre_fmt,
                "vendas": narrative_payload["vendas"],
                "estoque": narrative_payload["estoque"],
                "atendimento": narrative_payload["atendimento"],
                "marketing": narrative_payload["marketing"],
                "clientes": narrative_payload["clientes"],
                "consolidated_alerts": narrative_payload["consolidated_alerts"],
                "consolidated_levers": narrative_payload["consolidated_levers"]
            }
        else:
            sec_cfg = config["sectors"][sector]
            curr_fmt = self._format_dict_values(analytical_payload.get("metrics", {}))
            context = {
                "page_title": f"{sec_cfg['name']} ({analytical_payload.get('week', 'Consolidado')}) · Vértice Retail",
                "week_label": analytical_payload.get("week", "Consolidado"),
                "generated_at": generated_at,
                "sector_name": sec_cfg["name"],
                "sector_color": sec_cfg["color"],
                "report_headline": narrative_payload["headline"],
                "report_subtitle": sec_cfg["title"],
                "executive_summary": narrative_payload["executive_summary"],
                "current": curr_fmt,
                "variations": analytical_payload.get("variations", {}),
                "facts": narrative_payload.get("facts", []),
                "alerts": narrative_payload.get("alerts", []),
                "levers": narrative_payload.get("levers", []),
                "channels": [self._format_dict_values(c) for c in curr_fmt.get("channels", [])] if sector == "marketing" else [],
                "segments": [self._format_dict_values(s) for s in curr_fmt.get("segments", [])] if sector == "clientes" else [],
            }

        rendered = template.render(**context)

        # Inject CSS inline so the file is 100% portable
        embedded_css = self._get_embedded_css()
        if embedded_css:
            rendered = rendered.replace(
                '<link rel="stylesheet" href="../../static/report.css">',
                embedded_css
            )

        return rendered

    def render_markdown(
        self,
        sector: str,
        analytical_payload: Dict[str, Any],
        narrative_payload: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Renders standard GitHub-flavored Markdown."""
        week = analytical_payload.get("week", "Consolidado")
        generated_at = time.strftime("%d/%m/%Y às %H:%M:%S")

        md = []
        md.append(f"# {narrative_payload['headline']}\n")
        md.append(f"**Cliente:** Vértice Retail | **Consultoria:** EloGroup Strategic Intelligence")
        md.append(f"**Janela / Semana:** {week} | **Gerado em:** {generated_at}\n")
        md.append("---\n")

        if sector == "all":
            md.append("## 1. Síntese Transversal Executiva\n")
            md.append(narrative_payload["executive_synthesis"] + "\n")

            if narrative_payload.get("consolidated_alerts"):
                md.append("## 2. Alertas Críticos Identificados\n")
                for a in narrative_payload["consolidated_alerts"]:
                    md.append(f"- **[{a['severity']}] {a['sector'].upper()}:** {a['headline']} ({a['grounded_evidence']})")
                md.append("")

            md.append("## 3. Alavancas Prioritárias Identificadas pelo Diagnóstico\n")
            md.append("| Rank | Setor | Alavanca | Gargalo Causal | Métrica de Grounding |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for l in narrative_payload["consolidated_levers"]:
                md.append(f"| #{l['rank']} | {l['sector']} | {l['title']} | {l['primary_bottleneck']} | {l['grounded_metric']} |")
            md.append("\n> **Nota de Escopo:** O Plano de Ação executivo detalhado (com cronogramas, metas por sprint e modelagem financeira completa) constitui entrega separada no Business Case.\n")

        else:
            md.append("## 1. Síntese Analítica Executiva\n")
            md.append(narrative_payload["executive_summary"] + "\n")

            if narrative_payload.get("alerts"):
                md.append("## 2. Alertas de Operação\n")
                for a in narrative_payload["alerts"]:
                    md.append(f"- **[{a['severity']}]** {a['headline']}: {a['grounded_evidence']}")
                md.append("")

            if narrative_payload.get("facts"):
                md.append("## 3. Fatos e Métricas Auditadas\n")
                md.append("| Métrica | Valor | Fonte | Impacto |")
                md.append("| :--- | :--- | :--- | :--- |")
                for f in narrative_payload["facts"]:
                    md.append(f"| {f['label']} | {f['formatted_value']} | {f['source_origin']} | {f['impact_assessment']} |")
                md.append("")

            if narrative_payload.get("levers"):
                md.append("## 4. Alavancas Identificadas pelo Diagnóstico\n")
                md.append("| Prioridade | Alavanca | Gargalo Causal | Métrica de Grounding |")
                md.append("| :--- | :--- | :--- | :--- |")
                for l in narrative_payload["levers"]:
                    md.append(f"| #{l['rank']} | {l['title']} | {l['primary_bottleneck']} | {l['grounded_metric']} |")
                md.append("\n> **Nota de Escopo:** O detalhamento executivo de prazos, metas graduais e modelagem de retorno incremental constitui o Business Case (documento complementar).\n")

        return "\n".join(md)

    def render_json(
        self,
        sector: str,
        analytical_payload: Dict[str, Any],
        narrative_payload: Dict[str, Any]
    ) -> str:
        """Renders complete machine-readable analytical payload."""
        output = {
            "metadata": {
                "sector": sector,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "engine": "EloGroup Analytical Synthesis Engine"
            },
            "analytics": analytical_payload,
            "narrative": narrative_payload
        }
        return json.dumps(output, ensure_ascii=False, indent=2)
