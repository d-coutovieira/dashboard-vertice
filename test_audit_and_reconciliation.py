"""
Test suite for Vertice Retail audit and reconciliation logic.
Validates data integrity, accounting identities, and inventory calculations.
"""

import pytest
import pandas as pd
import numpy as np

from audit_and_reconciliation import (
    load_and_sanitize_data,
    investigate_inventory_anomaly,
    compute_profitability_tree,
    analyze_customer_service_friction,
)


@pytest.fixture(scope="module")
def sanitized_data():
    return load_and_sanitize_data()


def test_sales_accounting_identities(sanitized_data):
    """
    Validates that gross revenue, discounts, net revenue, CMV, freight,
    and contribution margin satisfy exact financial accounting constraints.
    """
    df_sales = sanitized_data["sales"]

    # 1. Gross Revenue = Quantity * Unit Price
    calc_gross = df_sales["quantidade"] * df_sales["preco_unitario"]
    np.testing.assert_allclose(
        df_sales["receita_bruta"].values,
        calc_gross.values,
        rtol=1e-5,
        atol=1e-2,
        err_msg="Gross revenue must equal quantity times unit price",
    )

    # 2. Net Revenue = Gross Revenue - Discounts
    calc_net = df_sales["receita_bruta"] - df_sales["desconto_reais"]
    np.testing.assert_allclose(
        df_sales["receita_liquida"].values,
        calc_net.values,
        rtol=1e-5,
        atol=1e-2,
        err_msg="Net revenue must equal gross revenue minus discount",
    )

    # 3. Contribution Margin = Net Revenue - Product Cost - Outbound Freight
    calc_margin = (
        df_sales["receita_liquida"]
        - df_sales["custo_produto"]
        - df_sales["custo_frete"]
    )
    np.testing.assert_allclose(
        df_sales["margem_contribuicao"].values,
        calc_margin.values,
        rtol=1e-5,
        atol=1e-2,
        err_msg="Contribution margin must equal net revenue minus CMV and freight",
    )


def test_stock_uniqueness_and_scale(sanitized_data):
    """
    Verifies that stock table contains unique SKUs and no artificial fan-out duplicates.
    """
    df_stock = sanitized_data["stock"]

    assert len(df_stock) == 5000, "Stock table should contain exactly 5000 SKUs"
    assert (
        df_stock["sku_id"].nunique() == 5000
    ), "All sku_ids in stock must be strictly unique"
    assert (
        df_stock["estoque_fisico"] >= df_stock["estoque_disponivel"]
    ).all(), "Physical stock must be greater than or equal to available stock"


def test_inventory_anomaly_outputs(sanitized_data):
    """
    Tests the reconciliation function outputs and confirms the R$ 120M excess origin.
    """
    df_stock = sanitized_data["stock"]
    df_sales = sanitized_data["sales"]

    res = investigate_inventory_anomaly(df_stock, df_sales)

    # Confirm total physical cost is approximately R$ 348.7M
    assert 340_000_000 < res["total_physical_cost_brl"] < 355_000_000

    # Confirm defensive excess inventory is approximately R$ 120M
    assert 115_000_000 < res["excess_defensive_cost_brl"] < 125_000_000

    # Confirm turnover is below 0.1 (extremely low) and coverage is measured in years
    assert res["inventory_turnover_annual"] < 0.05
    assert res["years_of_inventory_coverage"] > 30.0


def test_profitability_tree_metrics(sanitized_data):
    """
    Verifies margin calculation and return rate logic.
    """
    df_sales = sanitized_data["sales"]
    res = compute_profitability_tree(df_sales)

    assert 20_000_000 < res["gross_revenue"] < 21_000_000
    assert 18_000_000 < res["net_revenue"] < 19_500_000
    assert 10_000_000 < res["contribution_margin"] < 11_000_000
    assert 14.0 < res["returns_rate_pct"] < 16.0
    assert res["returns_count"] == 4127


def test_customer_service_friction_metrics(sanitized_data):
    """
    Verifies customer support metrics and friction categorization.
    """
    df_service = sanitized_data["service"]
    df_sales = sanitized_data["sales"]
    res = analyze_customer_service_friction(df_service, df_sales)

    assert res["total_tickets"] == 35840
    assert 500_000 < res["total_cost_brl"] < 550_000
    assert res["order_status_pct"] > 25.0
