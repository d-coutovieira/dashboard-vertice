"""
Customer Segmentation, RFM Quality, LTV, and Churn Risk Analysis.
Evaluates customer tiers, transaction economics, support friction,
and defines actionable retention, upsell, and divestment strategies.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


def analyze_customer_segments(
    clients_path: str = "clientes.csv",
    sales_path: str = "vendas.csv",
    service_path: str = "atendimento.csv",
) -> Dict[str, Any]:
    """
    Deconstructs RFM segments across cumulative CRM LTV, realized transaction margins,
    return rates, support friction, and strategic actions.
    """
    df_cli = pd.read_csv(clients_path).dropna(subset=["customer_id"]).copy()
    df_sales = pd.read_csv(sales_path).dropna(subset=["order_id", "quantidade"]).copy()
    df_service = pd.read_csv(service_path).dropna(subset=["ticket_id"]).copy()

    df_sales["devolvido"] = df_sales["devolvido"].astype(bool)

    # 1. CRM Level RFM Summary (15,000 customers)
    total_clients = len(df_cli)
    total_ltv = float(df_cli["ltv_acumulado"].sum())

    rfm_crm = (
        df_cli.groupby("segmento_rfm")
        .agg(
            total_clientes=("customer_id", "count"),
            pedidos_historicos_medios=("total_pedidos_historico", "mean"),
            ltv_medio=("ltv_acumulado", "mean"),
            ltv_total=("ltv_acumulado", "sum"),
            renda_media=("renda_estimada", "mean"),
            opt_in_newsletter_pct=("opt_in_newsletter", lambda x: x.mean() * 100.0),
        )
        .reset_index()
    )
    rfm_crm["pct_base"] = (rfm_crm["total_clientes"] / total_clients * 100.0).round(2)
    rfm_crm["pct_ltv_total"] = (rfm_crm["ltv_total"] / total_ltv * 100.0).round(2)

    # 2. Transactional Realized Economics (vendas.csv cross-table)
    v_cust = (
        df_sales.groupby("customer_id")
        .agg(
            pedidos=("order_id", "count"),
            receita_bruta=("receita_bruta", "sum"),
            desconto=("desconto_reais", "sum"),
            margem=("margem_contribuicao", "sum"),
            devolucoes=("devolvido", "sum"),
        )
        .reset_index()
    )
    m_cust = v_cust.merge(
        df_cli[["customer_id", "segmento_rfm", "nivel_fidelidade"]],
        on="customer_id",
        how="left",
    )

    rfm_trans = (
        m_cust.groupby("segmento_rfm")
        .agg(
            clientes_ativos=("customer_id", "count"),
            pedidos_reais=("pedidos", "sum"),
            receita_real=("receita_bruta", "sum"),
            margem_real=("margem", "sum"),
            ticket_medio=("receita_bruta", lambda r: r.sum() / m_cust.loc[r.index, "pedidos"].sum()),
            pct_desconto=("desconto", lambda d: d.sum() / m_cust.loc[d.index, "receita_bruta"].sum() * 100.0),
            pct_margem=("margem", lambda m: m.sum() / m_cust.loc[m.index, "receita_bruta"].sum() * 100.0),
            taxa_devolucao=("devolucoes", lambda dev: dev.sum() / m_cust.loc[dev.index, "pedidos"].sum() * 100.0),
        )
        .reset_index()
    )

    # 3. Support Friction by Segment (atendimento.csv cross-table)
    m_serv = df_service.merge(
        df_cli[["customer_id", "segmento_rfm"]], on="customer_id", how="left"
    )
    rfm_serv = (
        m_serv.groupby("segmento_rfm")
        .agg(
            tickets=("ticket_id", "count"),
            custo_sac=("custo_operacional_ticket", "sum"),
            csat_medio=("nota_csat", "mean"),
        )
        .reset_index()
    )
    rfm_serv["pct_tickets"] = (
        rfm_serv["tickets"] / len(df_service) * 100.0
    ).round(2)

    # Merge all 3 views into a unified executive table
    unified = rfm_crm.merge(rfm_trans, on="segmento_rfm", how="left").merge(
        rfm_serv, on="segmento_rfm", how="left"
    )

    # Strategy tagging logic
    def assign_strategy(segment: str) -> str:
        if segment in ["Campeão", "Fiel"]:
            return "Retenção VIP & Fila Prioritária (Blindagem de LTV / White-Glove SAC)"
        elif segment == "Promissor":
            return "Upsell & Cross-Sell (Campanha de Fidelização para migrar para Fiel)"
        elif segment == "Em Risco":
            return "Resgate Ativo Anti-Churn (Contato proativo e resolução de gargalo logístico)"
        elif segment in ["Hibernando", "Churn"]:
            return "Corte de Investimento & Redução de Cupons (Evitar queima de margem em reativação inútil)"
        return "Geral"

    unified["estrategia_recomendada"] = unified["segmento_rfm"].apply(assign_strategy)

    return {
        "summary": {
            "total_customers": total_clients,
            "total_ltv_brl": round(total_ltv, 2),
            "top_value_segments_ltv_share_pct": round(
                float(
                    unified[unified["segmento_rfm"].isin(["Campeão", "Fiel"])][
                        "pct_ltv_total"
                    ].sum()
                ),
                2,
            ),
            "churn_discount_rate_pct": round(
                float(
                    unified[unified["segmento_rfm"] == "Churn"][
                        "pct_desconto"
                    ].values[0]
                ),
                2,
            ),
            "churn_return_rate_pct": round(
                float(
                    unified[unified["segmento_rfm"] == "Churn"][
                        "taxa_devolucao"
                    ].values[0]
                ),
                2,
            ),
        },
        "segments_detail": unified.to_dict(orient="records"),
    }


if __name__ == "__main__":
    res = analyze_customer_segments()
    print("Customer Segments Analysis:")
    print("Summary:", res["summary"])
    for row in res["segments_detail"]:
        print(f"\nSegment: {row['segmento_rfm']} -> {row['estrategia_recomendada']}")
        print(f"  Clients: {row['total_clientes']} ({row['pct_base']}%), LTV: R$ {row['ltv_total']:,.2f} ({row['pct_ltv_total']}%)")
        print(f"  Realized Margin: {row['pct_margem']:.2f}%, Return Rate: {row['taxa_devolucao']:.2f}%, Discount: {row['pct_desconto']:.2f}%")
        print(f"  SAC Tickets: {row['tickets']} ({row['pct_tickets']}%), SAC Cost: R$ {row['custo_sac']:,.2f}")
