/**
 * drill-down.js - Auditability and Traceability Modal Component
 * Displays formulas, SQL equivalents, underlying datasets, columns, and business premises.
 */

window.DrillDownManager = {
  currentKpiId: null,
  activeTab: 'formula',

  init() {
    const modal = document.getElementById('drill-down-modal');
    const closeBtn = document.getElementById('btn-close-modal');
    const tabFormula = document.getElementById('modal-tab-formula');
    const tabData = document.getElementById('modal-tab-data');
    const btnOpenAudit = document.getElementById('btn-open-audit');

    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.close();
      });
    }

    if (tabFormula) {
      tabFormula.addEventListener('click', () => {
        this.activeTab = 'formula';
        tabFormula.classList.add('active');
        if (tabData) tabData.classList.remove('active');
        this.renderContent();
      });
    }

    if (tabData) {
      tabData.addEventListener('click', () => {
        this.activeTab = 'data';
        tabData.classList.add('active');
        if (tabFormula) tabFormula.classList.remove('active');
        this.renderContent();
      });
    }

    if (btnOpenAudit) {
      btnOpenAudit.addEventListener('click', () => {
        this.open('gross_revenue');
      });
    }

    // Escape key to close modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.close();
    });
  },

  open(kpiId) {
    this.currentKpiId = kpiId || 'gross_revenue';
    const modal = document.getElementById('drill-down-modal');
    if (!modal) return;

    this.renderContent();
    modal.classList.add('active');
  },

  close() {
    const modal = document.getElementById('drill-down-modal');
    if (modal) modal.classList.remove('active');
  },

  renderContent() {
    const content = document.getElementById('modal-content');
    const title = document.getElementById('modal-kpi-title');
    if (!content || !window.dashboardData) return;

    const traceMap = window.dashboardData.traceability || {};
    const meta = traceMap[this.currentKpiId] || {
      title: 'Auditoria Geral da Metodologia',
      formula: 'Conciliação Contábil Gerencial Integrada',
      sql_equivalent: 'SELECT * FROM transacoes_auditadas',
      datasets: ['vendas.csv', 'estoque.csv', 'atendimento.csv', 'marketing.csv', 'clientes.csv'],
      columns: ['receita_bruta', 'margem_contribuicao', 'devolvido', 'custo_frete'],
      temporal_grain: 'Janeiro/2023 a Janeiro/2024 (13 meses auditados)',
      premises: 'Metodologia estrita baseada nas hipóteses empíricas de arvore_ebit.md e no relatório executivo do Case Vértice Retail.',
      benchmark: 'Padrão EloGroup de Auditoria e Analytics'
    };

    if (title) {
      title.textContent = `Auditoria & Rastreabilidade: ${meta.title}`;
    }

    if (this.activeTab === 'formula') {
      content.innerHTML = `
        <div>
          <div class="modal-section-title">Fórmula Algorítmica de Cálculo</div>
          <div class="code-snippet">${meta.formula}</div>
        </div>

        <div>
          <div class="modal-section-title">Consulta SQL Equivalente</div>
          <div class="code-snippet">${meta.sql_equivalent}</div>
        </div>

        <div>
          <div class="modal-section-title">Premissas de Negócio & Racional Contábil</div>
          <p style="color:var(--text-secondary);">${meta.premises}</p>
        </div>

        <div style="background:var(--bg-sidebar); padding:12px; border-radius:var(--radius-md); border-left:3px solid var(--accent-lime);">
          <div style="font-size:0.75rem; color:var(--accent-lime); font-weight:700;">BENCHMARK / REFERÊNCIA</div>
          <div style="font-size:0.82rem; color:var(--text-primary); margin-top:2px;">${meta.benchmark || 'Padrão Setorial de Varejo de Moda e Lifestyle'}</div>
        </div>
      `;
    } else {
      const datasetsTags = (meta.datasets || []).map(d => `<span class="data-tag">📁 ${d}</span>`).join(' ');
      const columnsTags = (meta.columns || []).map(c => `<span class="data-tag">🏷️ ${c}</span>`).join(' ');

      content.innerHTML = `
        <div>
          <div class="modal-section-title">Conjuntos de Dados Fonte (Data Lineage)</div>
          <div class="pill-list">${datasetsTags}</div>
        </div>

        <div>
          <div class="modal-section-title">Colunas & Atributos Utilizados</div>
          <div class="pill-list">${columnsTags}</div>
        </div>

        <div>
          <div class="modal-section-title">Granularidade Temporal Auditada</div>
          <p style="color:var(--text-secondary);">${meta.temporal_grain}</p>
        </div>

        <div style="background:var(--bg-sidebar); padding:12px; border-radius:var(--radius-md); border-left:3px solid var(--accent-cyan);">
          <div style="font-size:0.75rem; color:var(--accent-cyan); font-weight:700;">CONFORMIDADE DOS DADOS</div>
          <div style="font-size:0.82rem; color:var(--text-primary); margin-top:2px;">
            Tratamento de nulos via pipeline automatizado (build_dashboard_data.py); verificação cruzada com o relatório executivo oficial.
          </div>
        </div>
      `;
    }
  }
};
