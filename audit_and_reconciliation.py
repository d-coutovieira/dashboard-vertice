"""
Auditing and reconciliation pipeline for Vertice Retail dataset.
Investigates the inventory vs. sales anomaly, reconciles unit economics,
deconstructs the profitability tree, and identifies margin leaks.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


def load_and_sanitize_data(
    sales_path: str = "vendas.csv",
    stock_path: str = "estoque.csv",
    service_path: str = "atendimento.csv",
    customer_path: str = "clientes.csv",
    marketing_path: str = "marketing.csv",
) -> Dict[str, pd.DataFrame]:
    """
    Loads raw CSV files, trims structural nulls, and applies strict type casting.
    """
    df_sales = pd.read_csv(sales_path)
    df_stock = pd.read_csv(stock_path)
    df_service = pd.read_csv(service_path)
    df_customer = pd.read_csv(customer_path)
    df_marketing = pd.read_csv(marketing_path)

    # 1. Clean sales: drop sentinel empty rows
    df_sales = df_sales.dropna(subset=["order_id", "quantidade"]).copy()
    df_sales["data_pedido"] = pd.to_datetime(df_sales["data_pedido"])
    df_sales["devolvido"] = df_sales["devolvido"].astype(bool)

    # 2. Clean stock
    df_stock = df_stock.dropna(subset=["sku_id"]).copy()
    df_stock["data_ultima_entrada"] = pd.to_datetime(df_stock["data_ultima_entrada"])

    # 3. Clean customer service
    df_service = df_service.dropna(subset=["ticket_id", "data_abertura"]).copy()
    df_service["data_abertura"] = pd.to_datetime(df_service["data_abertura"])

    # 4. Clean customers & marketing
    df_customer = df_customer.dropna(subset=["customer_id"]).copy()
    df_marketing["data_inicio"] = pd.to_datetime(df_marketing["data_inicio"])
    df_marketing["data_fim"] = pd.to_datetime(df_marketing["data_fim"])

    return {
        "sales": df_sales,
        "stock": df_stock,
        "service": df_service,
        "customers": df_customer,
        "marketing": df_marketing,
    }


def investigate_inventory_anomaly(
    df_stock: pd.DataFrame, df_sales: pd.DataFrame
) -> Dict[str, Any]:
    """
    Investigates the R$ 120M inventory vs R$ 20M revenue hypothesis.
    Calculates exact inventory valuation at cost, retail suggested price,
    and the previous squad's defensive excess definition.
    """
    # Total valuation
    df_stock["valor_custo_fisico"] = (
        df_stock["estoque_fisico"] * df_stock["custo_unitario"]
    )
    df_stock["valor_venda_sugerido"] = (
        df_stock["estoque_fisico"] * df_stock["preco_venda_sugerido"]
    )
    df_stock["valor_custo_disponivel"] = (
        df_stock["estoque_disponivel"] * df_stock["custo_unitario"]
    )

    # Defensive excess stock (> 3x reorder point) as computed in H13
    df_stock["unidades_excesso"] = (
        df_stock["estoque_disponivel"] - (3 * df_stock["ponto_pedido"])
    ).clip(lower=0)
    df_stock["valor_excesso_defensivo"] = (
        df_stock["unidades_excesso"] * df_stock["custo_unitario"]
    )

    total_physical_units = int(df_stock["estoque_fisico"].sum())
    total_physical_cost = float(df_stock["valor_custo_fisico"].sum())
    total_suggested_retail = float(df_stock["valor_venda_sugerido"].sum())
    total_available_cost = float(df_stock["valor_custo_disponivel"].sum())
    total_excess_defensive_cost = float(df_stock["valor_excesso_defensivo"].sum())

    # Annualized sales metrics
    sales_start = df_sales["data_pedido"].min()
    sales_end = df_sales["data_pedido"].max()
    period_days = max(1.0, (sales_end - sales_start).total_seconds() / 86400.0)
    annualization_factor = 365.0 / period_days

    total_units_sold = float(df_sales["quantidade"].sum())
    annual_units_sold = total_units_sold * annualization_factor

    total_cmv = float(df_sales["custo_produto"].sum())
    annual_cmv = total_cmv * annualization_factor

    gross_revenue = float(df_sales["receita_bruta"].sum())
    annual_gross_revenue = gross_revenue * annualization_factor

    # Turnover and coverage
    inventory_turnover = annual_cmv / total_physical_cost
    days_of_inventory = 365.0 / inventory_turnover
    years_of_inventory = days_of_inventory / 365.0

    return {
        "total_skus": len(df_stock),
        "unique_skus": df_stock["sku_id"].nunique(),
        "total_physical_units": total_physical_units,
        "total_physical_cost_brl": round(total_physical_cost, 2),
        "total_suggested_retail_brl": round(total_suggested_retail, 2),
        "total_available_cost_brl": round(total_available_cost, 2),
        "excess_defensive_cost_brl": round(total_excess_defensive_cost, 2),
        "period_days": round(period_days, 1),
        "annual_gross_revenue_brl": round(annual_gross_revenue, 2),
        "annual_cmv_brl": round(annual_cmv, 2),
        "annual_units_sold": round(annual_units_sold, 1),
        "inventory_turnover_annual": round(inventory_turnover, 4),
        "days_of_inventory_coverage": round(days_of_inventory, 1),
        "years_of_inventory_coverage": round(years_of_inventory, 2),
    }


def compute_profitability_tree(df_sales: pd.DataFrame) -> Dict[str, Any]:
    """
    Deconstructs the sales accounting structure into a strict income statement (DRE).
    """
    gross_rev = float(df_sales["receita_bruta"].sum())
    discounts = float(df_sales["desconto_reais"].sum())
    net_rev = float(df_sales["receita_liquida"].sum())
    cmv = float(df_sales["custo_produto"].sum())
    outbound_freight = float(df_sales["custo_frete"].sum())
    contribution_margin = float(df_sales["margem_contribuicao"].sum())

    # Order return impacts
    returned_orders = df_sales[df_sales["devolvido"] == True]
    num_returns = len(returned_orders)
    return_rate_pct = (num_returns / len(df_sales)) * 100.0
    returned_gross_rev = float(returned_orders["receita_bruta"].sum())
    returned_freight_loss = float(returned_orders["custo_frete"].sum())

    # Reverse logistics handling assumption (R$ 40 per case based on sector benchmark)
    unit_reverse_handling_cost = 40.0
    estimated_reverse_handling_total = num_returns * unit_reverse_handling_cost

    # Negative margin orders due to freight subsidy
    negative_margin_orders = df_sales[df_sales["margem_contribuicao"] < 0]
    num_negative_margin = len(negative_margin_orders)
    negative_margin_loss = float(negative_margin_orders["margem_contribuicao"].sum())

    return {
        "gross_revenue": round(gross_rev, 2),
        "discounts": round(discounts, 2),
        "discounts_pct": round((discounts / gross_rev) * 100.0, 2),
        "net_revenue": round(net_rev, 2),
        "net_revenue_pct": round((net_rev / gross_rev) * 100.0, 2),
        "cmv": round(cmv, 2),
        "cmv_pct": round((cmv / gross_rev) * 100.0, 2),
        "outbound_freight": round(outbound_freight, 2),
        "outbound_freight_pct": round((outbound_freight / gross_rev) * 100.0, 2),
        "contribution_margin": round(contribution_margin, 2),
        "contribution_margin_pct": round((contribution_margin / gross_rev) * 100.0, 2),
        "returns_count": num_returns,
        "returns_rate_pct": round(return_rate_pct, 2),
        "returns_gross_revenue": round(returned_gross_rev, 2),
        "returns_freight_lost": round(returned_freight_loss, 2),
        "estimated_reverse_handling_cost": round(estimated_reverse_handling_total, 2),
        "negative_margin_orders_count": num_negative_margin,
        "negative_margin_loss_brl": round(negative_margin_loss, 2),
    }


def analyze_customer_service_friction(
    df_service: pd.DataFrame, df_sales: pd.DataFrame
) -> Dict[str, Any]:
    """
    Quantifies customer support cost, delivery friction, and sizing defect tickets.
    """
    total_tickets = len(df_service)
    total_cost = float(df_service["custo_operacional_ticket"].sum())
    mean_csat = float(df_service["nota_csat"].mean())

    # Delivery status inquiry ('Onde está meu pedido?')
    order_status_mask = df_service["categoria_problema"].str.contains(
        "pedido", case=False, na=False
    )
    order_status_tickets = int(order_status_mask.sum())
    order_status_cost = float(
        df_service.loc[order_status_mask, "custo_operacional_ticket"].sum()
    )

    # Defect and size exchange
    defect_mask = df_service["categoria_problema"].str.contains(
        "defeito", case=False, na=False
    )
    size_mask = df_service["categoria_problema"].str.contains(
        "tamanho", case=False, na=False
    )
    product_issue_tickets = int((defect_mask | size_mask).sum())
    product_issue_cost = float(
        df_service.loc[defect_mask | size_mask, "custo_operacional_ticket"].sum()
    )

    # 2023 filtered service (aligned with sales horizon)
    df_service_2023 = df_service[df_service["data_abertura"].dt.year == 2023]
    cost_2023 = float(df_service_2023["custo_operacional_ticket"].sum())
    tickets_2023 = len(df_service_2023)

    return {
        "total_tickets": total_tickets,
        "total_cost_brl": round(total_cost, 2),
        "mean_csat": round(mean_csat, 2),
        "order_status_tickets": order_status_tickets,
        "order_status_pct": round((order_status_tickets / total_tickets) * 100.0, 2),
        "order_status_cost_brl": round(order_status_cost, 2),
        "product_issue_tickets": product_issue_tickets,
        "product_issue_pct": round((product_issue_tickets / total_tickets) * 100.0, 2),
        "product_issue_cost_brl": round(product_issue_cost, 2),
        "tickets_2023_count": tickets_2023,
        "tickets_2023_cost_brl": round(cost_2023, 2),
    }


def main():
    data = load_and_sanitize_data()
    inv_res = investigate_inventory_anomaly(data["stock"], data["sales"])
    prof_res = compute_profitability_tree(data["sales"])
    serv_res = analyze_customer_service_friction(data["service"], data["sales"])

    print("=== 1. AUDITORIA DO ESTOQUE VS FATURAMENTO ===")
    for k, v in inv_res.items():
        print(f"  {k}: {v}")

    print("\n=== 2. ARVORE DE LUCRATIVIDADE (DRE CONCILIADA) ===")
    for k, v in prof_res.items():
        print(f"  {k}: {v}")

    print("\n=== 3. ATRITO OPERACIONAL E ATENDIMENTO ===")
    for k, v in serv_res.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
