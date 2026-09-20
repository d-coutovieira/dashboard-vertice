# Vértice Retail — Dashboard Executivo & Inteligência Estratégica
**EloGroup Strategic Intelligence · Retail & Consumer Goods Practice**

Sistema integrado de inteligência analítica, reconciliação financeira (DRE) e gerador de relatórios executivos determinísticos com suporte a IA generativa (Módulo D).

---

## 👥 Equipe & Contribuidores
Projeto desenvolvido para entrega executiva do Bootcamp:
* **Daniel Couto Vieira**
* **Carlos Estevão Araújo**
* **Bruno da Mata Barbosa Macedo**

---

## 🚀 Como Executar em 2 Minutos

### Opção 1: Inicialização Automática (Windows)
Basta dar um **duplo clique** no arquivo executável:
```text
run_dashboard.bat
```
Ele instalará as bibliotecas necessárias silenciosamente e iniciará o servidor na porta `8088`.

### Opção 2: Via Terminal (PowerShell ou Bash)
1. Instale as dependências:
```powershell
pip install -r requirements.txt
```

2. Inicie o servidor:
```powershell
python dashboard_server.py
```

3. Abra o navegador e acesse:
👉 **[http://localhost:8088/](http://localhost:8088/)**

---

## 🏛️ Funcionalidades do Dashboard SPA

1. **Visão Geral & DRE Conciliada:** Formação da lucratividade desde o faturamento bruto (R$ 20,53M) até a margem pós-atrito operacional e custo de estoque WACC.
2. **Sistemas Operacionais:**
   - **Vendas & Canais:** Descontos comerciais e dinâmica de marketplace.
   - **Estoque & Capital:** Desova dos 207 SKUs descontinuados (R$ 17,71M) e alívio de R$ 3,19M/ano em juros WACC (18%).
   - **Atendimento (SAC):** Atrito logístico WISMO (27,24% dos tickets) e deflexão com IA.
   - **Marketing & Aquisição:** Análise de ROAS por canal e dispersão de CAC.
   - **Clientes (RFM):** Curva de Pareto (top 20% concentra 61,05% do faturamento LTV).
3. **Relatórios Executivos com IA (Módulo D):** Síntese em 4 camadas com exportação direta para **PDF A4** e **Markdown**.

---

## 📋 Relatórios Executivos (Módulo D)

O gerador opera com uma **arquitetura determinística em 4 camadas** que garante **zero alucinação** e 100% de conciliação com os dados contábeis:
* **Camada 1 (Ingestão & Slicing):** Ingestão com filtros temporais por semana ISO ou consolidado.
* **Camada 2 (Motor Analítico):** Cálculo de variações WoW, decomposição preço-volume e detecção de anomalias.
* **Camada 3 (Síntese Narrativa):** Geração determinística de manchetes, fatos auditados e mandatos C-Level.
* **Camada 4 (Apresentação Multi-formato):** Renderização HTML com CSS de alta fidelidade para PDF A4 e Markdown.

### Enriquecimento Opcional com IA (LLM)
O sistema funciona **100% offline**. Se desejar refinamento textual adicional:
* **Na interface:** Ative o botão *"Enriquecer com IA (LLM)"* e informe sua chave de API (DeepSeek, OpenAI ou Google Gemini).
* **Por variável de ambiente:**
```powershell
# Exemplo PowerShell:
$env:DEEPSEEK_API_KEY="sua_chave_aqui"
python dashboard_server.py
```

### Exportação para PDF / Impressão
Na visualização do relatório, clique em **🖨️ Imprimir / Salvar PDF**. O sistema aplica formatação dedicada `@media print` calibrada para folha **A4**, com contraste nítido, quebras de página controladas e layout executivo de consultoria.

---

## 📄 Geração em Lote via Linha de Comando (CLI)
Você também pode exportar relatórios em lote sem abrir o navegador:

```powershell
# Gerar suíte completa para a Black Friday (Semana 47)
python generate_weekly_report.py --week 2023-W47 --sector full_suite

# Gerar o relatório consolidado de todos os 13 meses
python generate_weekly_report.py --week consolidated --sector all
```
Os arquivos gerados (.html, .md e .json) são gravados automaticamente na pasta `reports/`.

---

## 🧪 Testes Automatizados de Validação
O projeto inclui suíte completa de testes automatizados com PyTest:

```powershell
python -m pytest test_dashboard_server.py test_diagnostic_consistency.py test_weekly_generator.py -v
```
*(37 testes automatizados com 100% de aprovação)*.
