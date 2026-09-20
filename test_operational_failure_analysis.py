"""
Unit tests for operational failure analysis module.
"""

import pytest
from operational_failure_analysis import analyze_operational_failures


@pytest.fixture(scope="module")
def op_analysis():
    return analyze_operational_failures()


def test_operational_returns_metrics(op_analysis):
    op = op_analysis["operational_returns"]
    # 3 operational reasons: defect (1039), size (1025), delay (808) = 2872
    assert op["operational_orders_count"] == 2872
    assert 68.0 < op["pct_of_all_returns"] < 71.0
    assert 2_000_000 < op["refunded_revenue_brl"] < 2_200_000
    assert 1_100_000 < op["direct_economic_drain_brl"] < 1_300_000


def test_delivery_sla_breaches(op_analysis):
    sla = op_analysis["delivery_sla"]
    assert sla["total_orders"] == 27758
    assert sla["pct_gt_7d"] > 55.0
    assert sla["pct_gt_10d"] > 30.0


def test_customer_service_operational_friction(op_analysis):
    sac = op_analysis["customer_service_friction"]
    assert sac["pct_of_all_tickets"] > 60.0
    assert 300_000 < sac["total_sac_operational_cost_brl"] < 360_000


def test_discontinued_inventory_capital(op_analysis):
    inv = op_analysis["inventory_risk"]
    assert inv["stockout_skus_count"] == 99
    assert inv["discontinued_skus_count"] == 207
    assert 17_000_000 < inv["discontinued_capital_tied_brl"] < 18_500_000
