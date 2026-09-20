"""
Unit tests for customer service root-cause and automation analysis module.
"""

import pytest
from customer_service_analysis import analyze_customer_service_automation


@pytest.fixture(scope="module")
def cs_analysis():
    return analyze_customer_service_automation()


def test_customer_service_overview(cs_analysis):
    ov = cs_analysis["overview"]
    assert ov["total_tickets"] == 35840
    assert 530_000 < ov["total_cost_brl"] < 535_000
    assert 3.0 < ov["mean_csat"] < 3.5
    assert ov["mean_frt_minutes"] > 100.0


def test_category_breakdown_consistency(cs_analysis):
    cats = {c["categoria_limpa"]: c for c in cs_analysis["category_breakdown"]}
    assert "Onde está meu pedido?" in cats
    assert "Defeito" in cats
    assert "Troca de Tamanho" in cats
    assert cats["Onde está meu pedido?"]["tickets"] == 10765
    assert cats["Defeito"]["tickets"] == 6509


def test_automation_savings_simulation(cs_analysis):
    auto = cs_analysis["automation_modeling"]
    # Total deflected tickets should be between 22k and 26k (out of 35.8k)
    assert 22_000 < auto["total_deflected_tickets"] < 26_000
    assert auto["total_deflection_rate_pct"] > 60.0
    # Hours saved should be over 5,500 hours
    assert auto["total_hours_saved"] > 5500.0
    # Financial savings should be over 55% of baseline cost
    assert auto["total_savings_pct"] > 55.0
    assert auto["total_savings_brl"] > 280_000.0
