"""
Customer Service (SAC) Root-Cause and AI Automation Potential Analysis.
Quantifies recurring ticket themes, operational friction, automation feasibility tiers,
and financial/productivity gains from intelligent triage.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


def analyze_customer_service_automation(
    service_path: str = "atendimento.csv",
) -> Dict[str, Any]:
    """
    Evaluates support ticket volume, costs, channels, resolution times,
    and models productivity gains under an AI-first automated triage architecture.
    """
    df = pd.read_csv(service_path).dropna(subset=["ticket_id", "data_abertura"]).copy()
    df["data_abertura"] = pd.to_datetime(df["data_abertura"])

    total_tickets = len(df)
    total_cost = float(df["custo_operacional_ticket"].sum())
    mean_csat = float(df["nota_csat"].mean())
    mean_frt = float(df["tempo_primeira_resposta_minutos"].mean())

    # 1. Volume and Economics by Problem Category
    # Clean category names for consistent grouping
    def clean_category(cat: str) -> str:
        cat_lower = str(cat).lower()
        if "pedido" in cat_lower:
            return "Onde está meu pedido?"
        elif "defeito" in cat_lower:
            return "Defeito"
        elif "tamanho" in cat_lower:
            return "Troca de Tamanho"
        elif "t" in cat_lower and "cnica" in cat_lower:
            return "Dúvida Técnica"
        elif "pagamento" in cat_lower:
            return "Pagamento não aprovado"
        elif "elogio" in cat_lower:
            return "Elogio"
        return "Outros"

    df["categoria_limpa"] = df["categoria_problema"].apply(clean_category)

    category_stats = (
        df.groupby("categoria_limpa")
        .agg(
            tickets=("ticket_id", "count"),
            custo_total=("custo_operacional_ticket", "sum"),
            csat_medio=("nota_csat", "mean"),
            frt_medio_min=("tempo_primeira_resposta_minutos", "mean"),
        )
        .reset_index()
    )
    category_stats["pct_tickets"] = (
        category_stats["tickets"] / total_tickets * 100.0
    ).round(2)
    category_stats["custo_medio"] = (
        category_stats["custo_total"] / category_stats["tickets"]
    ).round(2)

    # 2. Channel Economics Breakdown
    channel_stats = (
        df.groupby("canal_entrada")
        .agg(
            tickets=("ticket_id", "count"),
            custo_total=("custo_operacional_ticket", "sum"),
            custo_unitario=("custo_operacional_ticket", "mean"),
            csat_medio=("nota_csat", "mean"),
            frt_medio_min=("tempo_primeira_resposta_minutos", "mean"),
        )
        .reset_index()
    )
    channel_stats["pct_tickets"] = (
        channel_stats["tickets"] / total_tickets * 100.0
    ).round(2)

    # 3. AI Automation & Deflection Modeling
    # Automation feasibility parameters by category:
    # Tier 1: High Deflection (Zero Human Touch) -> e.g. Tracking, Praise, Technical FAQ
    # Tier 2: Medium Deflection (Automated self-service with human oversight) -> Size, Payment retry
    # Tier 3: Low Deflection (AI Pre-qualification + Fast Human L2 Escalation) -> Defect/Damage
    automation_assumptions = {
        "Onde está meu pedido?": {
            "tier": "Tier 1: 100% Automatizável (Rastreio / API)",
            "deflection_rate": 0.90,
            "bot_cost": 1.50,
        },
        "Dúvida Técnica": {
            "tier": "Tier 1: 100% Automatizável (RAG / FAQ)",
            "deflection_rate": 0.75,
            "bot_cost": 1.50,
        },
        "Elogio": {
            "tier": "Tier 1: 100% Automatizável (Agradecimento Auto)",
            "deflection_rate": 1.00,
            "bot_cost": 0.50,
        },
        "Pagamento não aprovado": {
            "tier": "Tier 2: Semi-Automatizável (Link Pix / Retentativa)",
            "deflection_rate": 0.70,
            "bot_cost": 1.50,
        },
        "Troca de Tamanho": {
            "tier": "Tier 2: Semi-Automatizável (Self-Service Reversa)",
            "deflection_rate": 0.60,
            "bot_cost": 2.00,
        },
        "Defeito": {
            "tier": "Tier 3: Triagem IA + Escalação Prioritária N2 Humano",
            "deflection_rate": 0.25,
            "bot_cost": 5.00,
        },
    }

    automation_results = []
    total_new_cost = 0.0
    total_deflected_tickets = 0

    for cat_name, params in automation_assumptions.items():
        subset = df[df["categoria_limpa"] == cat_name]
        n_tickets = len(subset)
        baseline_cost = float(subset["custo_operacional_ticket"].sum())

        deflected = int(n_tickets * params["deflection_rate"])
        remaining = n_tickets - deflected
        total_deflected_tickets += deflected

        # Average human cost per ticket on non-bot channels
        human_cost_avg = float(
            subset[subset["canal_entrada"] != "ChatBot"][
                "custo_operacional_ticket"
            ].mean()
        )
        if np.isnan(human_cost_avg):
            human_cost_avg = 15.0

        new_cost = (deflected * params["bot_cost"]) + (remaining * human_cost_avg)
        savings = baseline_cost - new_cost
        total_new_cost += new_cost

        automation_results.append(
            {
                "categoria": cat_name,
                "tier_classificacao": params["tier"],
                "tickets_totais": n_tickets,
                "taxa_automacao_pct": round(params["deflection_rate"] * 100.0, 1),
                "tickets_automatizados": deflected,
                "custo_atual_brl": round(baseline_cost, 2),
                "novo_custo_brl": round(new_cost, 2),
                "economia_brl": round(savings, 2),
                "economia_pct": round((savings / baseline_cost) * 100.0, 2),
            }
        )

    total_savings = total_cost - total_new_cost
    # Hours saved assuming standard 15 minutes of human effort per handled ticket
    hours_saved = (total_deflected_tickets * 15.0) / 60.0

    return {
        "overview": {
            "total_tickets": total_tickets,
            "total_cost_brl": round(total_cost, 2),
            "mean_csat": round(mean_csat, 2),
            "mean_frt_minutes": round(mean_frt, 1),
        },
        "category_breakdown": category_stats.to_dict(orient="records"),
        "channel_breakdown": channel_stats.to_dict(orient="records"),
        "automation_modeling": {
            "categories_simulation": automation_results,
            "total_deflected_tickets": total_deflected_tickets,
            "total_deflection_rate_pct": round(
                (total_deflected_tickets / total_tickets) * 100.0, 2
            ),
            "total_hours_saved": round(hours_saved, 1),
            "baseline_total_cost_brl": round(total_cost, 2),
            "new_total_cost_brl": round(total_new_cost, 2),
            "total_savings_brl": round(total_savings, 2),
            "total_savings_pct": round((total_savings / total_cost) * 100.0, 2),
        },
    }


if __name__ == "__main__":
    res = analyze_customer_service_automation()
    print("Customer Service Analysis Completed:")
    print("Overview:", res["overview"])
    print("Automation Simulation Summary:", res["automation_modeling"])
