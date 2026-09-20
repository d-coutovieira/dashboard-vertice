"""
test_diagnostic_consistency.py - Strict consistency tests against Diagnóstico_Final.
Validates that dashboard_data.json, build_dashboard_data.py, and generated reports
match 100% with the audited ground truth in Diagnóstico_Final/resumo_diagnostico_3.md.
"""

import os
import json
import pytest


@pytest.fixture(scope="module")
def data():
    json_path = os.path.join("dashboard", "data", "dashboard_data.json")
    assert os.path.exists(json_path), f"JSON not found at {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_dre_ground_truth(data):
    dre = data["dre"]["summary"]
    assert dre["gross_revenue"] == pytest.approx(20526133.84, rel=1e-4)
    assert dre["total_orders"] == 27758
    assert dre["discounts_total"] == pytest.approx(1636799.83, rel=1e-4)
    assert dre["discounts_pct"] == pytest.approx(7.97, abs=0.05)
    assert dre["contribution_margin"] == pytest.approx(10270436.65, rel=1e-4)
    assert dre["contribution_margin_pct"] == pytest.approx(50.04, abs=0.05)
    assert dre["post_friction_margin"] == pytest.approx(9874979.50, rel=1e-4)
    assert dre["post_friction_margin_pct"] == pytest.approx(48.12, abs=0.05)


def test_no_arbitrary_client_concentration(data):
    # Rule: Replace hallucinated "5 clientes corporativos concentram 74%" with Pareto / RFM grounded metrics
    diagnosis = data["dre"]["waterfall_items"][0]["diagnosis"]
    assert "5 clientes corporativos" not in diagnosis, "Hallucinated '5 clientes corporativos' found in waterfall diagnosis"
    assert "61,05%" in diagnosis or "56,0%" in diagnosis, "Grounded RFM/Pareto concentration metric must be present"


def test_inventory_ground_truth(data):
    inv = data["inventory"]
    assert inv["total_skus"] == 5000
    assert inv["discontinued_skus"] == 207
    assert inv["discontinued_capital"] == pytest.approx(17714096.89, rel=1e-4)
    assert inv["discontinued_wacc_saving_18pct"] == pytest.approx(3188537.44, rel=1e-4)
    assert inv["excess_defensive_cost"] == pytest.approx(120045834.67, rel=1e-4)
    assert inv["excess_stock_wacc_cost"] == pytest.approx(21608250.24, rel=1e-4)


def test_marketing_channels_cac_and_roas(data):
    channels = {c["canal"]: c for c in data["channels"]}
    
    # Influenciador: Highest ROAS and lowest weighted CAC
    inf = channels["Influenciador"]
    assert inf["roas"] == pytest.approx(7.75, abs=0.05)
    assert inf["cac_weighted"] == pytest.approx(1.76, abs=0.02)
    assert inf["cac_medio"] == pytest.approx(4.17, abs=0.05)
    assert inf["ticket_medio_liquido"] == pytest.approx(912.40, rel=1e-2)
    assert inf["ticket_medio"] == pytest.approx(994.66, rel=1e-2)

    # TikTok: Low weighted CAC and strong ROAS
    ttk = channels["TikTok Ads"]
    assert ttk["roas"] == pytest.approx(4.67, abs=0.05)
    assert ttk["cac_weighted"] == pytest.approx(1.75, abs=0.02)
    assert ttk["cac_medio"] == pytest.approx(3.95, abs=0.05)

    # Marketplace: High freight and lower ROAS
    mp = channels["Marketplace"]
    assert mp["roas"] == pytest.approx(3.02, abs=0.05)
    assert mp["frete_pct"] == pytest.approx(4.55, abs=0.1)


def test_customer_service_ground_truth(data):
    cs = data["customer_service"]
    assert cs["total_tickets"] == 35840
    
    # Find "Onde está meu pedido?" category (WISMO)
    cats = {c["categoria_normalizada"]: c for c in cs["categories"]}
    assert "Onde está meu pedido?" in cats
    wismo = cats["Onde está meu pedido?"]
    assert wismo["tickets"] == 10765
    assert wismo["share_pct"] == pytest.approx(30.04, abs=0.1)
    assert wismo["potencial_ia_pct"] == 90.0


def test_rfm_concentration_ground_truth(data):
    rfm = data["customers_rfm"]
    assert rfm["total_customers"] == 15000
    
    # Pareto top 20%
    assert rfm["pareto"]["top_20_ltv_share_pct"] == pytest.approx(61.05, abs=0.1)
    
    # Champions + Loyal Customers concentration
    champ = [s for s in rfm["segments"] if "camp" in s["segmento_rfm"].lower()][0]
    loyal = [s for s in rfm["segments"] if "fiel" in s["segmento_rfm"].lower()][0]
    
    combined_base = champ["pct_base"] + loyal["pct_base"]
    combined_ltv = champ["pct_ltv"] + loyal["pct_ltv"]
    
    assert combined_base == pytest.approx(25.86, abs=0.5)
    assert combined_ltv == pytest.approx(56.04, abs=0.5)
