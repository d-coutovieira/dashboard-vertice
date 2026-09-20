"""
Operational Failure and Post-Sale Friction Analysis for Vertice Retail.
Quantifies the financial cost of operational failures: Returns (Defects, Size, Delays),
Delivery SLA breaches, Customer Support overload, Supplier Lead Times, and Stockout/Obsolescence.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd


def analyze_operational_failures(
    sales_path: str = "vendas.csv",
    stock_path: str = "estoque.csv",
    service_path: str = "atendimento.csv",
) -> Dict[str, Any]:
    """
    Quantifies the economic drain of operational failures across logistics,
    quality control, customer service, and supply chain.
    """
    df_sales = pd.read_csv(sales_path).dropna(subset=["order_id", "quantidade"]).copy()
    df_stock = pd.read_csv(stock_path).dropna(subset=["sku_id"]).copy()
    df_service = (
        pd.read_csv(service_path).dropna(subset=["ticket_id", "data_abertura"]).copy()
    )

    df_sales["devolvido"] = df_sales["devolvido"].astype(bool)

    # 1. Operational Return Failures (Defects, Sizing, Delivery Delays)
    returned = df_sales[df_sales["devolvido"]].copy()
    unit_reverse_cost = 40.0

    return_reasons = (
        returned.groupby("motivo_devolucao")
        .agg(
            pedidos=("order_id", "count"),
            receita_estornada=("receita_bruta", "sum"),
            frete_perdido=("custo_frete", "sum"),
            margem_estornada=("margem_contribuicao", "sum"),
        )
        .reset_index()
    )

    return_reasons["custo_reversa_manuseio"] = (
        return_reasons["pedidos"] * unit_reverse_cost
    )
    return_reasons["impacto_economico_direto"] = (
        return_reasons["frete_perdido"]
        + return_reasons["custo_reversa_manuseio"]
        + return_reasons["margem_estornada"]
    )

    operational_reasons = ["Produto com defeito", "Tamanho errado", "Atraso na entrega"]
    op_returns = return_reasons[
        return_reasons["motivo_devolucao"].isin(operational_reasons)
    ]
    total_op_return_orders = int(op_returns["pedidos"].sum())
    total_op_revenue_refunded = float(op_returns["receita_estornada"].sum())
    total_op_direct_drain = float(op_returns["impacto_economico_direto"].sum())

    # 2. Delivery SLA Breaches (>7 days and >10 days)
    total_sales_orders = len(df_sales)
    orders_gt_7d = int((df_sales["tempo_entrega_real"] > 7.0).sum())
    orders_gt_10d = int((df_sales["tempo_entrega_real"] > 10.0).sum())
    pct_gt_7d = (orders_gt_7d / total_sales_orders) * 100.0
    pct_gt_10d = (orders_gt_10d / total_sales_orders) * 100.0

    # 3. Customer Service (SAC) Friction Driven by Operations
    tracking_tickets = df_service[
        df_service["categoria_problema"].str.contains("pedido", case=False, na=False)
    ]
    defect_tickets = df_service[
        df_service["categoria_problema"].str.contains("defeito", case=False, na=False)
    ]
    size_tickets = df_service[
        df_service["categoria_problema"].str.contains("tamanho", case=False, na=False)
    ]

    tracking_cost = float(tracking_tickets["custo_operacional_ticket"].sum())
    defect_cost = float(defect_tickets["custo_operacional_ticket"].sum())
    size_cost = float(size_tickets["custo_operacional_ticket"].sum())
    total_sac_op_cost = tracking_cost + defect_cost + size_cost
    total_sac_op_tickets = (
        len(tracking_tickets) + len(defect_tickets) + len(size_tickets)
    )

    # 4. Inventory Status, Stockouts, and Discontinued Capital Trap
    stockout_skus = df_stock[df_stock["status_disponibilidade"] == "Ruptura"]
    critical_skus = df_stock[df_stock["status_disponibilidade"] == "Estoque Crítico"]
    discontinued_skus = df_stock[df_stock["status_disponibilidade"] == "Descontinuado"]

    discontinued_capital_tied = float(
        (
            discontinued_skus["estoque_fisico"]
            * discontinued_skus["custo_unitario"]
        ).sum()
    )

    # 5. Top Defective Suppliers
    defects_per_sku = (
        df_sales[df_sales["motivo_devolucao"] == "Produto com defeito"]
        .groupby("sku_id")["order_id"]
        .count()
        .rename("defeitos_count")
    )
    df_stock_defects = df_stock.merge(defects_per_sku, on="sku_id", how="left")
    df_stock_defects["defeitos_count"] = df_stock_defects["defeitos_count"].fillna(0)

    top_defect_suppliers = (
        df_stock_defects.groupby("fornecedor_id")
        .agg(
            total_skus=("sku_id", "count"),
            total_defeitos=("defeitos_count", "sum"),
            lead_time_medio=("lead_time_reposicao", "mean"),
        )
        .reset_index()
        .sort_values("total_defeitos", ascending=False)
        .head(5)
        .to_dict(orient="records")
    )

    return {
        "operational_returns": {
            "reasons_detail": return_reasons.to_dict(orient="records"),
            "operational_orders_count": total_op_return_orders,
            "pct_of_all_returns": round(
                (total_op_return_orders / len(returned)) * 100.0, 2
            ),
            "refunded_revenue_brl": round(total_op_revenue_refunded, 2),
            "direct_economic_drain_brl": round(total_op_direct_drain, 2),
        },
        "delivery_sla": {
            "total_orders": total_sales_orders,
            "orders_gt_7d": orders_gt_7d,
            "pct_gt_7d": round(pct_gt_7d, 2),
            "orders_gt_10d": orders_gt_10d,
            "pct_gt_10d": round(pct_gt_10d, 2),
        },
        "customer_service_friction": {
            "operational_tickets_count": total_sac_op_tickets,
            "pct_of_all_tickets": round(
                (total_sac_op_tickets / len(df_service)) * 100.0, 2
            ),
            "tracking_cost_brl": round(tracking_cost, 2),
            "defect_cost_brl": round(defect_cost, 2),
            "size_cost_brl": round(size_cost, 2),
            "total_sac_operational_cost_brl": round(total_sac_op_cost, 2),
        },
        "inventory_risk": {
            "stockout_skus_count": len(stockout_skus),
            "critical_skus_count": len(critical_skus),
            "discontinued_skus_count": len(discontinued_skus),
            "discontinued_capital_tied_brl": round(discontinued_capital_tied, 2),
        },
        "top_defect_suppliers": top_defect_suppliers,
    }


if __name__ == "__main__":
    res = analyze_operational_failures()
    print("Operational Failures Analysis:")
    print(res)
