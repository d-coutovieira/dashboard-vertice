import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sales_data():
    return pd.read_csv("Carlos_08_09/dados_tratados/vendas.csv")

def test_negative_margin_orders_totals(sales_data):
    neg = sales_data[sales_data["margem_contribuicao"] < 0]
    assert len(neg) == 491
    assert round(neg["margem_contribuicao"].sum(), 2) == -6636.11
    assert neg["desconto_reais"].sum() < 20000.0  # Not 180k!

def test_excess_discount_above_15_pct(sales_data):
    df = sales_data.copy()
    df["desconto_pct"] = df["desconto_reais"] / df["receita_bruta"]
    subset = df[df["desconto_pct"] > 0.15]
    
    assert len(subset) == 7101
    excess = (subset["desconto_reais"] - (subset["receita_bruta"] * 0.15)).sum()
    assert round(excess, 2) == 653320.64

def test_break_even_and_target_churn_thresholds(sales_data):
    df = sales_data.copy()
    df["desconto_pct"] = df["desconto_reais"] / df["receita_bruta"]
    subset = df[df["desconto_pct"] > 0.15].copy()
    
    orig_rl = subset["receita_liquida"].sum()
    orig_mc = subset["margem_contribuicao"].sum()
    
    subset["desc_15"] = subset["receita_bruta"] * 0.15
    subset["rl_15"] = subset["receita_bruta"] - subset["desc_15"]
    subset["mc_15"] = subset["rl_15"] - subset["custo_produto"] - subset["custo_frete"]
    
    total_rl_15 = subset["rl_15"].sum()
    total_mc_15 = subset["mc_15"].sum()
    
    # Revenue break-even threshold (Delta RL = 0)
    churn_revenue = 1 - (orig_rl / total_rl_15)
    assert 0.14 < churn_revenue < 0.15  # exactly ~14.77%
    
    # Margin break-even threshold (Delta MC = 0)
    churn_margin = 1 - (orig_mc / total_mc_15)
    assert 0.29 < churn_margin < 0.30  # exactly ~29.42%
    
    # At 12.31% churn, margin gain is R$ 380,000.00
    ret_target = 1 - 0.1231
    gain_mc = (total_mc_15 * ret_target) - orig_mc
    assert abs(gain_mc - 380000.0) < 1000.0  # within R$ 1k of 380k
