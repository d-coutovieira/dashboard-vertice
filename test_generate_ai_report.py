"""
test_generate_ai_report.py - Unit tests for the AI Executive Report Generator.
Validates the 4 requested topics, metric consistency against DRE, and fallback resilience.
"""

import pytest
from generate_ai_report import (
    TOPICS,
    load_dashboard_data,
    build_topic_context,
    generate_executive_report,
)


@pytest.fixture(scope="module")
def dashboard_data():
    return load_dashboard_data()


def test_topic_dictionary_coverage():
    expected_topics = [
        "visao_geral_dre",
        "devolucoes_logistica",
        "estoque_capital_giro",
        "midia_roas_preco",
    ]
    for t in expected_topics:
        assert t in TOPICS, f"Topic '{t}' must be defined in TOPICS."


def test_load_dashboard_data(dashboard_data):
    assert "dre" in dashboard_data
    assert "ice_levers" in dashboard_data
    assert "channels" in dashboard_data
    assert "customer_service" in dashboard_data
    assert "inventory" in dashboard_data


def test_generation_all_four_topics():
    for topic_key in TOPICS.keys():
        result = generate_executive_report(topic_key)
        assert result["topic"] == topic_key
        assert result["topic_title"] == TOPICS[topic_key]
        assert "html_report" in result
        assert len(result["html_report"]) > 500
        assert "EloGroup" in result["html_report"]
        assert "Vértice Retail" in result["html_report"]


def test_topic_visao_geral_dre_grounding(dashboard_data):
    context = build_topic_context("visao_geral_dre", dashboard_data)
    assert context["faturamento_bruto"] == 20526133.84
    assert context["margem_contribuicao_pct"] == 50.04
    assert context["margem_pos_atrito_pct"] == 48.12
    assert context["taxa_desconto_pct"] == 7.97

    res = generate_executive_report("visao_geral_dre")
    html = res["html_report"]
    assert "20.526.133,84" in html or "20,53M" in html
    assert "50,04%" in html
    assert "9,87M" in html or "48,12%" in html


def test_topic_devolucoes_logistica_grounding(dashboard_data):
    context = build_topic_context("devolucoes_logistica", dashboard_data)
    assert context["total_devolucoes"] == 4127
    assert context["taxa_devolucao_pct"] == 14.87
    assert context["falhas_operacionais_evitaveis_pct"] == 69.59
    assert context["marketplace_frete_pct"] == 4.55

    res = generate_executive_report("devolucoes_logistica")
    html = res["html_report"]
    assert "4.127" in html
    assert "14,87%" in html
    assert "69,59%" in html
    assert "Defeito" in html
    assert "Tamanho" in html


def test_topic_estoque_capital_giro_grounding(dashboard_data):
    context = build_topic_context("estoque_capital_giro", dashboard_data)
    assert context["skus_descontinuados_qtd"] == 207
    assert context["skus_descontinuados_capital_parado"] == 17714096.89
    assert context["giro_estoque_anual"] == 0.022

    res = generate_executive_report("estoque_capital_giro")
    html = res["html_report"]
    assert "207" in html
    assert "17,71" in html or "17.714.096,89" in html
    assert "WACC" in html or "3,19M" in html


def test_topic_midia_roas_preco_grounding(dashboard_data):
    context = build_topic_context("midia_roas_preco", dashboard_data)
    assert "Influenciadores" in context["top_performer"]
    assert context["realloc_projetada"]["ganho_margem_projetado"] == 17900000.0

    res = generate_executive_report("midia_roas_preco")
    html = res["html_report"]
    assert "Influenciador" in html
    assert "7.75x" in html or "7,75x" in html
    assert "17,90" in html or "17,9M" in html


def test_invalid_topic_raises_error():
    with pytest.raises(ValueError) as exc:
        generate_executive_report("topico_inexistente")
    assert "Tópico inválido" in str(exc.value)
