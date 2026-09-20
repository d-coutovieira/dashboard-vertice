"""
test_weekly_generator.py - Comprehensive Unit & Integration Tests for Module D layers.
Tests Loader (Layer 1), Analyzer (Layer 2), Narrative (Layer 3), and Renderer (Layer 4).
"""

import os
import json
import pytest

from report_data_loader import ReportDataLoader
from weekly_analyzer import WeeklyAnalyzer
from narrative_engine import NarrativeEngine
from report_renderer import ReportRenderer
from generate_weekly_report import generate_single_report


@pytest.fixture(scope="module")
def loader():
    return ReportDataLoader()


@pytest.fixture(scope="module")
def analyzer(loader):
    return WeeklyAnalyzer(loader.config)


@pytest.fixture(scope="module")
def engine():
    return NarrativeEngine()


@pytest.fixture(scope="module")
def renderer():
    return ReportRenderer()


# -------------------------------------------------------------
# Layer 1: ReportDataLoader Tests
# -------------------------------------------------------------
def test_loader_available_weeks(loader):
    weeks = loader.get_available_weeks()
    assert len(weeks) >= 50
    assert "2023-W47" in weeks
    assert "2024-W04" in weeks


def test_loader_resolve_week(loader):
    assert loader.resolve_week("latest") == loader.get_available_weeks()[-1]
    assert loader.resolve_week("consolidated") == "consolidated"
    assert loader.resolve_week("2023-W47") == "2023-W47"
    with pytest.raises(ValueError):
        loader.resolve_week("invalid_week_string")


def test_loader_vendas_payload_consolidated(loader):
    v = loader.get_sector_payload("vendas", "consolidated")
    assert v["current"]["receita_bruta"] == pytest.approx(20526133.84, rel=1e-4)
    assert v["current"]["pedidos"] == 27758
    assert v["current"]["margem_contribuicao_pct"] == pytest.approx(50.04, abs=0.05)


def test_loader_vendas_payload_black_friday(loader):
    v = loader.get_sector_payload("vendas", "2023-W47")
    assert v["current"]["receita_bruta"] == pytest.approx(889225.25, rel=1e-2)
    assert v["current"]["pedidos"] == 1219
    assert v["prev_week"] == "2023-W46"
    assert v["previous"] is not None


# -------------------------------------------------------------
# Layer 2: WeeklyAnalyzer Tests
# -------------------------------------------------------------
def test_analyzer_wow_and_variance_decomposition(loader, analyzer):
    v = loader.get_sector_payload("vendas", "2023-W47")
    res = analyzer.analyze_vendas(v)
    assert res["variations"]["receita"]["has_previous"] is True
    assert res["variations"]["receita"]["direction"] in ("up", "down")
    assert "delta_volume_reais" in res["variance_decomposition"]
    assert "delta_price_reais" in res["variance_decomposition"]


def test_analyzer_black_friday_discount_anomaly(loader, analyzer):
    v = loader.get_sector_payload("vendas", "2023-W47")
    res = analyzer.analyze_vendas(v)
    alerts = res["alerts"]
    assert len(alerts) > 0
    # BF discount was > 9.0%, so it should trigger CRITICO alert
    severities = [a["severity"] for a in alerts]
    assert "CRITICO" in severities or "ALERTA" in severities


def test_analyzer_grounded_levers_structure(loader, analyzer):
    v = loader.get_sector_payload("vendas", "consolidated")
    res = analyzer.analyze_vendas(v)
    assert len(res["levers"]) >= 1
    for lever in res["levers"]:
        assert "rank" in lever
        assert "title" in lever
        assert "primary_bottleneck" in lever
        assert "grounded_metric" in lever
        assert "origin_test" in lever


# -------------------------------------------------------------
# Layer 3: NarrativeEngine Tests
# -------------------------------------------------------------
def test_narrative_engine_grounded_facts(loader, analyzer, engine):
    v = loader.get_sector_payload("vendas", "2023-W47")
    a = analyzer.analyze_vendas(v)
    n = engine.synthesize_vendas_narrative(a)
    assert "headline" in n and len(n["headline"]) > 10
    assert "executive_summary" in n and len(n["executive_summary"]) > 50
    assert len(n["facts"]) >= 3
    for fact in n["facts"]:
        assert "label" in fact
        assert "formatted_value" in fact
        assert "source_origin" in fact
        assert "None" not in fact["formatted_value"]


# -------------------------------------------------------------
# Layer 4: ReportRenderer Tests (All 6 Reports)
# -------------------------------------------------------------
@pytest.mark.parametrize("sector", ["all", "vendas", "estoque", "atendimento", "marketing", "clientes"])
def test_renderer_all_six_reports_html(loader, analyzer, engine, renderer, sector):
    cfg = loader.config
    if sector == "all":
        raw = loader.get_sector_payload("all", "2023-W47")
        ana = analyzer.analyze_consolidated(raw)
        nar = engine.synthesize_consolidated_memo(ana)
    else:
        raw = loader.get_sector_payload(sector, "2023-W47")
        if sector == "vendas":
            ana = analyzer.analyze_vendas(raw)
            nar = engine.synthesize_vendas_narrative(ana)
        elif sector == "estoque":
            ana = analyzer.analyze_estoque(raw)
            nar = engine.synthesize_estoque_narrative(ana)
        elif sector == "atendimento":
            ana = analyzer.analyze_atendimento(raw)
            nar = engine.synthesize_atendimento_narrative(ana)
        elif sector == "marketing":
            ana = analyzer.analyze_marketing(raw)
            nar = engine.synthesize_marketing_narrative(ana)
        elif sector == "clientes":
            ana = analyzer.analyze_clientes(raw)
            nar = engine.synthesize_clientes_narrative(ana)

    html = renderer.render_html(sector, ana, nar, cfg)
    assert len(html) > 5000, f"HTML for sector '{sector}' is too short ({len(html)} chars)"
    assert "EloGroup" in html
    assert "Vértice Retail" in html
    assert "Nota Metodológica de Escopo" in html or "Business Case" in html
    assert ">NaN<" not in html and ">nan<" not in html
    assert "undefined" not in html.lower()


def test_cli_generator_e2e(tmp_path, loader, analyzer, engine, renderer):
    out_dir = str(tmp_path / "test_reports")
    res = generate_single_report(
        sector="vendas",
        resolved_week="2023-W47",
        loader=loader,
        analyzer=analyzer,
        engine=engine,
        renderer=renderer,
        output_dir=out_dir,
        formats=["html", "md", "json"]
    )
    assert "html" in res and os.path.exists(res["html"])
    assert "md" in res and os.path.exists(res["md"])
    assert "json" in res and os.path.exists(res["json"])
