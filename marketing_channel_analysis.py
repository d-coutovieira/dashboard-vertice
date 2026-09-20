"""
Marketing Channel and Customer Acquisition Quality Analysis.
Evaluates ROAS, CAC, Ticket Size, Return Rates, Margin post-returns,
and models long-term budget reallocation.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


def evaluate_acquisition_channels(
    mkt_path: str = "marketing.csv", sales_path: str = "vendas.csv"
) -> Dict[str, Any]:
    """
    Cross-analyzes campaign performance with post-purchase customer economics.
    """
    df_mkt = pd.read_csv(mkt_path)
    df_sales = pd.read_csv(sales_path).dropna(subset=["order_id", "quantidade"]).copy()

    df_sales["devolvido"] = df_sales["devolvido"].astype(bool)
    df_sales["receita_efetiva"] = np.where(
        df_sales["devolvido"], 0.0, df_sales["receita_liquida"]
    )
    df_sales["cmv_efetivo"] = np.where(
        df_sales["devolvido"], 0.0, df_sales["custo_produto"]
    )
    df_sales["custo_reversa_est"] = np.where(df_sales["devolvido"], 40.0, 0.0)
    df_sales["margem_pos_dev"] = (
        df_sales["receita_efetiva"]
        - df_sales["cmv_efetivo"]
        - df_sales["custo_frete"]
        - df_sales["custo_reversa_est"]
    )

    # 1. Marketing metrics aggregation
    mkt_summary = (
        df_mkt.groupby("canal")
        .agg(
            investimento=("investimento_reais", "sum"),
            receita_gerada=("receita_gerada", "sum"),
            conversoes=("conversoes", "sum"),
            roas=(
                "receita_gerada",
                lambda r: r.sum() / df_mkt.loc[r.index, "investimento_reais"].sum(),
            ),
            cac_medio=("cac", "mean"),
        )
        .reset_index()
    )

    # 2. Sales economics aggregation
    sales_summary = (
        df_sales.groupby("canal")
        .agg(
            pedidos=("order_id", "count"),
            receita_bruta=("receita_bruta", "sum"),
            ticket_medio=("receita_bruta", "mean"),
            pct_desconto=(
                "desconto_reais",
                lambda d: d.sum()
                / df_sales.loc[d.index, "receita_bruta"].sum()
                * 100.0,
            ),
            pct_frete=(
                "custo_frete",
                lambda f: f.sum()
                / df_sales.loc[f.index, "receita_bruta"].sum()
                * 100.0,
            ),
            pct_margem_bruta=(
                "margem_contribuicao",
                lambda m: m.sum()
                / df_sales.loc[m.index, "receita_bruta"].sum()
                * 100.0,
            ),
            taxa_devolucao=("devolvido", lambda d: d.mean() * 100.0),
            pct_margem_real=(
                "margem_pos_dev",
                lambda m: m.sum()
                / df_sales.loc[m.index, "receita_bruta"].sum()
                * 100.0,
            ),
            pedidos_margem_neg=("margem_contribuicao", lambda m: (m < 0).sum()),
        )
        .reset_index()
    )

    combined = pd.merge(mkt_summary, sales_summary, on="canal")

    # Classification logic
    def classify_channel(row: pd.Series) -> str:
        if row["roas"] >= 6.0 and row["ticket_medio"] > 800:
            return "Tier 1: Alto Valor e Eficiência (Prioridade Máxima de Investimento)"
        elif row["roas"] >= 4.0 and row["cac_medio"] <= 4.0:
            return "Tier 1: Tração Sustentável em Escala (Aumentar Orçamento)"
        elif row["pct_margem_real"] > 42.0 and row["pct_frete"] < 1.0:
            return "Tier 2: Rentabilidade e Retenção (Manter / Otimizar)"
        elif row["pct_desconto"] > 8.4:
            return "Tier 3: Volume Viciado em Desconto (Otimizar / Reduzir Cupons)"
        elif row["pct_frete"] > 3.0 or row["pct_margem_real"] < 39.0:
            return "Tier 4: Ilusão de Volume / Margem Destruída (Desinvestir Imediatamente)"
        return "Tier 2: Maduro e Equilibrado"

    combined["classificacao"] = combined.apply(classify_channel, axis=1)

    # 3. Budget Reallocation Simulation
    # Reallocate: -R$ 10M from Marketplace, -R$ 5M from Google Ads
    # +R$ 10M to Influenciador, +R$ 5M to TikTok Ads
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
    new_inv = curr_inv + deltas

    # Conservative diminishing returns: -15% for Influencer boost, -10% for TikTok
    inc_roas = curr_roas.copy()
    for i, c in enumerate(channels):
        if c == "Influenciador":
            inc_roas[i] *= 0.85
        elif c == "TikTok Ads":
            inc_roas[i] *= 0.90

    current_gen_rev = float((curr_inv * curr_roas).sum())
    new_gen_rev = float(
        ((curr_inv * curr_roas) + (deltas * inc_roas)).sum()
    )
    current_gen_margin = float((curr_inv * curr_roas * margin_real).sum())
    new_gen_margin = float(
        (((curr_inv * curr_roas) + (deltas * inc_roas)) * margin_real).sum()
    )

    return {
        "channels_table": combined.to_dict(orient="records"),
        "simulation": {
            "current_generated_revenue_brl": round(current_gen_rev, 2),
            "new_generated_revenue_brl": round(new_gen_rev, 2),
            "delta_generated_revenue_brl": round(new_gen_rev - current_gen_rev, 2),
            "pct_revenue_growth": round(
                (new_gen_rev / current_gen_rev - 1.0) * 100.0, 2
            ),
            "current_generated_margin_brl": round(current_gen_margin, 2),
            "new_generated_margin_brl": round(new_gen_margin, 2),
            "delta_generated_margin_brl": round(new_gen_margin - current_gen_margin, 2),
            "pct_margin_growth": round(
                (new_gen_margin / current_gen_margin - 1.0) * 100.0, 2
            ),
        },
    }


if __name__ == "__main__":
    res = evaluate_acquisition_channels()
    print("Channel Evaluation Result:")
    for row in res["channels_table"]:
        print(f"{row['canal']}: {row['classificacao']} (ROAS: {row['roas']:.2f}x, Real Margin: {row['pct_margem_real']:.2f}%)")
    print("\nSimulation:", res["simulation"])
