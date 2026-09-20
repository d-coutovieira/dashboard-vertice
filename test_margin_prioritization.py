"""
test_margin_prioritization.py - Regression & Integrity tests confirming the removal of
Centro de Decisão Estratégica (Priorização de Margem, Alavancas ICE, Simuladores de Cenários)
while preserving the Stock Liquidation Simulator in Estoque & Capital.
"""

import os
import pytest


@pytest.fixture
def dashboard_html_content():
    path = os.path.join(os.path.dirname(__file__), "dashboard", "index.html")
    assert os.path.exists(path), f"File not found: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_removed_modules_are_absent_from_html(dashboard_html_content):
    """Asserts that the 3 removed views and the decision center section are completely gone."""
    # 1. Views
    assert 'id="view-priorizacao-margem"' not in dashboard_html_content
    assert 'id="view-alavancas-ice"' not in dashboard_html_content
    assert 'id="view-simuladores"' not in dashboard_html_content

    # 2. Navigation items
    assert 'data-view="priorizacao-margem"' not in dashboard_html_content
    assert 'data-view="alavancas-ice"' not in dashboard_html_content
    assert 'data-view="simuladores"' not in dashboard_html_content
    assert "Centro de Decisão Estratégica" not in dashboard_html_content

    # 3. Script tags
    assert "margin-prioritization.js" not in dashboard_html_content


def test_margin_prioritization_js_file_deleted():
    """Asserts that the physical file margin-prioritization.js has been deleted."""
    js_path = os.path.join(os.path.dirname(__file__), "dashboard", "js", "margin-prioritization.js")
    assert not os.path.exists(js_path), "dashboard/js/margin-prioritization.js must be deleted"


def test_stock_simulator_is_preserved(dashboard_html_content):
    """Asserts that the Stock Liquidation Simulator in Estoque & Capital is intact."""
    assert 'id="view-estoque-supply"' in dashboard_html_content
    assert 'id="sim-container-stock"' in dashboard_html_content
    assert 'id="slider-liq-disc"' in dashboard_html_content
    assert 'id="slider-liq-time"' in dashboard_html_content
    assert 'id="sim-stock-cash"' in dashboard_html_content
    assert 'id="sim-stock-interest"' in dashboard_html_content
