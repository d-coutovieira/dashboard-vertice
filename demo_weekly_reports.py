"""
demo_weekly_reports.py - Executive Panel Demonstration Runner (Pitch Script).

Simulates 3 key historical weeks plus the consolidated audit period,
generating full multi-sector report suites and an executive navigation hub (demo_hub.html).

Key Demonstration Windows:
1. 2023-W45: Baseline operational week (pre-Black Friday).
2. 2023-W47: Black Friday peak week (discount anomaly detection).
3. 2023-W51: Christmas / Year-end holiday season.
4. consolidated: Full 13-month strategic audit memo.
"""

import os
import sys
import time
from typing import List, Dict, Any

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
from generate_weekly_report import generate_single_report


DEMO_WEEKS = [
    ("2023-W45", "Semana Operacional Pré-Black Friday (Baseline Regular)"),
    ("2023-W47", "Pico da Black Friday 2023 (Alerta Crítico de Desconto)"),
    ("2023-W51", "Sazonalidade de Natal / Fim de Ano"),
    ("consolidated", "Consolidado Estratégico 13 Meses (Auditoria Geral DRE)")
]

SECTORS = [
    ("all", "Consolidado Geral C-Level", "relatorio_geral_executivo.html", "#6366f1"),
    ("vendas", "Vendas & Receita", "relatorio_vendas.html", "#38bdf8"),
    ("estoque", "Estoque & Suprimentos", "relatorio_estoque.html", "#facc15"),
    ("atendimento", "Atendimento & SAC", "relatorio_atendimento.html", "#a78bfa"),
    ("marketing", "Marketing & Aquisição", "relatorio_marketing.html", "#fb923c"),
    ("clientes", "Clientes & Retenção (RFM)", "relatorio_clientes.html", "#34d399"),
]


def generate_demo_hub_html(reports_catalog: Dict[str, List[Dict[str, str]]], output_path: str = "reports/demo_hub.html"):
    """
    Creates a master navigation hub for the evaluation panel.
    """
    html_cards = []
    for week_code, week_desc in DEMO_WEEKS:
        sector_links = []
        for sec_id, sec_name, filename, color in SECTORS:
            file_rel = f"{week_code}/{filename}"
            sector_links.append(f"""
            <a href="{file_rel}" target="_blank" class="report-link" style="border-left-color:{color};">
              <span class="link-sector" style="color:{color};">● {sec_name}</span>
              <span class="link-action">Visualizar HTML ➔</span>
            </a>
            """)

        html_cards.append(f"""
        <div class="week-card">
          <div class="week-header">
            <span class="week-badge">{week_code}</span>
            <h3 class="week-title">{week_desc}</h3>
          </div>
          <div class="links-grid">
            {"".join(sector_links)}
          </div>
        </div>
        """)

    hub_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hub de Demonstração Executiva · Módulo D · Vértice Retail</title>
  <link rel="stylesheet" href="../static/report.css">
  <style>
    .hub-container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
    .hub-header {{ text-align: center; margin-bottom: 48px; }}
    .hub-badge {{ display: inline-block; padding: 6px 16px; border-radius: 999px; background: rgba(99, 102, 241, 0.15); color: #a5b4fc; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; }}
    .hub-title {{ font-size: 2.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.03em; margin-bottom: 12px; }}
    .hub-desc {{ color: #94a3b8; font-size: 1.05rem; max-width: 800px; margin: 0 auto; }}
    .week-card {{ background: rgba(17, 24, 39, 0.9); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 28px; margin-bottom: 28px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }}
    .week-header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }}
    .week-badge {{ background: #1e293b; color: #38bdf8; font-family: 'JetBrains Mono', monospace; font-weight: 700; padding: 4px 12px; border-radius: 6px; font-size: 0.9rem; }}
    .week-title {{ font-size: 1.25rem; font-weight: 700; color: #f1f5f9; }}
    .links-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .report-link {{ display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); border-left-width: 4px; padding: 14px 18px; border-radius: 8px; text-decoration: none; color: #e2e8f0; transition: all 0.2s ease; }}
    .report-link:hover {{ background: rgba(30, 41, 59, 0.8); transform: translateX(3px); }}
    .link-sector {{ font-size: 0.92rem; font-weight: 600; }}
    .link-action {{ font-size: 0.8rem; color: #94a3b8; font-weight: 500; }}
  </style>
</head>
<body style="background:#0a0e1a; color:#f3f4f6; font-family:'Inter', sans-serif;">
  <div class="hub-container">
    <div class="hub-header">
      <span class="hub-badge">EloGroup Transformation, Strategy & Analytics</span>
      <h1 class="hub-title">Hub Executivo de Demonstração (Módulo D)</h1>
      <p class="hub-desc">
        Catálogo navegável dos relatórios gerados automaticamente pelo Motor Analítico Grounded.
        Selecione qualquer semana ou setor para inspecionar os memorandos executivos completos.
      </p>
    </div>

    {"".join(html_cards)}

    <div style="text-align:center; padding-top:24px; color:#64748b; font-size:0.85rem;">
      Vértice Retail · Case EloGroup · Todos os números auditados e conciliados com a DRE Oficial.
    </div>
  </div>
</body>
</html>
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(hub_html)


def run_demo():
    print("=" * 75)
    print(" INICIANDO DEMONSTRAÇÃO EXECUTIVA · BANCA AVALIADORA (MÓDULO D)")
    print("=" * 75)

    loader = ReportDataLoader()
    analyzer = WeeklyAnalyzer(loader.config)
    engine = NarrativeEngine()
    renderer = ReportRenderer()

    reports_catalog = {}
    total_files = 0
    t0 = time.time()

    for week_code, week_desc in DEMO_WEEKS:
        print(f"\n[>>>] Processando Janela: {week_code} ({week_desc})")
        out_dir = os.path.join("reports", week_code)
        reports_catalog[week_code] = []

        for sec_id, sec_name, _, _ in SECTORS:
            files = generate_single_report(
                sector=sec_id,
                resolved_week=week_code,
                loader=loader,
                analyzer=analyzer,
                engine=engine,
                renderer=renderer,
                output_dir=out_dir,
                formats=["html", "md", "json"]
            )
            total_files += len(files)
            reports_catalog[week_code].append(files)

        print(f"      |-> 6 relatórios completos gerados em {out_dir}")

    # Generate Hub
    hub_path = os.path.join("reports", "demo_hub.html")
    generate_demo_hub_html(reports_catalog, hub_path)
    print(f"\n[+] Hub de navegação executiva criado em: {hub_path}")

    elapsed = time.time() - t0
    print("\n" + "=" * 75)
    print(f" DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO EM {elapsed:.2f}s!")
    print(f" Total de {total_files} artefatos gerados nas 4 janelas temporais.")
    print(f" Abra no navegador: {os.path.abspath(hub_path)}")
    print("=" * 75)


if __name__ == "__main__":
    run_demo()
