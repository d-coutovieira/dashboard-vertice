# Resumo de Entrega — Diagnóstico Vértice Retail

> **Fase:** Diagnóstico (Árvore de Hipóteses + Auditoria de Dados)
> **Data de fechamento original:** 14/09/2026
> **Última revisão:** correção do Teste 3.2.3, formalização do Teste 4.1 (Raiz 4 · Capital Investido), remoção de todo conteúdo de Business Case/roadmap/alavanca dos notebooks 00, 02 e 03, e correção de 3 achados (1.4, 2.1.2, 3.1.1, 3.2.1) que não batiam com os notebooks
> **Status:** Fechado e validado — pronto para servir de insumo à fase de Insights & Priorização

---

## 1. Questão Central do Case

> **Onde está concentrada a perda de rentabilidade e eficiência da Vértice Retail, e qual plano de priorização maximiza o valor recuperável no horizonte de 90 dias?**

Este documento resume o que foi entregue na fase de Diagnóstico: a estrutura da árvore de hipóteses, os resultados dos 18 testes quantitativos (17 no bloco EBIT + 1 no bloco Capital Investido), e o que foi revisado desde o fechamento original de 14/09. Não contém priorização, estimativa de ganho ou plano de ação — isso é propositalmente reservado para a próxima fase (Insights e Priorização).

---

## 2. Estrutura da Árvore de Hipóteses

O ROIC é o nó comum a partir do qual a árvore se ramifica em dois blocos irmãos, de naturezas diferentes: o bloco **EBIT** (100% MECE, 3 raízes, 17 testes) e o bloco **Capital Investido** (1 raiz formal, mas declaradamente não-exaustiva, 1 teste). Notação "17 + 1" usada propositalmente ao longo deste documento para não diluir essa diferença.

| Raiz | Nº de testes | Cobre |
|---|---|---|
| 1. Receita Líquida | 5 | Volume, preço, mix, retenção/RFM, descontos |
| 2. Custos Variáveis | 7 | CMV, fornecedores, frete, prazo de entrega, devolução, ruptura, estoque parado |
| 3. Despesas Operacionais | 5 | CAC, ROAS, custo de atendimento, causas-raiz de suporte, tempo de resposta |
| 4. Capital Investido | 1 | Capital imobilizado em SKUs descontinuados (status cadastral) |

O **bloco EBIT** (Raízes 1–3) é **MECE**: cada real da DRE é contado uma única vez, e as 3 raízes somadas reconstroem 100% do EBIT. A **Raiz 4** é formal (mesmo rigor de validação, entra na priorização de oportunidades), mas **não é coletivamente exaustiva** em relação ao universo de Capital Investido — cobre apenas o subcomponente com dado disponível e testado, não CAPEX, dívida ou outros ativos.

Documento de referência da estrutura: `arvore_ebit_final.md` (pasta `Execução/Árvore/`).

---

## 3. Base de Dados e Premissas Metodológicas

**5 bases tratadas:** `vendas.csv` (27.758 pedidos), `estoque.csv` (5.000 SKUs), `clientes.csv`, `marketing.csv`, `atendimento.csv`.

**Períodos por base** (relevante para interpretar qualquer indicador):
- `vendas.csv`: 01/01/2023 a 26/01/2024
- `atendimento.csv` e `marketing.csv`: 01/01/2023 a 31/12/2025
- `estoque.csv`: fotografia do estado atual, sem série temporal própria

**[PREMISSA] Continuidade de demanda:** como o histórico de vendas termina antes da data de referência do estoque (sem sobreposição limpa entre as duas séries), qualquer cálculo que cruza `vendas.csv` com `estoque.csv` (ruptura, giro, capital por grupo) assume que o padrão de venda observado no histórico ainda é representativo do comportamento atual. Isso vale para os achados de Ruptura e Estoque Parado (Seção 4) e para Capital Investido (Seção 5).

**Cálculos:** feitos via código (pandas/scipy), não por IA generativa, e documentados em notebook — prática exigida pelo mentor e preservada em todas as revisões.

---

## 4. Síntese dos 17 Testes do Bloco EBIT

Status: **Confirmada** (hipótese sustentada pelos dados) · **Refutada** (não sustentada) · **Sazonal** (efeito parcial/condicional) · **Parcialmente Confirmada** (parte da hipótese se sustenta, parte não).

### Raiz 1 — Receita Líquida

| Teste | Status | Achado-chave [FATO] |
|---|---|---|
| 1.1 Quantidade Vendida | Confirmada | Crescimento de receita puxado por efeito volume (97.420 unidades, 3,51 un/pedido); preço médio estável (~R$210,69) |
| 1.2 Erosão de Preço Unitário | Refutada | Preços homogêneos entre categorias (R$209-212), sem desvalorização estrutural |
| 1.3 Mix de Categorias | Refutada | Margens de contribuição homogêneas entre categorias (~54,1%-54,5%) |
| 1.4 Retenção & RFM | Confirmada | Campeões e Fiéis somam 25,8% da base e respondem por 56,0% do LTV total (segmentação RFM); numa lente diferente (Pareto por LTV individual, não por segmento), o Top 20% dos clientes concentra 61,05% do LTV |
| 1.5 Descontos Concedidos | Confirmada | Descontos >20% derrubam MC de 58,2% para 39,5%; 491 pedidos com MC negativa |

### Raiz 2 — Custos Variáveis

| Teste | Status | Achado-chave [FATO] |
|---|---|---|
| 2.1 CMV Unitário | Sazonal | Markup médio 2,48x; CMV sobe de 43,83% para 44,8% da receita líquida na Black Friday |
| 2.1.2 Fornecedores (Curva ABC) | Confirmada | Spread de margem entre fornecedores varia de 50,84% a 56,92%; fornecedores críticos (FORN-058, FORN-060, FORN-087) entregam MC ~3,5 p.p. abaixo da média (50,84%-51,64%) |
| 2.2 Frete por Pedido | Confirmada | Marketplace concentra 57,8% do frete total (R$196,7k), custo médio 5x acima dos canais próprios |
| 2.2.2 Lead Time / SLA | Confirmada | Prazo médio nacional 8,32 dias; Norte/Nordeste acima de 8,5 dias, com mais devolução |
| 2.3.1 Taxa de Devolução | Confirmada | 14,87% de devolução (4.127 pedidos, R$3,06M); 69,6% por causas operacionais evitáveis |
| 2.3.2 Ruptura de Estoque | Confirmada | 800 SKUs (16,0%) abaixo do ponto de pedido — 99 zerados, 701 críticos. Receita bruta em risco: R$3,17M histórico (~R$247k/mês). Margem em risco: R$1,58M histórico (~R$124k/mês) [INFERÊNCIA sob premissa de continuidade de demanda] |
| 2.3.3 Estoque Parado — Efeito em Margem | Refutada | Sem relação estatística entre giro do SKU e desconto concedido (correlação ≈0,03; giro baixo desconta 7,66% vs. 8,01% do restante) |

### Raiz 3 — Despesas Operacionais

| Teste | Status | Achado-chave [FATO] |
|---|---|---|
| 3.1.1 CAC & Conversões | Confirmada | TikTok Ads e Influenciadores têm o menor CAC ponderado (R$1,75 e R$1,76, respectivamente — praticamente empatados); Influenciadores tem o maior ticket médio (R$912,40, 38% acima da média) e maior margem de contribuição por pedido |
| 3.1.2 ROAS & Atribuição | Confirmada | Influenciadores com ROAS 7,75x, consistente entre modelos de atribuição |
| 3.2.1 Custo por Chamado | Confirmada | Reclame Aqui custa R$45/chamado (22,5x o ChatBot, R$2); WhatsApp e E-mail somam 60,8% do custo total de atendimento |
| 3.2.2 Falhas CX & Sentimento | Confirmada | WISMO ("onde está meu pedido?") é 30,04% dos tickets (10.765 chamados); Defeito tem o pior CSAT (2,82) |
| **3.2.3 Tempo de Resposta & CSAT** *(status corrigido nesta rodada)* | **Parcialmente Confirmada** | **Sem correlação** entre tempo de resposta e CSAT (Pearson r=0,015; Spearman não significativo, p=0,159). São dois achados independentes: (a) tempo de resposta alto em canais assíncronos — E-mail 269,6 min, Reclame Aqui 778,3 min de média, 21,6% dos tickets >4h; (b) CSAT baixo em geral (médio 3,24), explicado por `categoria_problema` (2,82 Defeito a 4,57 Elogio), não por canal ou velocidade |

**Nota sobre a correção do Teste 3.2.3:** a versão anterior deste resumo afirmava uma correlação direta (resposta <15min → CSAT 4,42; >4h → CSAT 2,10; reabertura 28,7%) que **não é reproduzível no notebook oficial** — o cálculo real (`sla_summary` no notebook `03_arvore_hipoteses_raiz_3_despesas_operacionais.ipynb`) mostra CSAT oscilando apenas entre 3,20 e 3,30 em todas as 6 faixas de SLA. O erro estava na narrativa deste resumo, não no cálculo em si; o notebook foi complementado com uma célula de checagem formal de correlação (Pearson/Spearman) para deixar isso auditável, e a conclusão executiva do teste foi reescrita.

---

## 5. Raiz 4 — Capital Investido (Estoque Imobilizado)

Diferente da rodada anterior, este não é mais um "achado satélite" fora do rigor de validação — é uma raiz formal da árvore (`arvore_ebit_final.md`, Seção 3), com o mesmo padrão de auditoria dos demais testes, ainda que declaradamente não-exaustiva em relação ao universo de Capital Investido (cobre só o subcomponente com dado disponível: estoque imobilizado).

**Definição de população (importante):** este teste usa `status_disponibilidade == "Descontinuado"` (207 SKUs) — um critério de status cadastral, **não** o quartil de menor giro. Isso substitui o número informal citado em versões anteriores deste resumo para "SKUs de giro baixo" (R$ 116,8 milhões / 36,2% do capital) — essa cifra usava uma população mais ampla e nunca foi auditada com o rigor exigido agora; não deve ser reutilizada. O achado oficial da Raiz 4 é exclusivamente sobre a população "Descontinuado", auditada no notebook próprio `04_arvore_hipoteses_raiz_4_capital_investido.ipynb`.

### Teste 4.1 · Capital Parado em SKUs Descontinuados — Status: Confirmada

- **[FATO]** Capital total imobilizado no catálogo (5.000 SKUs, a custo de aquisição): **R$ 348.701.550,87**
- **[FATO]** SKUs com status "Descontinuado": **207** (4,1% do catálogo em número de SKUs)
- **[FATO]** Capital imobilizado nesses 207 SKUs: **R$ 17.714.096,89** (5,1% do capital total) — sobre-representação de ~1,2x (modesta, não dramática; o achado relevante é o valor absoluto parado em itens sem linha ativa)
- **[FATO]** Distribuição por categoria: Moda 66 SKUs / R$ 8.368.306,83 · Beleza 67 / R$ 4.362.802,86 · Lifestyle 38 / R$ 2.535.348,48 · Acessórios 36 / R$ 2.447.638,72
- **[FATO]** Markup médio desses SKUs (custo → preço de venda sugerido): **2,35x** — liquidação não seria venda abaixo do custo
- **[FATO]** Checagem de reposição: mediana de dias desde a última entrada de estoque não difere estatisticamente entre descontinuados (533 dias) e ativos (560 dias) — teste de Mann-Whitney, p=0,25
- **[INFERÊNCIA]** A ausência de diferença estatística na reposição sugere que "Descontinuado" reflete uma decisão/status comercial, não o resultado observável de abandono operacional gradual — a base não permite datar quando a decisão foi tomada

**Não há dupla contagem com o Teste 2.3.3** (Estoque Parado — Efeito em Margem, Raiz 2): as populações têm critérios de seleção distintos (status "Descontinuado" vs. quartil de giro) e podem se sobrepor apenas parcialmente. Onde se sobrepõem, a distinção de lente segue válida — fluxo de margem cedida no período (2.3.3, efeito de DRE) vs. estoque de capital imobilizado num instante (4.1, efeito de balanço).

**Fora de escopo deste teste (propositalmente):** estimativa de ganho financeiro de liquidação, prazo de monetização ou plano de ação — isso pertence à fase de Insights e Priorização / Business Case.

---

## 6. O Que Mudou Desde o Fechamento de 14/09/2026

**Rodada de 14/09/2026 (fechamento original):**
1. **Split do antigo Teste 2.3.2** ("Ruptura e Giro de Estoque") em dois testes distintos + 1 satélite.
2. **Simplificação do diagnóstico:** removidos business case, roadmap 30-60-90, seção de alavancas, waterfall de EBITDA e todo valor de ganho/recuperação financeira estimada. O diagnóstico passou a conter somente análises — sem priorização ou ganho.
3. **Datas adicionadas** a todos os indicadores principais, refletindo o período real de cada base de origem.

**Rodada atual:**
4. **Teste 3.2.3 corrigido de "Confirmada" para "Parcialmente Confirmada".** A correlação direta entre tempo de resposta e CSAT afirmada na versão anterior deste resumo não é reproduzível no notebook oficial. Recalculado com checagem formal de correlação (Pearson/Spearman): sem relação estatística. Reformulado como dois achados independentes (tempo de resposta alto em canais críticos; CSAT baixo explicado por categoria de problema). Notebook `03_arvore_hipoteses_raiz_3_despesas_operacionais.ipynb` atualizado com célula de correlação e conclusão executiva revisada.
5. **Capital Investido formalizado como Raiz 4** (`arvore_ebit_final.md`), com o Teste 4.1 recebendo, pela primeira vez, notebook próprio e o mesmo rigor de validação dos demais 17 testes. População redefinida de "giro baixo" (informal, nunca auditada) para "status Descontinuado" (207 SKUs, auditado) — o número antigo de R$116,8M/36,2% não é mais citável como achado oficial. Novo notebook: `04_arvore_hipoteses_raiz_4_capital_investido.ipynb`.
6. **Notebook `02_arvore_hipoteses_raiz_2_custos_variaveis.ipynb` revisado.** O achado satélite de Capital Investido (população "giro baixo", R$116,8M/36,2%) foi marcado explicitamente como **superado** dentro do próprio notebook — mantido intacto para rastreabilidade histórica, mas com nota apontando para o Teste 4.1/notebook 04 como fonte oficial. A antiga "Seção 4 · Síntese Integrada & Recomendações Estratégicas (30-60-90 Dias)" — matriz com coluna de impacto financeiro e roadmap tático — foi **removida** por ser conteúdo de Business Case, incompatível com o escopo de Diagnóstico.
7. **Notebook `00_arvore_hipoteses_consolidada_master.ipynb` revisado.** A seção de "Reconciliação do EBIT com Alavancas e Roadmap" (três cenários de mídia com ganho estimado, EBIT otimizado, gráfico waterfall de captura de valor) foi **removida** — ficou só a reconciliação histórica real (Receita Líquida → EBIT Base), sem nenhuma projeção. A Matriz de Cobertura Final foi reescrita: coluna "Alavanca Acionável" removida, Testes 2.3.2/2.3.3 separados com os números corretos (antes apareciam fundidos), 3.2.3 corrigido para "Parcialmente Confirmada", e a Raiz 4/Teste 4.1 adicionada. A "Decomposição Contábil da Alavanca 4" e o roadmap 30-60-90 que vinham na sequência também foram removidos. O cálculo de ruptura de estoque (célula 3.1) foi mantido com o corte bruto antigo (787 SKUs/15,7%) ao lado do critério oficial por status cadastral (800/16,0%), com nota explicando a diferença.
8. **Auditoria hipótese-a-hipótese contra os notebooks (esta rodada) encontrou 3 números do resumo que não batiam com o cálculo real, todos corrigidos nesta versão:**
   - **Teste 3.1.1 (CAC):** o resumo citava "TikTok R$1,98 / Influenciadores R$8,12" — números que não existem no notebook 03. O cálculo real mostra TikTok e Influenciadores com CAC ponderado quase empatado (R$1,75 e R$1,76) — ambos entre os menores, não o maior.
   - **Teste 1.4 (RFM):** o resumo juntava dois cortes diferentes como se fossem um só. Campeões+Fiéis (25,8% da base) respondem por 56,0% do LTV — não >60%. O ">60%" (61,05%) é de um corte diferente (Top 20% dos clientes por LTV via Pareto, não por segmento RFM). Os dois números agora aparecem separados e identificados.
   - **Teste 2.1.2 (Fornecedores):** o resumo citava spread de 56,8%-61,0% (Curva A) e <45% (cauda) — sem correspondência no notebook 02. O spread real é 50,84%-56,92%, com os fornecedores críticos em ~50,8%-51,6%.
   - **Teste 3.2.1 (Custo por Ticket):** o "R$18" citado como referência de "Chat" era, na verdade, uma premissa hardcoded do Business Case (removida — ver abaixo), não um cálculo diagnóstico. Substituído pela comparação real do notebook: Reclame Aqui (R$45) vs. ChatBot (R$2), 22,5x.
9. **Notebook `03_arvore_hipoteses_raiz_3_despesas_operacionais.ipynb` revisado (limpeza de Business Case, mesma rodada).** Removidos: a "Faixa de Sensibilidade da Alavanca 3" (cenários de mídia R$187k/268k/350k, testes 3.1.2), o item "Potencial Financeiro com IA" (teste 3.2.1), a "Modelagem Quantitativa/Decomposição Formal da Alavanca 4" (Módulo B de IA, R$177k/163k/340k, teste 3.2.2), e toda a antiga "Síntese Estratégica e Recomendações Executivas (30-60-90 Dias)" com roadmap em Gantt. Substituída por uma Matriz Consolidada só de diagnóstico (Teste/Status/Achado-Chave), sem coluna de impacto financeiro e sem roadmap.

---

## 7. Rastreabilidade — Onde Está Cada Coisa

| Documento | Papel | Pasta |
|---|---|---|
| `arvore_ebit_final.md` | Estrutura oficial da árvore de hipóteses (18 testes: 17 EBIT + 1 Capital Investido) | `Execução/Árvore/` |
| `relatorio_executivo_diretoria.html` | Diagnóstico executivo (somente análises, 17 testes, 16 gráficos) — **não revisado nesta rodada, pendente de atualização** | `Execução/Diagnóstico/` |
| `auditoria_de_dados.html` | Laudo de auditoria e conciliação dos dados — **não revisado nesta rodada** | `Execução/Diagnóstico/` |
| `00_arvore_hipoteses_consolidada_master.ipynb` | Consolidação e matriz de cobertura final — **atualizado nesta rodada**: seção de alavancas/waterfall/EBIT otimizado removida (Business Case), Matriz de Cobertura reescrita sem coluna de alavanca, com 2.3.2/2.3.3 separados e Raiz 4 incluída | `Execução/Diagnóstico/Notebooks/` |
| `02_arvore_hipoteses_raiz_2_custos_variaveis.ipynb` | Cálculo da Raiz 2 — **atualizado nesta rodada**: achado satélite de Capital Investido marcado como superado (mantido intacto por rastreabilidade), Seção 4 de roadmap/impacto financeiro removida | `Execução/Diagnóstico/Notebooks/` |
| `03_arvore_hipoteses_raiz_3_despesas_operacionais.ipynb` | Cálculo da Raiz 3 — **atualizado nesta rodada**: checagem formal de correlação do Teste 3.2.3, e limpeza de todo conteúdo de Business Case (alavancas 3 e 4, roadmap 30-60-90) | `Execução/Diagnóstico/Notebooks/` |
| `04_arvore_hipoteses_raiz_4_capital_investido.ipynb` | Cálculo do Teste 4.1 (Raiz 4) — **novo nesta rodada**, primeira vez com notebook e rigor próprios | `Execução/Diagnóstico/Notebooks/` |
| `Dados_Tratados/` | As 5 bases tratadas (vendas, estoque, clientes, marketing, atendimento) | `Execução/Diagnóstico/Dados_Tratados/` |

---

## 8. Fora de Escopo Nesta Fase (propositalmente)

O diagnóstico **não** contém: priorização de oportunidades, estimativa de ganho financeiro, plano de ação (30-60-90 dias), protótipo de IA, ou recomendação de qual alavanca perseguir primeiro. Isso vale igualmente para o novo Teste 4.1 (Raiz 4). Está reservado à próxima fase — **Insights e Priorização** — que ainda não existe e usará este documento e os arquivos da Seção 7 como insumo direto.
