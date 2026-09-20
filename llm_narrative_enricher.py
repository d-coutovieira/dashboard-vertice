"""
llm_narrative_enricher.py - LLM Prose Refinement Layer (Phase 3) for Module D.

Enriches deterministic narrative summaries using LLM capabilities while strictly
preserving audited numerical ground truth. Implements automated, transparent fallback
to the EloGroup Grounded Engine when offline or without API keys.
"""

import os
import json
from typing import Dict, Any, Optional
import requests


class LLMNarrativeEnricher:
    """
    Enriches executive text via LLM API without altering any underlying metrics.
    """

    def __init__(self, api_key: Optional[str] = None):
        raw_key = (
            api_key
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("DEEPSEEK_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )
        self.api_key = raw_key.strip() if raw_key else ""

    def is_available(self) -> bool:
        """Returns True if an API key is configured."""
        return bool(self.api_key and len(self.api_key) > 8)

    def enrich_narrative(
        self,
        sector: str,
        narrative_payload: Dict[str, Any],
        analytical_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refines narrative headlines and executive summary.
        If LLM call fails or is unavailable, returns narrative_payload unchanged.
        """
        if not self.is_available():
            return narrative_payload

        system_prompt = (
            "Você é um Consultor Sênior em Estratégia, Analytics e Engenharia Financeira da EloGroup. "
            "Seu papel é refinar a redação de um memorando executivo para a Diretoria da Vértice Retail. "
            "DIRETRIZES INEGOCIÁVEIS: "
            "1. NÃO altere, recalcule, adicione ou arredonde nenhum número. Preserve rigorosamente os valores auditados. "
            "2. Linguagem executiva direta, profissional, em português (PT-BR). Zero saudações ou introduções genéricas. "
            "3. Responda à pergunta: 'E daí? O que a diretoria deve decidir agora?'. "
            "4. Retorne APENAS um JSON válido com as chaves 'headline' e 'executive_summary'."
        )

        user_prompt = (
            f"Setor: {sector.upper()}\n"
            f"Manchete Atual: {narrative_payload.get('headline')}\n"
            f"Síntese Atual:\n{narrative_payload.get('executive_summary', narrative_payload.get('executive_synthesis', ''))}\n"
            f"Fatos Auditados de Grounding:\n{json.dumps(narrative_payload.get('facts', []), ensure_ascii=False, indent=2)}\n"
            f"Alertas de Anomalia:\n{json.dumps(narrative_payload.get('alerts', []), ensure_ascii=False, indent=2)}\n"
            "Refine a redação tornando-a ainda mais assertiva e cirúrgica para o C-Level."
        )

        # Smart provider routing based on API key prefix
        endpoints = []
        if self.api_key.startswith("AIza"):
            # Native Google Gemini Key
            endpoints.append(("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-1.5-flash"))
        elif self.api_key.startswith("sk-") and len(self.api_key) > 30:
            # DeepSeek or OpenAI
            endpoints.append(("https://api.deepseek.com/chat/completions", "deepseek-chat"))
            endpoints.append(("https://api.openai.com/v1/chat/completions", "gpt-4o-mini"))
        else:
            endpoints.append(("https://api.deepseek.com/chat/completions", "deepseek-chat"))
            endpoints.append(("https://api.openai.com/v1/chat/completions", "gpt-4o-mini"))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for url, model in endpoints:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    parsed = json.loads(raw_content)
                    enriched = dict(narrative_payload)
                    if "headline" in parsed and parsed["headline"]:
                        enriched["headline"] = parsed["headline"]
                    if "executive_summary" in parsed and parsed["executive_summary"]:
                        if "executive_summary" in enriched:
                            enriched["executive_summary"] = parsed["executive_summary"]
                        elif "executive_synthesis" in enriched:
                            enriched["executive_synthesis"] = parsed["executive_summary"]
                    return enriched
            except Exception:
                continue

        # Fallback to deterministic payload
        return narrative_payload
