# Semana de Forte Volume (1.219 pedidos), mas com Erosão Severa de Margem por Descontos (13,27%)

**Cliente:** Vértice Retail | **Consultoria:** EloGroup Strategic Intelligence
**Janela / Semana:** Consolidado | **Gerado em:** 19/09/2026 às 15:16:45

---

## 1. Síntese Analítica Executiva

No período 2023-W47, a Vértice Retail processou <strong>1.219 pedidos</strong> gerando <strong>R$ 889.225,25 em receita bruta</strong> e <strong>R$ 391.886,40 de margem de contribuição (44,07%)</strong>. A concessão de descontos atingiu <strong>R$ 118.001,60 (13,27%)</strong>. A decomposição de variância indica impacto de volume de R$ 264.540,94 e impacto de preço de R$ 10.544,35 contra o ciclo anterior.

## 2. Alertas de Operação

- **[CRITICO]** Concessão crítica de descontos comerciais: Desconto atingiu 13.27% (limite crítico 9.0%).

## 3. Fatos e Métricas Auditadas

| Métrica | Valor | Fonte | Impacto |
| :--- | :--- | :--- | :--- |
| Receita Bruta Faturada | R$ 889.225,25 | DRE Auditada / vendas.csv | Base de faturamento bruto realizada no período. |
| Volume de Pedidos | 1.219 | vendas.csv | Ticket médio resultante de R$ 729,47 por pedido. |
| Descontos Concedidos | R$ 118.001,60 (13,27%) | DRE Auditada / vendas.csv | Principal redutor de margem bruta entre receita faturada e realizada. |
| Margem de Contribuição | R$ 391.886,40 (44,07%) | DRE Auditada / vendas.csv | Resultado operacional gerado antes dos atritos de pós-venda. |

## 4. Alavancas Identificadas pelo Diagnóstico

| Prioridade | Alavanca | Gargalo Causal | Métrica de Grounding |
| :--- | :--- | :--- | :--- |
| #2 | Piso de Frete Mínimo (R$ 150) & Repasse de Frete em Marketplace | Subsídio abusivo de frete corroendo margem em pedidos de baixo ticket. | 741 transações em margem negativa identificadas no diagnóstico; frete atinge 4,55% da receita. |
| #6 | Calibragem de Desconto Comercial & Trava de Margem | Descontos promocionais excessivos em campanhas sazonais comprimindo a DRE. | R$ 1.636.799,83 em descontos (7,97% da receita); pico de 9,55% na Black Friday. |

> **Nota de Escopo:** O detalhamento executivo de prazos, metas graduais e modelagem de retorno incremental constitui o Business Case (documento complementar).
