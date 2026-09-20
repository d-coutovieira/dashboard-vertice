"""
Unit tests for marketing channel acquisition quality evaluation.
"""

import pytest
from marketing_channel_analysis import evaluate_acquisition_channels


@pytest.fixture(scope="module")
def channel_analysis_results():
    return evaluate_acquisition_channels()


def test_channel_evaluation_completeness(channel_analysis_results):
    channels = channel_analysis_results["channels_table"]
    assert len(channels) == 7, "Must contain all 7 channels"
    channel_names = {c["canal"] for c in channels}
    expected_channels = {
        "Email Marketing",
        "Google Ads",
        "Influenciador",
        "Instagram Ads",
        "Marketplace",
        "Orgânico",
        "TikTok Ads",
    }
    assert channel_names == expected_channels


def test_influencer_and_marketplace_extremes(channel_analysis_results):
    channels = {c["canal"]: c for c in channel_analysis_results["channels_table"]}

    # Influencer should have highest ROAS and ticket
    assert channels["Influenciador"]["roas"] > 7.0
    assert channels["Influenciador"]["ticket_medio"] > 900.0
    assert "Prioridade Máxima" in channels["Influenciador"]["classificacao"]

    # Marketplace should have lowest real margin and highest freight %
    assert channels["Marketplace"]["pct_frete"] > 4.0
    assert channels["Marketplace"]["pct_margem_real"] < 39.0
    assert "Desinvestir" in channels["Marketplace"]["classificacao"]


def test_budget_reallocation_simulation_gain(channel_analysis_results):
    sim = channel_analysis_results["simulation"]
    # Reallocation should increase revenue and margin without adding budget
    assert sim["delta_generated_revenue_brl"] > 20_000_000
    assert sim["delta_generated_margin_brl"] > 10_000_000
    assert sim["pct_margin_growth"] > 3.0
