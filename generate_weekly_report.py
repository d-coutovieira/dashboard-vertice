"""
generate_weekly_report.py - CLI Orchestrator for Module D (Executive Report Generator).

Orchestrates the 4-layer architecture:
1. Data Ingestion (ReportDataLoader)
2. Analytical Engine (WeeklyAnalyzer)
3. Grounded Narrative Synthesis (NarrativeEngine)
4. Multi-format Presentation Rendering (ReportRenderer)

Generates publication-grade reports for all 5 business sectors plus cross-sector C-Level memo:
- Vendas & Receita
- Estoque & Suprimentos
- Atendimento & SAC
- Marketing & Aquisição
- Clientes & Retenção (RFM)
- Consolidado Geral C-Level

Usage:
  python generate_weekly_report.py --week 2023-W47 --sector all
  python generate_weekly_report.py --week latest --sector vendas --format html
  python generate_weekly_report.py --week consolidated --sector all
"""

import os
import sys
import argparse
from typing import Dict, Any, List

# Ensure safe UTF-8 terminal encoding on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from report_data_loader import ReportDataLoader
from weekly_analyzer import WeeklyAnalyzer
from narrative_engine import NarrativeEngine
from report_renderer import ReportRenderer


def generate_single_report(
    sector: str,
    resolved_week: str,
    loader: ReportDataLoader,
    analyzer: WeeklyAnalyzer,
    engine: NarrativeEngine,
    renderer: ReportRenderer,
    output_dir: str,
    formats: List[str],
    llm_enrich: bool = False
) -> Dict[str, str]:
    """
    Generates and saves report artifacts for a specific sector.
    Returns dict mapping format -> absolute file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    cfg = loader.config

    if sector == "all":
        raw_payload = loader.get_sector_payload("all", resolved_week)
        analytical = analyzer.analyze_consolidated(raw_payload)
        narrative = engine.synthesize_consolidated_memo(analytical)
        base_filename = "relatorio_geral_executivo"
    else:
        raw_payload = loader.get_sector_payload(sector, resolved_week)
        if sector == "vendas":
            analytical = analyzer.analyze_vendas(raw_payload)
            narrative = engine.synthesize_vendas_narrative(analytical)
        elif sector == "estoque":
            analytical = analyzer.analyze_estoque(raw_payload)
            narrative = engine.synthesize_estoque_narrative(analytical)
        elif sector == "atendimento":
            analytical = analyzer.analyze_atendimento(raw_payload)
            narrative = engine.synthesize_atendimento_narrative(analytical)
        elif sector == "marketing":
            analytical = analyzer.analyze_marketing(raw_payload)
            narrative = engine.synthesize_marketing_narrative(analytical)
        elif sector == "clientes":
            analytical = analyzer.analyze_clientes(raw_payload)
            narrative = engine.synthesize_clientes_narrative(analytical)
        else:
            raise ValueError(f"Unknown sector '{sector}'")
        base_filename = f"relatorio_{sector}"

    # Optional LLM prose enrichment
    if llm_enrich:
        try:
            from llm_narrative_enricher import LLMNarrativeEnricher
            enricher = LLMNarrativeEnricher()
            narrative = enricher.enrich_narrative(sector, narrative, analytical)
        except Exception as e:
            print(f"  [LLM Layer] Fallback to deterministic expert engine: {e}")

    generated_files = {}

    if "html" in formats:
        html_content = renderer.render_html(sector, analytical, narrative, cfg)
        html_path = os.path.join(output_dir, f"{base_filename}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        generated_files["html"] = html_path

    if "md" in formats:
        md_content = renderer.render_markdown(sector, analytical, narrative, cfg)
        md_path = os.path.join(output_dir, f"{base_filename}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        generated_files["md"] = md_path

    if "json" in formats:
        json_content = renderer.render_json(sector, analytical, narrative)
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        generated_files["json"] = json_path

    return generated_files


def run_cli():
    parser = argparse.ArgumentParser(
        description="Vértice Retail Executive Report Generator (Module D)"
    )
    parser.add_argument(
        "--week",
        type=str,
        default="2023-W47",
        help="ISO week (e.g., '2023-W45', '2023-W47', '2023-W51'), 'latest', or 'consolidated'."
    )
    parser.add_argument(
        "--sector",
        type=str,
        default="all",
        choices=["all", "vendas", "estoque", "atendimento", "marketing", "clientes", "full_suite"],
        help="Target sector or 'all' for consolidated memo, 'full_suite' for all 6 reports."
    )
    parser.add_argument(
        "--format",
        type=str,
        default="all",
        choices=["html", "md", "json", "all"],
        help="Output file format (default: all)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory (default: reports/{week}/)."
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM narrative refinement layer (fallback to grounded engine if offline)."
    )

    args = parser.parse_args()

    loader = ReportDataLoader()
    analyzer = WeeklyAnalyzer(loader.config)
    engine = NarrativeEngine()
    renderer = ReportRenderer()

    resolved_week = loader.resolve_week(args.week)
    output_dir = args.output_dir or os.path.join("reports", resolved_week)

    formats = ["html", "md", "json"] if args.format == "all" else [args.format]

    print("=" * 70)
    print(f" VÉRTICE RETAIL · GERADOR DE RELATÓRIOS EXECUTIVOS (MÓDULO D)")
    print(f" Ciclo / Janela: {resolved_week} | Diretório: {output_dir}")
    print("=" * 70)

    # Determine sectors to run
    if args.sector == "all":
        sectors_to_run = ["all", "vendas", "estoque", "atendimento", "marketing", "clientes"]
    elif args.sector == "full_suite":
        sectors_to_run = ["all", "vendas", "estoque", "atendimento", "marketing", "clientes"]
    else:
        sectors_to_run = [args.sector]

    total_artifacts = 0
    for sec in sectors_to_run:
        label = "Consolidado Geral C-Level" if sec == "all" else loader.config["sectors"][sec]["name"]
        print(f"\n[+] Gerando relatório: {label}...")
        files = generate_single_report(
            sector=sec,
            resolved_week=resolved_week,
            loader=loader,
            analyzer=analyzer,
            engine=engine,
            renderer=renderer,
            output_dir=output_dir,
            formats=formats,
            llm_enrich=args.llm
        )
        for fmt, path in files.items():
            size_kb = os.path.getsize(path) / 1024.0
            print(f"    |-> [{fmt.upper()}] {path} ({size_kb:.1f} KB)")
            total_artifacts += 1

    print("\n" + "=" * 70)
    print(f" Concluído com sucesso! {total_artifacts} artefatos gerados em {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    run_cli()
