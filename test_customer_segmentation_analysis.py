"""
Unit tests for customer segmentation and RFM value analysis module.
"""

import pytest
from customer_segmentation_analysis import analyze_customer_segments


@pytest.fixture(scope="module")
def segmentation_results():
    return analyze_customer_segments()


def test_segmentation_overview_and_counts(segmentation_results):
    summary = segmentation_results["summary"]
    assert summary["total_customers"] == 15000
    assert 135_000_000 < summary["total_ltv_brl"] < 142_000_000

    # Top segments (Campeão + Fiel) must represent over 50% of total LTV
    assert summary["top_value_segments_ltv_share_pct"] > 50.0

    # Churn customers receive higher discount and return more
    assert summary["churn_discount_rate_pct"] > 10.0
    assert summary["churn_return_rate_pct"] >= 18.0


def test_segment_detail_structure(segmentation_results):
    segments = {s["segmento_rfm"]: s for s in segmentation_results["segments_detail"]}
    expected_segments = {"Campeão", "Fiel", "Promissor", "Em Risco", "Hibernando", "Churn"}
    assert set(segments.keys()) == expected_segments

    # Campeão must have highest average LTV
    assert segments["Campeão"]["ltv_medio"] > 25000.0

    # Promissor must generate the most SAC tickets
    assert segments["Promissor"]["tickets"] > 15000
