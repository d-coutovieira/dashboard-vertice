"""
dashboard_server.py - Zero-Dependency Application Server for Executive Dashboard & AI Reports.

Serves static frontend files from 'dashboard/' directory and exposes REST APIs:
- GET  /api/health: Health check, provider availability, and engine status.
- GET  /api/available-weeks: Dynamic list of dataset ISO weeks + special windows.
- POST /api/weekly-report: Grounded 4-layer Executive Weekly Report Generator (Module D).
- POST /api/generate-report: Legacy executive report generator across 4 topics.
"""

import os
import sys
import json
import tempfile
import subprocess
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, Optional

from generate_ai_report import generate_executive_report, TOPICS
from report_data_loader import ReportDataLoader
from weekly_analyzer import WeeklyAnalyzer
from narrative_engine import NarrativeEngine
from report_renderer import ReportRenderer


PORT = 8088
DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard")

# Cached singletons for high-performance in-memory report generation (<25ms)
_LOADER: Optional[ReportDataLoader] = None
_ANALYZER: Optional[WeeklyAnalyzer] = None
_ENGINE: Optional[NarrativeEngine] = None
_RENDERER: Optional[ReportRenderer] = None


def get_reporting_engine():
    """Initializes and returns cached instances of the 4-layer engine."""
    global _LOADER, _ANALYZER, _ENGINE, _RENDERER
    if _LOADER is None:
        _LOADER = ReportDataLoader()
        _ANALYZER = WeeklyAnalyzer(_LOADER.config)
        _ENGINE = NarrativeEngine()
        _RENDERER = ReportRenderer()
    return _LOADER, _ANALYZER, _ENGINE, _RENDERER


def generate_weekly_report_payload(sector: str, week: str, llm_enrich: bool = False, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the 4-layer reporting engine:
    Loader -> Analyzer -> Narrative Engine -> Renderer
    """
    loader, analyzer, engine, renderer = get_reporting_engine()
    cfg = loader.config
    resolved_week = loader.resolve_week(week)

    if sector == "all":
        raw_payload = loader.get_sector_payload("all", resolved_week)
        analytical = analyzer.analyze_consolidated(raw_payload)
        narrative = engine.synthesize_consolidated_memo(analytical)
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

    if llm_enrich:
        try:
            from llm_narrative_enricher import LLMNarrativeEnricher
            enricher = LLMNarrativeEnricher(api_key=api_key)
            narrative = enricher.enrich_narrative(sector, narrative, analytical)
        except Exception:
            pass

    html_content = renderer.render_html(sector, analytical, narrative, cfg)
    markdown_content = renderer.render_markdown(sector, analytical, narrative, cfg)

    return {
        "success": True,
        "sector": sector,
        "week": week,
        "resolved_week": resolved_week,
        "headline": narrative.get("headline", ""),
        "executive_summary": narrative.get("executive_summary") or narrative.get("executive_synthesis", ""),
        "html": html_content,
        "markdown": markdown_content
    }


def get_available_weeks_payload() -> Dict[str, Any]:
    """Builds formatted list of available weeks for the dashboard selector."""
    loader, _, _, _ = get_reporting_engine()
    iso_weeks = loader.get_available_weeks()

    special_items = [
        {"value": "2023-W47", "label": "Semana 47 / 2023 (Black Friday · Destaque)", "badge": "Pico BF"},
        {"value": "consolidated", "label": "Período Consolidado (13 meses auditados)", "badge": "Visão Geral"},
        {"value": "latest", "label": "Última Semana Registrada (2024-W04)", "badge": "Recente"},
        {"value": "2023-W51", "label": "Semana 51 / 2023 (Pico de Natal)", "badge": "Fim de Ano"},
        {"value": "2023-W45", "label": "Semana 45 / 2023 (Pré-Black Friday)", "badge": "Normalidade"}
    ]

    seen = {item["value"] for item in special_items}
    chronological_items = []
    for w in reversed(iso_weeks):
        if w not in seen:
            chronological_items.append({
                "value": w,
                "label": f"Semana {w}",
                "badge": ""
            })

    return {
        "success": True,
        "default_week": "2023-W47",
        "weeks": special_items + chronological_items
    }


def find_browser_executable() -> Optional[str]:
    """Finds installed Google Chrome or Microsoft Edge executable on Windows."""
    browsers = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    return next((b for b in browsers if os.path.exists(b)), None)


def convert_html_to_pdf(html_content: str) -> bytes:
    """Renders HTML string to PDF bytes via local headless Chromium without browser headers/footers."""
    browser_exe = find_browser_executable()
    if not browser_exe:
        raise RuntimeError("Nenhum navegador compatível (Chrome/Edge) encontrado no sistema para geração de PDF.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tf_html:
        tf_html.write(html_content)
        html_path = tf_html.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf_pdf:
        pdf_path = tf_pdf.name

    try:
        cmd = [
            browser_exe,
            "--headless=new",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path,
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=20)
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            raise RuntimeError(f"Falha ao gerar PDF headless: {res.stderr.decode('utf-8', errors='ignore')}")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return pdf_bytes
    finally:
        for p in (html_path, pdf_path):
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving dashboard files and handling REST APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self._set_headers(200)

    def do_GET(self):
        """Handle health check, week listing, or static file serving."""
        if self.path == "/api/health":
            self._set_headers(200)
            payload = {
                "status": "online",
                "engine_status": "ready",
                "topics_available": TOPICS,
                "sectors_available": ["all", "vendas", "estoque", "atendimento", "marketing", "clientes"],
                "server": "EloGroup Executive Analytics Server"
            }
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            return

        if self.path == "/api/available-weeks":
            try:
                payload = get_available_weeks_payload()
                self._set_headers(200)
                self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if self.path.startswith("/api/export-pdf"):
            try:
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                sector = params.get("sector", ["all"])[0]
                week = params.get("week", ["2023-W47"])[0]
                llm = params.get("llm", ["false"])[0].lower() in ("true", "1")

                payload = generate_weekly_report_payload(sector, week, llm_enrich=llm)
                html_content = payload.get("html", "")
                pdf_bytes = convert_html_to_pdf(html_content)

                filename = f"Relatorio_Executivo_Vertice_{sector}_{week}.pdf"
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(pdf_bytes)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(pdf_bytes)
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        """Handle report generation APIs."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        req_data = json.loads(post_body) if post_body else {}

        # 1. Direct Headless PDF Export
        if self.path == "/api/export-pdf":
            try:
                sector = req_data.get("sector", "all")
                week = req_data.get("week", "2023-W47")
                llm = bool(req_data.get("llm", False))
                api_key = req_data.get("api_key")

                payload = generate_weekly_report_payload(sector, week, llm_enrich=llm, api_key=api_key)
                html_content = payload.get("html", "")
                pdf_bytes = convert_html_to_pdf(html_content)

                filename = f"Relatorio_Executivo_Vertice_{sector}_{week}.pdf"
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(pdf_bytes)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(pdf_bytes)
            except Exception as e:
                self._set_headers(500)
                err_response = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(err_response, ensure_ascii=False).encode("utf-8"))
            return

        # 2. Module D 4-layer engine endpoint
        if self.path == "/api/weekly-report":
            try:
                sector = req_data.get("sector", "all")
                week = req_data.get("week", "2023-W47")
                llm = bool(req_data.get("llm", False))
                api_key = req_data.get("api_key")

                response = generate_weekly_report_payload(sector, week, llm_enrich=llm, api_key=api_key)
                self._set_headers(200)
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                err_response = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(err_response, ensure_ascii=False).encode("utf-8"))
            return

        # 2. Legacy generator endpoint (fallback compatibility)
        if self.path == "/api/generate-report":
            try:
                topic = req_data.get("topic", "visao_geral_dre")
                api_key = req_data.get("api_key")
                sim_params = req_data.get("sim_params")

                report = generate_executive_report(
                    topic=topic,
                    api_key=api_key,
                    sim_params=sim_params
                )

                self._set_headers(200)
                response = {
                    "success": True,
                    "report": report
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                err_response = {
                    "success": False,
                    "error": str(e)
                }
                self.wfile.write(json.dumps(err_response, ensure_ascii=False).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


class ThreadingServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


def run_server(port=PORT):
    server_address = ("", port)
    try:
        httpd = ThreadingServer(server_address, DashboardRequestHandler)
    except OSError as e:
        if getattr(e, "winerror", None) == 10048 or "Address already in use" in str(e):
            print("=" * 65)
            print(f"  [AVISO] A porta {port} já está em uso por outro processo!")
            print(f"  O dashboard já está ativo em: http://localhost:{port}/")
            print("=" * 65)
            sys.exit(0)
        raise e

    print("=" * 65)
    print("  EloGroup Executive Dashboard & AI Report Server")
    print(f"  URL: http://localhost:{port}/")
    print(f"  API Semanal (Módulo D): http://localhost:{port}/api/weekly-report")
    print(f"  API Semanas: http://localhost:{port}/api/available-weeks")
    print(f"  Diretório Estático: {DASHBOARD_DIR}")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor finalizado com sucesso.")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port_arg)

