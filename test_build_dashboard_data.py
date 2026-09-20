"""
test_build_dashboard_data.py - Unit tests for dashboard data pipeline.
Validates exact DRE numbers, ICE prioritization levers, AI productivity KPIs,
and simulator parameters.
"""

import json
import os
import pytest
from build_dashboard_data import (
    load_datasets,
    compute_executive_dre,
    compute_channel_breakdown,
    compute_customer_rfm,
    compute_sac_diagnostics,
    compute_inventory_breakdown,
    get_ice_levers,
    get_traceability_metadata,
    get_simulator_presets,
)


@pytest.fixture(scope="module")
def datasets():
    return load_datasets()


@pytest.fixture(scope="module")
def json_payload():
    path = os.path.join("dashboard", "data", "dashboard_data.json")
    assert os.path.exists(path), f"JSON file {path} must exist."
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_dataset_record_counts(datasets):
    assert len(datasets["sales"]) == 27758
    assert len(datasets["stock"]) == 5000
    assert len(datasets["service"]) == 35840
    assert len(datasets["customers"]) == 15000
    assert len(datasets["marketing"]) == 3500


def test_executive_dre_exact_values(datasets, json_payload):
    dre = json_payload["dre"]
    summary = dre["summary"]

    # Reconciled figures from diagnostico_executivo_vertice.html
    assert summary["gross_revenue"] == 20526133.84
    assert summary["net_revenue"] == 18889334.01
    assert summary["contribution_margin"] == 10270436.65
    assert summary["contribution_margin_pct"] == 50.04
    assert summary["post_friction_margin"] == 9874979.50
    assert summary["post_friction_margin_pct"] == 48.12
    assert summary["discounts_pct"] == 7.97

    # Check that waterfall items contain all core accounting rows
    item_ids = [item["id"] for item in dre["waterfall_items"]]
    assert "gross_revenue" in item_ids
    assert "discounts" in item_ids
    assert "net_revenue" in item_ids
    assert "cmv" in item_ids
    assert "outbound_freight" in item_ids
    assert "contribution_margin" in item_ids
    assert "operating_margin_post_friction" in item_ids
    assert "inventory_opportunity_cost" in item_ids


def test_ice_levers_ranking(json_payload):
    levers = json_payload["ice_levers"]
    assert len(levers) == 5

    # Lever #1 must be Discontinued Inventory Liquidation
    assert levers[0]["rank"] == 1
    assert levers[0]["ice_score"] == 72.0
    assert "Descontinuados" in levers[0]["title"]

    # Lever #2 must be Minimum Freight Floor
    assert levers[1]["rank"] == 2
    assert levers[1]["ice_score"] == 60.0
    assert "Piso de Frete" in levers[1]["title"]

    # Lever #3 must be WhatsApp AI Tracking Agent
    assert levers[2]["rank"] == 3
    assert levers[2]["ice_score"] == 50.4
    assert "Rastreio" in levers[2]["title"]

    # Lever #4 must be Supplier Quarantine
    assert levers[3]["rank"] == 4
    assert levers[3]["ice_score"] == 38.4

    # Lever #5 must be Media Reallocation
    assert levers[4]["rank"] == 5
    assert levers[4]["ice_score"] == 37.8


def test_ai_productivity_kpis(json_payload):
    sac = json_payload["customer_service"]
    assert "ai_productivity_kpis" in sac
    kpis = sac["ai_productivity_kpis"]
    assert len(kpis) >= 4

    names = [k["kpi"] for k in kpis]
    assert any("Deflexão" in n for n in names)
    assert any("CPTC" in n or "Contato" in n for n in names)
    assert any("FRT" in n or "Resposta" in n for n in names)
    assert any("Horas" in n for n in names)

    # Check that each KPI has formula and premise
    for k in kpis:
        assert "formula" in k and len(k["formula"]) > 5
        assert "premise" in k and len(k["premise"]) > 5


def test_simulators_configuration(json_payload):
    sims = json_payload["simulators"]
    assert "marketing_reallocation" in sims
    assert "pricing_discount" in sims
    assert "inventory_liquidation" in sims

    mkt_params = sims["marketing_reallocation"]["parameters"]
    assert len(mkt_params) == 4
    param_ids = [p["id"] for p in mkt_params]
    assert "delta_influencer" in param_ids
    assert "delta_marketplace" in param_ids


def test_traceability_coverage(json_payload):
    trace = json_payload["traceability"]
    required_keys = [
        "gross_revenue",
        "discounts",
        "contribution_margin",
        "reverse_logistics_drain",
        "post_friction_margin",
        "excess_stock",
        "roas_channel",
    ]
    for key in required_keys:
        assert key in trace
        item = trace[key]
        assert "formula" in item
        assert "datasets" in item
        assert "premises" in item


def test_new_stock_indicators(json_payload):
    inv = json_payload["inventory"]

    # 1. Discontinued detail
    assert "discontinued_detail" in inv
    assert len(inv["discontinued_detail"]) > 0
    top_disc = inv["discontinued_detail"][0]
    assert "sku_id" in top_disc
    assert "custo_total" in top_disc
    assert top_disc["custo_total"] > 0

    # 2. Critical shelf life (10-20 days window)
    assert "shelf_life_actionable_window" in inv
    shelf = inv["shelf_life_actionable_window"]
    assert shelf["total_skus_in_window"] > 0
    assert "traceability_formula" in shelf
    assert len(shelf["items"]) > 0
    for item in shelf["items"]:
        assert 10 <= item["dias_ate_vencer"] <= 20
        assert "acao_sugerida" in item
        assert item["quantidade"] > 0

    # 3. Rupture risk
    assert "rupture_risk" in inv
    rupture = inv["rupture_risk"]
    assert rupture["total_skus_at_risk"] > 0
    assert len(rupture["items"]) > 0
    for item in rupture["items"]:
        assert item["cobertura_dias"] < item["lead_time_reposicao"]
        assert "criticidade" in item

