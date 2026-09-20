"""
Margin Degradation Analysis for Vertice Retail.
Deconstructs margin losses across Time (Period), Channel, Category, Ticket Size,
and Product/SKU dimensions.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd


def analyze_margin_by_dimension(df_sales: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes and quantifies margin leakage across Period, Channel, Category,
    Ticket Size, and High-Return SKUs.
    """
    df = df_sales.dropna(subset=["order_id", "quantidade"]).copy()
    df["data_pedido"] = pd.to_datetime(df["data_pedido"])
    df["mes"] = df["data_pedido"].dt.to_period("M").astype(str)
    df["devolvido"] = df["devolvido"].astype(bool)

    # Effective margin considering returns:
    # Returned products: revenue is refunded (0), product returned to stock (CMV=0),
    # outbound shipping lost, and reverse logistics handling cost (R$ 40/case).
    df["receita_efetiva"] = np.where(df["devolvido"], 0.0, df["receita_liquida"])
    df["cmv_efetivo"] = np.where(df["devolvido"], 0.0, df["custo_produto"])
    df["custo_reversa"] = np.where(df["devolvido"], 40.0, 0.0)
    df["margem_pos_devolucao"] = (
        df["receita_efetiva"]
        - df["cmv_efetivo"]
        - df["custo_frete"]
        - df["custo_reversa"]
    )

    total_gross_rev = float(df["receita_bruta"].sum())
    total_net_rev = float(df["receita_liquida"].sum())
    total_margin = float(df["margem_contribuicao"].sum())

    # 1. Period Degradation (Black Friday effect - Nov 2023 vs baseline)
    monthly = df.groupby("mes").agg(
        pedidos=("order_id", "count"),
        receita_bruta=("receita_bruta", "sum"),
        desconto=("desconto_reais", "sum"),
        pct_desconto=(
            "desconto_reais",
            lambda d: d.sum() / df.loc[d.index, "receita_bruta"].sum() * 100,
        ),
        pct_margem=(
            "margem_contribuicao",
            lambda m: m.sum() / df.loc[m.index, "receita_bruta"].sum() * 100,
        ),
        pct_margem_pos_dev=(
            "margem_pos_devolucao",
            lambda m: m.sum() / df.loc[m.index, "receita_bruta"].sum() * 100,
        ),
        taxa_devolucao=("devolvido", lambda d: d.mean() * 100),
    )
    nov_discount_pct = float(monthly.loc["2023-11", "pct_desconto"])
    jan_discount_pct = float(monthly.loc["2023-01", "pct_desconto"])
    nov_margin_pct = float(monthly.loc["2023-11", "pct_margem"])

    # 2. Channel Degradation (Marketplace shipping anomaly)
    channel = df.groupby("canal").agg(
        pedidos=("order_id", "count"),
        receita_bruta=("receita_bruta", "sum"),
        pct_desconto=(
            "desconto_reais",
            lambda d: d.sum() / df.loc[d.index, "receita_bruta"].sum() * 100,
        ),
        pct_frete=(
            "custo_frete",
            lambda f: f.sum() / df.loc[f.index, "receita_bruta"].sum() * 100,
        ),
        pct_margem=(
            "margem_contribuicao",
            lambda m: m.sum() / df.loc[m.index, "receita_bruta"].sum() * 100,
        ),
        pct_margem_pos_dev=(
            "margem_pos_devolucao",
            lambda m: m.sum() / df.loc[m.index, "receita_bruta"].sum() * 100,
        ),
        pedidos_margem_neg=("margem_contribuicao", lambda m: (m < 0).sum()),
    )
    mktplace_freight_pct = float(channel.loc["Marketplace", "pct_frete"])
    other_channels_freight_pct = float(
        df[df["canal"] != "Marketplace"]["custo_frete"].sum()
        / df[df["canal"] != "Marketplace"]["receita_bruta"].sum()
        * 100
    )

    # 3. Ticket Size Breakdown (Freight erosion on low tickets <= R$ 100)
    df["faixa_ticket"] = pd.cut(
        df["receita_bruta"],
        bins=[0, 50, 100, 200, 500, 100000],
        labels=["R$ 0-50", "R$ 50-100", "R$ 100-200", "R$ 200-500", "R$ >500"],
    )
    low_ticket = df[df["receita_bruta"] <= 100.0]
    low_ticket_orders = len(low_ticket)
    low_ticket_freight = float(low_ticket["custo_frete"].sum())
    low_ticket_revenue = float(low_ticket["receita_bruta"].sum())
    low_ticket_freight_pct = (low_ticket_freight / low_ticket_revenue) * 100.0
    low_ticket_neg_margin_orders = int((low_ticket["margem_contribuicao"] < 0).sum())

    # 4. Returns & Reverse Logistics Leakage
    returned = df[df["devolvido"] == True]
    returned_revenue = float(returned["receita_bruta"].sum())
    returned_freight_loss = float(returned["custo_frete"].sum())
    returned_handling_cost = float(len(returned) * 40.0)
    returned_margin_lost = float(returned["margem_contribuicao"].sum())
    total_return_economic_drain = (
        returned_freight_loss + returned_handling_cost + returned_margin_lost
    )

    # 5. Top SKU Return Offenders (min 5 orders)
    sku_stats = df.groupby(["sku_id", "produto", "categoria"]).agg(
        pedidos=("order_id", "count"),
        receita_bruta=("receita_bruta", "sum"),
        taxa_devolucao=("devolvido", lambda d: d.mean() * 100),
        perda_margem_devolucao=(
            "margem_contribuicao",
            lambda m: df.loc[m.index, "margem_contribuicao"].sum()
            - df.loc[m.index, "margem_pos_devolucao"].sum(),
        ),
    )
    top_return_skus = (
        sku_stats[sku_stats["pedidos"] >= 5]
        .sort_values("taxa_devolucao", ascending=False)
        .head(10)
        .reset_index()
        .to_dict(orient="records")
    )

    return {
        "total_gross_revenue": round(total_gross_rev, 2),
        "total_contribution_margin": round(total_margin, 2),
        "period": {
            "nov_discount_pct": round(nov_discount_pct, 2),
            "jan_discount_pct": round(jan_discount_pct, 2),
            "nov_margin_pct": round(nov_margin_pct, 2),
            "discount_jump_pp": round(nov_discount_pct - jan_discount_pct, 2),
        },
        "channel": {
            "marketplace_freight_pct": round(mktplace_freight_pct, 2),
            "other_channels_freight_pct": round(other_channels_freight_pct, 2),
            "marketplace_margin_post_dev_pct": round(
                float(channel.loc["Marketplace", "pct_margem_pos_dev"]), 2
            ),
            "marketplace_orders": int(channel.loc["Marketplace", "pedidos"]),
        },
        "ticket_size": {
            "low_ticket_orders": low_ticket_orders,
            "low_ticket_revenue": round(low_ticket_revenue, 2),
            "low_ticket_freight": round(low_ticket_freight, 2),
            "low_ticket_freight_pct": round(low_ticket_freight_pct, 2),
            "low_ticket_negative_margin_orders": low_ticket_neg_margin_orders,
        },
        "returns": {
            "returned_orders_count": len(returned),
            "returned_gross_revenue": round(returned_revenue, 2),
            "returned_freight_loss": round(returned_freight_loss, 2),
            "returned_handling_cost": round(returned_handling_cost, 2),
            "returned_margin_lost": round(returned_margin_lost, 2),
            "total_economic_drain": round(total_return_economic_drain, 2),
            "drain_pct_gross_revenue": round(
                (total_return_economic_drain / total_gross_rev) * 100.0, 2
            ),
        },
        "top_return_skus": top_return_skus,
    }


if __name__ == "__main__":
    df_sales = pd.read_csv("vendas.csv")
    results = analyze_margin_by_dimension(df_sales)
    print("Margin Degradation Analysis Completed:")
    print(results)
