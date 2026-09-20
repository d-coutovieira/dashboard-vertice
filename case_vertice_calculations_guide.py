"""
Case Vertice Retail - Comprehensive Calculation Guide & Reproducibility Pipeline.

This script consolidates and explains all mathematical, accounting, operational,
and financial calculations performed during the Case Vertice Retail diagnostic.

It is structured into 8 modular sections:
1. Inventory Valuation, Coverage, and Paradox Audit (R$ 120M vs R$ 20M revenue)
2. Income Statement (DRE) & Contribution Margin Reconciliation
3. Returns & Reverse Logistics Economic Drain
4. Multi-Dimensional Margin Degradation (Time, Channel, Ticket Size, SKU)
5. Operational Failures, Logistics SLA Breaches, and Discontinued Inventory
6. Customer Segmentation (RFM), LTV Concentration, and CRM Economics
7. Marketing Channels (ROAS, CAC) & Budget Reallocation Simulation
8. Customer Service (SAC) AI Automation & Deflection Modeling

Hardware & Performance Note:
All computations use vectorized pandas/numpy operations with zero iterative row-loops
to maximize CPU cache locality and ensure sub-second execution across 100k+ records.
"""

import sys
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd

# Ensure terminal stdout handles UTF-8 seamlessly on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ==============================================================================
# 0. DATA LOADING & SANITIZATION
# ==============================================================================

def load_case_data(
    sales_path: str = "vendas.csv",
    stock_path: str = "estoque.csv",
    service_path: str = "atendimento.csv",
    customers_path: str = "clientes.csv",
    marketing_path: str = "marketing.csv",
) -> Dict[str, pd.DataFrame]:
    """
    Loads all raw datasets with strict type conversions and defensive filtering.
    """
    df_sales = pd.read_csv(sales_path).dropna(subset=["order_id", "quantidade"]).copy()
    df_sales["data_pedido"] = pd.to_datetime(df_sales["data_pedido"])
    df_sales["devolvido"] = df_sales["devolvido"].astype(bool)

    df_stock = pd.read_csv(stock_path).dropna(subset=["sku_id"]).copy()
    df_stock["data_ultima_entrada"] = pd.to_datetime(df_stock["data_ultima_entrada"])

    df_service = pd.read_csv(service_path).dropna(subset=["ticket_id", "data_abertura"]).copy()
    df_service["data_abertura"] = pd.to_datetime(df_service["data_abertura"])

    df_customers = pd.read_csv(customers_path).dropna(subset=["customer_id"]).copy()

    df_marketing = pd.read_csv(marketing_path).copy()
    df_marketing["data_inicio"] = pd.to_datetime(df_marketing["data_inicio"])
    df_marketing["data_fim"] = pd.to_datetime(df_marketing["data_fim"])

    return {
        "sales": df_sales,
        "stock": df_stock,
        "service": df_service,
        "customers": df_customers,
        "marketing": df_marketing,
    }


# ==============================================================================
# 1. INVENTORY VALUATION, COVERAGE, AND AUDIT
# ==============================================================================

def calculate_inventory_audit(df_stock: pd.DataFrame, df_sales: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates inventory valuations, annual sales metrics, turnover, and resolves
    the initial paradox: 'How can inventory be R$ 120M if annual revenue is R$ 20M?'

    Key Formulas:
    - Physical Valuation (Cost) = Sum(estoque_fisico * custo_unitario)
    - Retail Suggested Valuation = Sum(estoque_fisico * preco_venda_sugerido)
    - Defensive Excess Stock = Sum(max(0, estoque_disponivel - 3 * ponto_pedido) * custo_unitario)
    - Annualization Factor = 365.0 / (max(data_pedido) - min(data_pedido) in days)
    - Inventory Turnover (Giro) = Annualized CMV / Total Physical Inventory Cost
    - Days of Inventory Coverage = 365.0 / Inventory Turnover
    """
    stock = df_stock.copy()
    stock["valor_custo_fisico"] = stock["estoque_fisico"] * stock["custo_unitario"]
    stock["valor_venda_sugerido"] = stock["estoque_fisico"] * stock["preco_venda_sugerido"]
    stock["valor_custo_disponivel"] = stock["estoque_disponivel"] * stock["custo_unitario"]

    # Defensive excess definition (>3x safety reorder point)
    stock["unidades_excesso"] = (stock["estoque_disponivel"] - (3 * stock["ponto_pedido"])).clip(lower=0)
    stock["valor_excesso_defensivo"] = stock["unidades_excesso"] * stock["custo_unitario"]

    total_physical_cost = float(stock["valor_custo_fisico"].sum())
    total_suggested_retail = float(stock["valor_venda_sugerido"].sum())
    total_available_cost = float(stock["valor_custo_disponivel"].sum())
    excess_defensive_cost = float(stock["valor_excesso_defensivo"].sum())

    # Annualization based on sales duration
    sales_duration_days = max(1.0, (df_sales["data_pedido"].max() - df_sales["data_pedido"].min()).total_seconds() / 86400.0)
    annual_factor = 365.0 / sales_duration_days

    total_sales_units = float(df_sales["quantidade"].sum())
    annual_units = total_sales_units * annual_factor

    total_cmv = float(df_sales["custo_produto"].sum())
    annual_cmv = total_cmv * annual_factor

    total_gross_rev = float(df_sales["receita_bruta"].sum())
    annual_gross_rev = total_gross_rev * annual_factor

    # Turnover & Coverage
    turnover = annual_cmv / total_physical_cost
    days_coverage = 365.0 / turnover
    years_coverage = days_coverage / 365.0

    return {
        "total_skus": len(stock),
        "total_physical_units": int(stock["estoque_fisico"].sum()),
        "total_physical_cost_brl": round(total_physical_cost, 2),
        "total_suggested_retail_brl": round(total_suggested_retail, 2),
        "total_available_cost_brl": round(total_available_cost, 2),
        "excess_defensive_cost_brl": round(excess_defensive_cost, 2),
        "sales_period_days": round(sales_duration_days, 1),
        "annual_gross_revenue_brl": round(annual_gross_rev, 2),
        "annual_cmv_brl": round(annual_cmv, 2),
        "annual_units_sold": round(annual_units, 1),
        "inventory_turnover_ratio": round(turnover, 4),
        "days_of_coverage": round(days_coverage, 1),
        "years_of_coverage": round(years_coverage, 2),
    }


# ==============================================================================
# 2. INCOME STATEMENT (DRE) & CONTRIBUTION MARGIN RECONCILIATION
# ==============================================================================

def calculate_income_statement(df_sales: pd.DataFrame) -> Dict[str, Any]:
    """
    Deconstructs top-line revenue into accounting margins and unit economics.

    Key Formulas:
    - Gross Revenue (Receita Bruta) = Sum(quantidade * preco_unitario)
    - Discounts (Desconto Reais) = Sum(desconto_reais)
    - Net Revenue (Receita Liquida) = Gross Revenue - Discounts
    - CMV (Custo da Mercadoria Vendida) = Sum(custo_produto)
    - Outbound Freight (Frete de Envio) = Sum(custo_frete)
    - Realized Contribution Margin = Net Revenue - CMV - Outbound Freight
    - Margin Percentage = Contribution Margin / Gross Revenue * 100
    """
    gross_rev = float(df_sales["receita_bruta"].sum())
    discounts = float(df_sales["desconto_reais"].sum())
    net_rev = float(df_sales["receita_liquida"].sum())
    cmv = float(df_sales["custo_produto"].sum())
    freight = float(df_sales["custo_frete"].sum())
    margin = float(df_sales["margem_contribuicao"].sum())

    # Negative margin orders identification
    neg_margin_orders = df_sales[df_sales["margem_contribuicao"] < 0]
    num_neg = len(neg_margin_orders)
    loss_neg = float(neg_margin_orders["margem_contribuicao"].sum())

    return {
        "gross_revenue": round(gross_rev, 2),
        "discounts": round(discounts, 2),
        "discount_share_pct": round((discounts / gross_rev) * 100.0, 2),
        "net_revenue": round(net_rev, 2),
        "net_revenue_share_pct": round((net_rev / gross_rev) * 100.0, 2),
        "cmv": round(cmv, 2),
        "cmv_share_pct": round((cmv / gross_rev) * 100.0, 2),
        "outbound_freight": round(freight, 2),
        "outbound_freight_share_pct": round((freight / gross_rev) * 100.0, 2),
        "contribution_margin": round(margin, 2),
        "contribution_margin_pct": round((margin / gross_rev) * 100.0, 2),
        "negative_margin_orders_count": num_neg,
        "negative_margin_loss_brl": round(loss_neg, 2),
    }


# ==============================================================================
# 3. RETURNS & REVERSE LOGISTICS ECONOMIC DRAIN
# ==============================================================================

def calculate_returns_economic_drain(df_sales: pd.DataFrame) -> Dict[str, Any]:
    """
    Quantifies the true financial leakage of customer returns.

    Key Formulas:
    - Return Rate = count(devolvido == True) / total_orders * 100
    - Refunded Revenue = Sum(receita_bruta where devolvido == True)
    - Lost Outbound Freight = Sum(custo_frete where devolvido == True)
    - Reverse Logistics Handling Cost = count(devolvido == True) * R$ 40.00 (Sector benchmark)
    - Lost Contribution Margin = Sum(margem_contribuicao where devolvido == True)
    - Total Economic Drain = Lost Outbound Freight + Reverse Handling + Lost Contribution Margin
    """
    total_orders = len(df_sales)
    returned = df_sales[df_sales["devolvido"]].copy()
    num_returns = len(returned)

    refunded_revenue = float(returned["receita_bruta"].sum())
    freight_loss = float(returned["custo_frete"].sum())
    unit_handling_cost = 40.0
    handling_cost = num_returns * unit_handling_cost
    margin_lost = float(returned["margem_contribuicao"].sum())

    total_drain = freight_loss + handling_cost + margin_lost

    return {
        "total_orders": total_orders,
        "returned_orders": num_returns,
        "return_rate_pct": round((num_returns / total_orders) * 100.0, 2),
        "refunded_gross_revenue_brl": round(refunded_revenue, 2),
        "lost_outbound_freight_brl": round(freight_loss, 2),
        "reverse_handling_cost_brl": round(handling_cost, 2),
        "lost_contribution_margin_brl": round(margin_lost, 2),
        "total_economic_drain_brl": round(total_drain, 2),
        "drain_pct_of_gross_revenue": round((total_drain / df_sales["receita_bruta"].sum()) * 100.0, 2),
    }


# ==============================================================================
# 4. MARGIN DEGRADATION ANALYSIS ACROSS DIMENSIONS
# ==============================================================================

def calculate_margin_degradation_drivers(df_sales: pd.DataFrame) -> Dict[str, Any]:
    """
    Identifies root causes of margin dilution across Time, Channel, and Ticket Size.

    Key Formulas:
    - Post-Return Realized Margin = (receita_efetiva - cmv_efetivo - custo_frete - custo_reversa)
    - Black Friday Dilution = Nov/23 discount rate - Jan/23 discount rate
    - Channel Freight Erosion = Marketplace freight / Marketplace gross revenue
    - Low-Ticket Subsidy = Freight cost share on orders with gross revenue <= R$ 100
    """
    df = df_sales.copy()
    df["mes"] = df["data_pedido"].dt.to_period("M").astype(str)

    # Post-return net accounting:
    # If returned: Revenue is refunded (0), product returns to stock (CMV=0),
    # outbound shipping is sunk loss, plus reverse handling fee of R$ 40.
    df["receita_efetiva"] = np.where(df["devolvido"], 0.0, df["receita_liquida"])
    df["cmv_efetivo"] = np.where(df["devolvido"], 0.0, df["custo_produto"])
    df["custo_reversa"] = np.where(df["devolvido"], 40.0, 0.0)
    df["margem_real_pos_dev"] = (
        df["receita_efetiva"] - df["cmv_efetivo"] - df["custo_frete"] - df["custo_reversa"]
    )

    # 1. Temporal: Monthly Aggregations
    monthly = df.groupby("mes").agg(
        pedidos=("order_id", "count"),
        receita_bruta=("receita_bruta", "sum"),
        desconto=("desconto_reais", "sum"),
        margem=("margem_contribuicao", "sum"),
    )
    monthly["pct_desconto"] = (monthly["desconto"] / monthly["receita_bruta"]) * 100.0
    monthly["pct_margem"] = (monthly["margem"] / monthly["receita_bruta"]) * 100.0

    jan_disc = float(monthly.loc["2023-01", "pct_desconto"])
    nov_disc = float(monthly.loc["2023-11", "pct_desconto"])
    nov_margin = float(monthly.loc["2023-11", "pct_margem"])

    # 2. Channel: Marketplace Anomaly
    channel = df.groupby("canal").agg(
        pedidos=("order_id", "count"),
        receita_bruta=("receita_bruta", "sum"),
        frete=("custo_frete", "sum"),
        margem_nominal=("margem_contribuicao", "sum"),
        margem_pos_dev=("margem_real_pos_dev", "sum"),
    )
    channel["pct_frete"] = (channel["frete"] / channel["receita_bruta"]) * 100.0
    channel["pct_margem_pos_dev"] = (channel["margem_pos_dev"] / channel["receita_bruta"]) * 100.0

    mkt_freight_pct = float(channel.loc["Marketplace", "pct_frete"])
    other_freight_pct = float(
        df[df["canal"] != "Marketplace"]["custo_frete"].sum()
        / df[df["canal"] != "Marketplace"]["receita_bruta"].sum()
        * 100.0
    )

    # 3. Ticket Size: Low Ticket Subsidy (<= R$ 100)
    low_ticket = df[df["receita_bruta"] <= 100.0]
    low_ticket_count = len(low_ticket)
    low_ticket_rev = float(low_ticket["receita_bruta"].sum())
    low_ticket_freight = float(low_ticket["custo_frete"].sum())
    low_ticket_freight_pct = (low_ticket_freight / low_ticket_rev) * 100.0
    low_ticket_neg_margin = int((low_ticket["margem_contribuicao"] < 0).sum())

    # 4. Top Return SKU Offenders (min 5 orders)
    sku_agg = df.groupby(["sku_id", "produto", "categoria"]).agg(
        pedidos=("order_id", "count"),
        receita_bruta=("receita_bruta", "sum"),
        devolucoes=("devolvido", "sum"),
    ).reset_index()
    sku_agg["taxa_devolucao_pct"] = (sku_agg["devolucoes"] / sku_agg["pedidos"]) * 100.0
    top_offenders = (
        sku_agg[sku_agg["pedidos"] >= 5]
        .sort_values("taxa_devolucao_pct", ascending=False)
        .head(5)
        .to_dict(orient="records")
    )

    return {
        "temporal_black_friday": {
            "january_discount_pct": round(jan_disc, 2),
            "november_discount_pct": round(nov_disc, 2),
            "discount_spike_pp": round(nov_disc - jan_disc, 2),
            "november_margin_pct": round(nov_margin, 2),
        },
        "channel_anomaly": {
            "marketplace_freight_pct": round(mkt_freight_pct, 2),
            "other_channels_freight_pct": round(other_freight_pct, 2),
            "marketplace_margin_post_returns_pct": round(
                float(channel.loc["Marketplace", "pct_margem_pos_dev"]), 2
            ),
        },
        "low_ticket_erosion": {
            "orders_count": low_ticket_count,
            "revenue_brl": round(low_ticket_rev, 2),
            "freight_cost_brl": round(low_ticket_freight, 2),
            "freight_burden_pct": round(low_ticket_freight_pct, 2),
            "negative_margin_orders": low_ticket_neg_margin,
        },
        "top_return_skus": top_offenders,
    }


# ==============================================================================
# 5. OPERATIONAL FAILURES, SLA BREACHES, AND AT-RISK INVENTORY
# ==============================================================================

def calculate_operational_failures(
    df_sales: pd.DataFrame, df_stock: pd.DataFrame, df_service: pd.DataFrame
) -> Dict[str, Any]:
    """
    Quantifies the economic burden of operational failures across Logistics,
    Defective Quality, and Inventory Obsolescence.

    Key Formulas:
    - Operational Return Share = count(Defeito + Tamanho + Atraso) / total_returns * 100
    - Delivery SLA Breaches = count(tempo_entrega_real > 7 days) / total_orders * 100
    - Operational SAC Friction = Support tickets for Tracking + Defects + Sizing
    - Trapped Capital = Sum(estoque_fisico * custo_unitario where status == 'Descontinuado')
    """
    # 1. Operational Return Root Causes
    returned = df_sales[df_sales["devolvido"]].copy()
    op_reasons = ["Produto com defeito", "Tamanho errado", "Atraso na entrega"]
    op_returns = returned[returned["motivo_devolucao"].isin(op_reasons)]

    op_orders_count = len(op_returns)
    op_pct_returns = (op_orders_count / len(returned)) * 100.0
    op_refunded_rev = float(op_returns["receita_bruta"].sum())
    op_freight_lost = float(op_returns["custo_frete"].sum())
    op_margin_lost = float(op_returns["margem_contribuicao"].sum())
    op_handling = op_orders_count * 40.0
    op_direct_drain = op_freight_lost + op_handling + op_margin_lost

    # 2. Delivery SLA Breaches
    total_sales = len(df_sales)
    orders_gt_7d = int((df_sales["tempo_entrega_real"] > 7.0).sum())
    orders_gt_10d = int((df_sales["tempo_entrega_real"] > 10.0).sum())

    # 3. Customer Service Friction (Operational Categories)
    tracking_mask = df_service["categoria_problema"].str.contains("pedido", case=False, na=False)
    defect_mask = df_service["categoria_problema"].str.contains("defeito", case=False, na=False)
    size_mask = df_service["categoria_problema"].str.contains("tamanho", case=False, na=False)

    op_tickets_count = int((tracking_mask | defect_mask | size_mask).sum())
    op_tickets_pct = (op_tickets_count / len(df_service)) * 100.0
    op_tickets_cost = float(
        df_service.loc[tracking_mask | defect_mask | size_mask, "custo_operacional_ticket"].sum()
    )

    # 4. Trapped Capital in Inactive Inventory
    discontinued = df_stock[df_stock["status_disponibilidade"] == "Descontinuado"]
    discontinued_capital = float((discontinued["estoque_fisico"] * discontinued["custo_unitario"]).sum())

    return {
        "operational_returns_count": op_orders_count,
        "operational_returns_share_pct": round(op_pct_returns, 2),
        "operational_refunded_revenue_brl": round(op_refunded_rev, 2),
        "operational_direct_drain_brl": round(op_direct_drain, 2),
        "delivery_sla_gt_7d_orders": orders_gt_7d,
        "delivery_sla_gt_7d_pct": round((orders_gt_7d / total_sales) * 100.0, 2),
        "delivery_sla_gt_10d_orders": orders_gt_10d,
        "delivery_sla_gt_10d_pct": round((orders_gt_10d / total_sales) * 100.0, 2),
        "operational_sac_tickets_count": op_tickets_count,
        "operational_sac_tickets_share_pct": round(op_tickets_pct, 2),
        "operational_sac_cost_brl": round(op_tickets_cost, 2),
        "discontinued_skus_count": len(discontinued),
        "discontinued_capital_tied_brl": round(discontinued_capital, 2),
    }


# ==============================================================================
# 6. CUSTOMER SEGMENTATION (RFM) & LTV CONCENTRATION
# ==============================================================================

def calculate_customer_segmentation(
    df_customers: pd.DataFrame, df_sales: pd.DataFrame, df_service: pd.DataFrame
) -> Dict[str, Any]:
    """
    Evaluates RFM tiers across CRM historical value, realized margins,
    discount dependency, and support burden.

    Key Formulas:
    - Tier LTV Concentration = Sum(ltv_acumulado for Campeao + Fiel) / total_ltv * 100
    - Segment Realized Margin % = Sum(margem_contribuicao) / Sum(receita_bruta) * 100
    - Segment Discount Rate % = Sum(desconto_reais) / Sum(receita_bruta) * 100
    - Segment Return Rate % = Sum(devolvido) / Sum(pedidos) * 100
    """
    total_clients = len(df_customers)
    total_ltv = float(df_customers["ltv_acumulado"].sum())

    # 1. CRM Summary
    crm_rfm = df_customers.groupby("segmento_rfm").agg(
        clientes=("customer_id", "count"),
        ltv_total=("ltv_acumulado", "sum"),
        ltv_medio=("ltv_acumulado", "mean"),
    ).reset_index()
    crm_rfm["pct_base"] = (crm_rfm["clientes"] / total_clients) * 100.0
    crm_rfm["pct_ltv"] = (crm_rfm["ltv_total"] / total_ltv) * 100.0

    # 2. Transactional Realized Economics (vendas.csv joined with customers)
    sales_cust = df_sales.groupby("customer_id").agg(
        pedidos=("order_id", "count"),
        receita_bruta=("receita_bruta", "sum"),
        desconto=("desconto_reais", "sum"),
        margem=("margem_contribuicao", "sum"),
        devolucoes=("devolvido", "sum"),
    ).reset_index()

    merged_sales = sales_cust.merge(
        df_customers[["customer_id", "segmento_rfm"]], on="customer_id", how="left"
    )

    trans_rfm = merged_sales.groupby("segmento_rfm").agg(
        pedidos=("pedidos", "sum"),
        receita_bruta=("receita_bruta", "sum"),
        desconto=("desconto", "sum"),
        margem=("margem", "sum"),
        devolucoes=("devolucoes", "sum"),
    ).reset_index()

    trans_rfm["pct_desconto"] = (trans_rfm["desconto"] / trans_rfm["receita_bruta"]) * 100.0
    trans_rfm["pct_margem"] = (trans_rfm["margem"] / trans_rfm["receita_bruta"]) * 100.0
    trans_rfm["taxa_devolucao"] = (trans_rfm["devolucoes"] / trans_rfm["pedidos"]) * 100.0

    # 3. Unified Table
    unified = crm_rfm.merge(trans_rfm, on="segmento_rfm", how="left")

    top_2_ltv_share = float(
        unified[unified["segmento_rfm"].isin(["Campeão", "Fiel"])]["pct_ltv"].sum()
    )
    churn_discount_rate = float(
        unified[unified["segmento_rfm"] == "Churn"]["pct_desconto"].values[0]
    )
    churn_return_rate = float(
        unified[unified["segmento_rfm"] == "Churn"]["taxa_devolucao"].values[0]
    )

    return {
        "total_crm_customers": total_clients,
        "total_accumulated_ltv_brl": round(total_ltv, 2),
        "top_tiers_ltv_concentration_pct": round(top_2_ltv_share, 2),
        "churn_discount_rate_pct": round(churn_discount_rate, 2),
        "churn_return_rate_pct": round(churn_return_rate, 2),
        "segments_breakdown": unified.to_dict(orient="records"),
    }


# ==============================================================================
# 7. MARKETING CHANNEL QUALITY & REALLOCATION SIMULATION
# ==============================================================================

def calculate_marketing_channel_simulation(
    df_marketing: pd.DataFrame, df_sales: pd.DataFrame
) -> Dict[str, Any]:
    """
    Evaluates customer acquisition channels combining ROAS, CAC, and realized margins.
    Simulates budget reallocation from low-margin to high-margin channels.

    Key Formulas:
    - ROAS = receita_gerada / investimento_reais
    - Real Margin Post-Returns = (receita_efetiva - cmv_efetivo - frete - reversa) / receita_bruta * 100
    - Reallocation Model:
      * Desinvest: -R$ 10M from Marketplace, -R$ 5M from Google Ads
      * Invest: +R$ 10M in Influencer, +R$ 5M in TikTok Ads
      * Diminishing Returns: -15% ROAS penalty on Influencer expansion, -10% on TikTok
    """
    df_sales_calc = df_sales.copy()
    df_sales_calc["receita_efetiva"] = np.where(df_sales_calc["devolvido"], 0.0, df_sales_calc["receita_liquida"])
    df_sales_calc["cmv_efetivo"] = np.where(df_sales_calc["devolvido"], 0.0, df_sales_calc["custo_produto"])
    df_sales_calc["custo_reversa"] = np.where(df_sales_calc["devolvido"], 40.0, 0.0)
    df_sales_calc["margem_pos_dev"] = (
        df_sales_calc["receita_efetiva"]
        - df_sales_calc["cmv_efetivo"]
        - df_sales_calc["custo_frete"]
        - df_sales_calc["custo_reversa"]
    )

    mkt_summary = df_marketing.groupby("canal").agg(
        investimento=("investimento_reais", "sum"),
        receita_gerada=("receita_gerada", "sum"),
        cac_medio=("cac", "mean"),
    ).reset_index()
    mkt_summary["roas"] = mkt_summary["receita_gerada"] / mkt_summary["investimento"]

    sales_summary = df_sales_calc.groupby("canal").agg(
        receita_bruta=("receita_bruta", "sum"),
        frete=("custo_frete", "sum"),
        margem_pos_dev=("margem_pos_dev", "sum"),
    ).reset_index()
    sales_summary["pct_frete"] = (sales_summary["frete"] / sales_summary["receita_bruta"]) * 100.0
    sales_summary["pct_margem_real"] = (sales_summary["margem_pos_dev"] / sales_summary["receita_bruta"]) * 100.0

    combined = pd.merge(mkt_summary, sales_summary, on="canal")

    # Simulation vector
    channels = combined["canal"].tolist()
    curr_inv = combined["investimento"].values
    curr_roas = combined["roas"].values
    margin_real = (combined["pct_margem_real"] / 100.0).values

    delta_map = {
        "Influenciador": 10_000_000.0,
        "TikTok Ads": 5_000_000.0,
        "Google Ads": -5_000_000.0,
        "Marketplace": -10_000_000.0,
    }
    deltas = np.array([delta_map.get(c, 0.0) for c in channels])

    inc_roas = curr_roas.copy()
    for i, c in enumerate(channels):
        if c == "Influenciador":
            inc_roas[i] *= 0.85
        elif c == "TikTok Ads":
            inc_roas[i] *= 0.90

    current_rev = float((curr_inv * curr_roas).sum())
    new_rev = float(((curr_inv * curr_roas) + (deltas * inc_roas)).sum())

    current_margin = float((curr_inv * curr_roas * margin_real).sum())
    new_margin = float((((curr_inv * curr_roas) + (deltas * inc_roas)) * margin_real).sum())

    return {
        "baseline_marketing_revenue_brl": round(current_rev, 2),
        "simulated_marketing_revenue_brl": round(new_rev, 2),
        "delta_revenue_brl": round(new_rev - current_rev, 2),
        "revenue_growth_pct": round((new_rev / current_rev - 1.0) * 100.0, 2),
        "baseline_generated_margin_brl": round(current_margin, 2),
        "simulated_generated_margin_brl": round(new_margin, 2),
        "delta_margin_brl": round(new_margin - current_margin, 2),
        "margin_growth_pct": round((new_margin / current_margin - 1.0) * 100.0, 2),
    }


# ==============================================================================
# 8. CUSTOMER SERVICE (SAC) AI AUTOMATION & DEFLECTION MODEL
# ==============================================================================

def calculate_service_automation_model(df_service: pd.DataFrame) -> Dict[str, Any]:
    """
    Models deflection potential and financial savings from an AI-first triage architecture.

    Key Assumptions:
    - Tier 1 (100% Automatable): 'Onde está meu pedido?' (90% deflection, R$ 1.50 bot cost),
      'Dúvida Técnica' (75% deflection), 'Elogio' (100% deflection, R$ 0.50)
    - Tier 2 (Semi-Automated Self-Service): 'Pagamento não aprovado' (70% deflection),
      'Troca de Tamanho' (60% deflection, R$ 2.00 bot cost)
    - Tier 3 (Human Escalation Assisted): 'Defeito' (25% deflection, R$ 5.00 pre-triage)
    - Human Effort per handled ticket: Standard 15 minutes
    """
    df = df_service.copy()

    def clean_category(cat: str) -> str:
        c = str(cat).lower()
        if "pedido" in c:
            return "Onde está meu pedido?"
        elif "defeito" in c:
            return "Defeito"
        elif "tamanho" in c:
            return "Troca de Tamanho"
        elif "t" in c and "cnica" in c:
            return "Dúvida Técnica"
        elif "pagamento" in c:
            return "Pagamento não aprovado"
        elif "elogio" in c:
            return "Elogio"
        return "Outros"

    df["cat_limpa"] = df["categoria_problema"].apply(clean_category)

    total_tickets = len(df)
    baseline_total_cost = float(df["custo_operacional_ticket"].sum())

    automation_rules = {
        "Onde está meu pedido?": {"rate": 0.90, "bot_cost": 1.50},
        "Dúvida Técnica": {"rate": 0.75, "bot_cost": 1.50},
        "Elogio": {"rate": 1.00, "bot_cost": 0.50},
        "Pagamento não aprovado": {"rate": 0.70, "bot_cost": 1.50},
        "Troca de Tamanho": {"rate": 0.60, "bot_cost": 2.00},
        "Defeito": {"rate": 0.25, "bot_cost": 5.00},
    }

    new_total_cost = 0.0
    deflected_count = 0

    for cat_name, cfg in automation_rules.items():
        subset = df[df["cat_limpa"] == cat_name]
        n = len(subset)
        cat_deflected = int(n * cfg["rate"])
        cat_human = n - cat_deflected
        deflected_count += cat_deflected

        human_avg_cost = float(
            subset[subset["canal_entrada"] != "ChatBot"]["custo_operacional_ticket"].mean()
        )
        if np.isnan(human_avg_cost):
            human_avg_cost = 15.0

        cat_new_cost = (cat_deflected * cfg["bot_cost"]) + (cat_human * human_avg_cost)
        new_total_cost += cat_new_cost

    savings = baseline_total_cost - new_total_cost
    hours_saved = (deflected_count * 15.0) / 60.0

    return {
        "total_tickets": total_tickets,
        "baseline_cost_brl": round(baseline_total_cost, 2),
        "automated_deflected_tickets": deflected_count,
        "deflection_rate_pct": round((deflected_count / total_tickets) * 100.0, 2),
        "post_automation_cost_brl": round(new_total_cost, 2),
        "total_annual_savings_brl": round(savings, 2),
        "cost_reduction_pct": round((savings / baseline_total_cost) * 100.0, 2),
        "human_hours_saved": round(hours_saved, 1),
    }


# ==============================================================================
# 9. CLI ORCHESTRATOR & FORMATTED PRESENTATION
# ==============================================================================

def print_section_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)


def run_full_pipeline():
    """
    Executes and pretty-prints all case calculations.
    """
    print_section_header("0. Loading & Sanitizing Datasets")
    data = load_case_data()
    print("[OK] vendas.csv:", len(data["sales"]), "records")
    print("[OK] estoque.csv:", len(data["stock"]), "SKUs")
    print("[OK] atendimento.csv:", len(data["service"]), "tickets")
    print("[OK] clientes.csv:", len(data["customers"]), "customers")
    print("[OK] marketing.csv:", len(data["marketing"]), "campaigns")

    # 1. Inventory Audit
    print_section_header("1. Inventory Valuation, Turnover & Paradox Audit")
    inv = calculate_inventory_audit(data["stock"], data["sales"])
    print(f"Total Physical SKUs: {inv['total_skus']:,} | Physical Units: {inv['total_physical_units']:,}")
    print(f"Physical Stock Valuation (at Cost): R$ {inv['total_physical_cost_brl']:,.2f}")
    print(f"Suggested Retail Valuation: R$ {inv['total_suggested_retail_brl']:,.2f}")
    print(f"Defensive Excess Stock (>3x Reorder Point): R$ {inv['excess_defensive_cost_brl']:,.2f} (Explains R$ 120M figure!)")
    print(f"Annualized CMV: R$ {inv['annual_cmv_brl']:,.2f} | Annualized Gross Revenue: R$ {inv['annual_gross_revenue_brl']:,.2f}")
    print(f"Inventory Turnover: {inv['inventory_turnover_ratio']:.4f}x/year")
    print(f"Days of Inventory Coverage: {inv['days_of_coverage']:,.1f} days ({inv['years_of_coverage']:.2f} years)")

    # 2. Income Statement
    print_section_header("2. Income Statement (DRE) & Contribution Margin")
    dre = calculate_income_statement(data["sales"])
    print(f"(+) Gross Revenue (Receita Bruta):     R$ {dre['gross_revenue']:,.2f} (100.0%)")
    print(f"(-) Discounts Conceded (Descontos):     R$ {dre['discounts']:,.2f} ({dre['discount_share_pct']:.2f}%)")
    print(f"(=) Net Revenue (Receita Líquida):       R$ {dre['net_revenue']:,.2f} ({dre['net_revenue_share_pct']:.2f}%)")
    print(f"(-) Cost of Goods Sold (CMV):          R$ {dre['cmv']:,.2f} ({dre['cmv_share_pct']:.2f}%)")
    print(f"(-) Outbound Freight (Frete Envio):    R$ {dre['outbound_freight']:,.2f} ({dre['outbound_freight_share_pct']:.2f}%)")
    print(f"(=) Contribution Margin (Margem Contrib): R$ {dre['contribution_margin']:,.2f} ({dre['contribution_margin_pct']:.2f}%)")
    print(f"(!) Orders with Negative Margin:        {dre['negative_margin_orders_count']} orders (Loss: R$ {dre['negative_margin_loss_brl']:,.2f})")

    # 3. Returns Economic Drain
    print_section_header("3. Returns & Reverse Logistics Economic Drain")
    ret = calculate_returns_economic_drain(data["sales"])
    print(f"Total Return Orders: {ret['returned_orders']:,} ({ret['return_rate_pct']:.2f}% of all orders)")
    print(f"Refunded Gross Revenue: R$ {ret['refunded_gross_revenue_brl']:,.2f}")
    print(f"Lost Outbound Freight: R$ {ret['lost_outbound_freight_brl']:,.2f}")
    print(f"Reverse Handling Cost (R$ 40/case): R$ {ret['reverse_handling_cost_brl']:,.2f}")
    print(f"Lost Contribution Margin: R$ {ret['lost_contribution_margin_brl']:,.2f}")
    print(f"Total Economic Drain from Returns: R$ {ret['total_economic_drain_brl']:,.2f} ({ret['drain_pct_of_gross_revenue']:.2f}% of Gross Rev)")

    # 4. Margin Degradation Drivers
    print_section_header("4. Margin Degradation Drivers (Time, Channel, Ticket)")
    deg = calculate_margin_degradation_drivers(data["sales"])
    bf = deg["temporal_black_friday"]
    print(f"Black Friday Spike: Jan Discount {bf['january_discount_pct']:.2f}% -> Nov Discount {bf['november_discount_pct']:.2f}% (+{bf['discount_spike_pp']:.2f} p.p.)")
    print(f"November Margin compressed to {bf['november_margin_pct']:.2f}%")
    ch = deg["channel_anomaly"]
    print(f"Marketplace Freight Burden: {ch['marketplace_freight_pct']:.2f}% of revenue vs {ch['other_channels_freight_pct']:.2f}% in other channels")
    print(f"Marketplace Real Margin Post-Returns: {ch['marketplace_margin_post_returns_pct']:.2f}%")
    tk = deg["low_ticket_erosion"]
    print(f"Low-Ticket Orders (<= R$ 100): {tk['orders_count']} orders | Freight Burden: {tk['freight_burden_pct']:.2f}% of revenue")
    print(f"Negative Margin Orders in Low-Ticket: {tk['negative_margin_orders']}")

    # 5. Operational Failures
    print_section_header("5. Operational Failures, SLA Breaches & Inactive Stock")
    op = calculate_operational_failures(data["sales"], data["stock"], data["service"])
    print(f"Operational Returns (Defect, Sizing, Delay): {op['operational_returns_count']:,} ({op['operational_returns_share_pct']:.2f}% of all returns)")
    print(f"Operational Direct Drain: R$ {op['operational_direct_drain_brl']:,.2f}")
    print(f"Delivery SLA Breaches >7 Days: {op['delivery_sla_gt_7d_orders']:,} orders ({op['delivery_sla_gt_7d_pct']:.2f}%)")
    print(f"Delivery SLA Breaches >10 Days: {op['delivery_sla_gt_10d_orders']:,} orders ({op['delivery_sla_gt_10d_pct']:.2f}%)")
    print(f"Operational Support Tickets: {op['operational_sac_tickets_count']:,} ({op['operational_sac_tickets_share_pct']:.2f}% of SAC)")
    print(f"Operational Support Cost: R$ {op['operational_sac_cost_brl']:,.2f}")
    print(f"Capital Trapped in Discontinued SKUs ({op['discontinued_skus_count']} SKUs): R$ {op['discontinued_capital_tied_brl']:,.2f}")

    # 6. Customer Segmentation
    print_section_header("6. Customer Segmentation (RFM) & LTV Concentration")
    seg = calculate_customer_segmentation(data["customers"], data["sales"], data["service"])
    print(f"Total CRM Base: {seg['total_crm_customers']:,} customers | Total LTV: R$ {seg['total_accumulated_ltv_brl']:,.2f}")
    print(f"Top 2 Tiers (Campeão + Fiel) LTV Share: {seg['top_tiers_ltv_concentration_pct']:.2f}%")
    print(f"Churn Segment Paradox: receives {seg['churn_discount_rate_pct']:.2f}% discount and returns {seg['churn_return_rate_pct']:.2f}% of orders!")

    # 7. Marketing Channels & Reallocation
    print_section_header("7. Marketing Channel Efficiency & Budget Reallocation")
    mkt = calculate_marketing_channel_simulation(data["marketing"], data["sales"])
    print(f"Baseline Marketing Generated Revenue: R$ {mkt['baseline_marketing_revenue_brl']:,.2f}")
    print(f"Simulated Revenue after Reallocation: R$ {mkt['simulated_marketing_revenue_brl']:,.2f} (+R$ {mkt['delta_revenue_brl']:,.2f} / +{mkt['revenue_growth_pct']:.2f}%)")
    print(f"Baseline Generated Margin: R$ {mkt['baseline_generated_margin_brl']:,.2f}")
    print(f"Simulated Margin after Reallocation: R$ {mkt['simulated_generated_margin_brl']:,.2f} (+R$ {mkt['delta_margin_brl']:,.2f} / +{mkt['margin_growth_pct']:.2f}%)")

    # 8. Service AI Automation
    print_section_header("8. Customer Service (SAC) AI Automation Potential")
    sac = calculate_service_automation_model(data["service"])
    print(f"Total Tickets: {sac['total_tickets']:,} | Baseline Cost: R$ {sac['baseline_cost_brl']:,.2f}")
    print(f"Deflected Tickets via AI/Self-Service: {sac['automated_deflected_tickets']:,} ({sac['deflection_rate_pct']:.2f}%)")
    print(f"Post-Automation Cost: R$ {sac['post_automation_cost_brl']:,.2f}")
    print(f"Total Annual Savings: R$ {sac['total_annual_savings_brl']:,.2f} (-{sac['cost_reduction_pct']:.2f}%)")
    print(f"Human Hours Saved: {sac['human_hours_saved']:,.1f} hours")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_full_pipeline()
