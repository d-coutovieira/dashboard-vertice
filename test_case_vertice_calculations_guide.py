"""
Unit tests for Case Vertice Calculations Guide script.
Validates inventory calculations, DRE reconciliation, returns economics,
operational failures, customer segmentation, marketing simulation, and SAC automation.
"""

import pytest
import pandas as pd
import numpy as np
from case_vertice_calculations_guide import (
    load_case_data,
    calculate_inventory_audit,
    calculate_income_statement,
    calculate_returns_economic_drain,
    calculate_margin_degradation_drivers,
    calculate_operational_failures,
    calculate_customer_segmentation,
    calculate_marketing_channel_simulation,
    calculate_service_automation_model,
)


@pytest.fixture(scope="module")
def case_data():
    return load_case_data()


def test_data_loading(case_data):
    assert len(case_data["sales"]) > 0
    assert len(case_data["stock"]) == 5000
    assert len(case_data["service"]) > 0
    assert len(case_data["customers"]) == 15000
    assert len(case_data["marketing"]) > 0


def test_inventory_audit(case_data):
    inv = calculate_inventory_audit(case_data["stock"], case_data["sales"])
    assert inv["total_skus"] == 5000
    assert inv["total_physical_cost_brl"] > 340_000_000.0
    # Validates defensive excess stock matches previous squad hypothesis of ~R$ 120M
    assert 119_000_000.0 <= inv["excess_defensive_cost_brl"] <= 121_000_000.0
    # Validates annual turnover and coverage years
    assert inv["years_of_coverage"] > 40.0


def test_income_statement(case_data):
    dre = calculate_income_statement(case_data["sales"])
    assert dre["gross_revenue"] > 20_000_000.0
    assert dre["contribution_margin"] > 10_000_000.0
    assert 49.0 <= dre["contribution_margin_pct"] <= 51.0
    assert dre["negative_margin_orders_count"] > 0


def test_returns_economic_drain(case_data):
    ret = calculate_returns_economic_drain(case_data["sales"])
    assert 14.0 <= ret["return_rate_pct"] <= 16.0
    assert ret["total_economic_drain_brl"] > 1_500_000.0
    assert ret["drain_pct_of_gross_revenue"] > 7.0


def test_margin_degradation_drivers(case_data):
    deg = calculate_margin_degradation_drivers(case_data["sales"])
    # Black Friday discount spike in November vs January
    assert deg["temporal_black_friday"]["discount_spike_pp"] > 2.0
    # Marketplace freight burden anomaly
    assert deg["channel_anomaly"]["marketplace_freight_pct"] > 4.0
    assert deg["channel_anomaly"]["other_channels_freight_pct"] < 1.5
    # Low ticket orders
    assert deg["low_ticket_erosion"]["orders_count"] > 500


def test_operational_failures(case_data):
    op = calculate_operational_failures(
        case_data["sales"], case_data["stock"], case_data["service"]
    )
    assert op["operational_returns_share_pct"] > 65.0
    assert op["delivery_sla_gt_7d_pct"] > 50.0
    assert op["discontinued_capital_tied_brl"] > 15_000_000.0


def test_customer_segmentation(case_data):
    seg = calculate_customer_segmentation(
        case_data["customers"], case_data["sales"], case_data["service"]
    )
    assert seg["total_crm_customers"] == 15000
    # Top 2 tiers concentrate over 50% of total LTV
    assert seg["top_tiers_ltv_concentration_pct"] > 50.0
    # Churn segment discount rate > 10%
    assert seg["churn_discount_rate_pct"] > 10.0


def test_marketing_simulation(case_data):
    mkt = calculate_marketing_channel_simulation(
        case_data["marketing"], case_data["sales"]
    )
    assert mkt["delta_revenue_brl"] > 0
    assert mkt["delta_margin_brl"] > 0


def test_service_automation_model(case_data):
    sac = calculate_service_automation_model(case_data["service"])
    assert sac["deflection_rate_pct"] > 65.0
    assert sac["total_annual_savings_brl"] > 250_000.0
    assert sac["human_hours_saved"] > 5000.0
