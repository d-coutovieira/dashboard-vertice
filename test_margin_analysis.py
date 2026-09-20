"""
Unit tests for margin degradation analysis logic.
"""

import pytest
import pandas as pd
from margin_analysis import analyze_margin_by_dimension


@pytest.fixture(scope="module")
def sales_data():
    return pd.read_csv("vendas.csv")


def test_margin_analysis_structure_and_values(sales_data):
    res = analyze_margin_by_dimension(sales_data)

    # 1. Total consistency
    assert 20_000_000 < res["total_gross_revenue"] < 21_000_000
    assert 10_000_000 < res["total_contribution_margin"] < 11_000_000

    # 2. Period (Black Friday discount spike)
    assert res["period"]["nov_discount_pct"] > 9.0
    assert res["period"]["jan_discount_pct"] < 8.0
    assert res["period"]["discount_jump_pp"] > 2.0

    # 3. Channel (Marketplace freight penalty)
    assert res["channel"]["marketplace_freight_pct"] > 4.0
    assert res["channel"]["other_channels_freight_pct"] < 1.5

    # 4. Low ticket freight subsidy
    assert res["ticket_size"]["low_ticket_freight_pct"] > 40.0
    assert res["ticket_size"]["low_ticket_negative_margin_orders"] > 250

    # 5. Returns economic drain
    assert res["returns"]["returned_orders_count"] == 4127
    assert res["returns"]["total_economic_drain"] > 1_500_000
