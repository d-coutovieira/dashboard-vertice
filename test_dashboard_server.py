"""
test_dashboard_server.py - Automated Unit & Integration Tests for Dashboard Server & Module D API.
"""

import os
import json
import threading
import time
import urllib.request
import pytest

from dashboard_server import (
    generate_weekly_report_payload,
    get_available_weeks_payload,
    DashboardRequestHandler,
    run_server
)
from http.server import HTTPServer


def test_get_available_weeks_payload():
    """Validates week listing endpoint payload structure and defaults."""
    payload = get_available_weeks_payload()
    assert payload["success"] is True
    assert payload["default_week"] == "2023-W47"
    assert isinstance(payload["weeks"], list)
    assert len(payload["weeks"]) > 50

    values = [w["value"] for w in payload["weeks"]]
    assert "2023-W47" in values
    assert "consolidated" in values
    assert "latest" in values
    assert "2023-W51" in values


def test_generate_weekly_report_all_consolidated():
    """Validates C-Level consolidated memo payload generation."""
    res = generate_weekly_report_payload(sector="all", week="consolidated")
    assert res["success"] is True
    assert res["sector"] == "all"
    assert res["resolved_week"] == "consolidated"
    assert len(res["html"]) > 5000
    assert len(res["markdown"]) > 500
    assert "Consolidado Executivo" in res["html"] or "C-Level" in res["html"]
    # Verify presence of key grounded facts (50,04% margin and gross revenue)
    assert "50,04%" in res["html"]
    assert "20.526.133" in res["html"] or "20.531.054" in res["html"]


@pytest.mark.parametrize("sector", ["vendas", "estoque", "atendimento", "marketing", "clientes"])
def test_generate_weekly_report_all_sectors(sector):
    """Validates that each of the 5 business sectors renders successfully without error."""
    res = generate_weekly_report_payload(sector=sector, week="2023-W47")
    assert res["success"] is True
    assert res["sector"] == sector
    assert len(res["html"]) > 3000
    assert len(res["markdown"]) > 200


def test_estoque_grounding_consistency():
    """Validates that inventory report strictly preserves the audited 207 SKUs and WACC cost."""
    res = generate_weekly_report_payload(sector="estoque", week="2023-W47")
    assert "207" in res["html"]
    assert "17.71M" in res["html"] or "17.708.541" in res["html"]
    assert "3.19M" in res["html"] or "3.188.537" in res["html"]


def test_marketing_grounding_consistency():
    """Validates marketing channel ROAS and CAC consistency."""
    res = generate_weekly_report_payload(sector="marketing", week="2023-W47")
    assert "Influenciador" in res["html"]
    assert "1,76" in res["html"] or "1.76" in res["html"]
    assert "Marketplace" in res["html"]



from http.server import ThreadingHTTPServer


def test_http_api_end_to_end():
    """Starts an ephemeral HTTP test server and validates REST endpoints."""
    test_port = 8189
    server = ThreadingHTTPServer(("127.0.0.1", test_port), DashboardRequestHandler)
    server.daemon_threads = True
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        # 1. Test GET /api/health
        with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/health") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "online"
            assert data["engine_status"] == "ready"

        # 2. Test GET /api/available-weeks
        with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/available-weeks") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["success"] is True
            assert len(data["weeks"]) > 50

        # 3. Test POST /api/weekly-report
        req_body = json.dumps({"sector": "vendas", "week": "2023-W47"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{test_port}/api/weekly-report",
            data=req_body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["success"] is True
            assert data["sector"] == "vendas"
            assert len(data["html"]) > 1000

    finally:
        server.shutdown()
        server.server_close()
