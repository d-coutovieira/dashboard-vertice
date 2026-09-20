/**
 * kpi-cards.js - Component for formatting and managing executive KPI cards
 */

window.KpiManager = {
  currentPeriod: '13m',

  formatCurrency(value, inMillions = false) {
    if (value === undefined || value === null) return 'R$ 0,00';
    if (inMillions) {
      const millions = value / 1_000_000.0;
      return `R$ ${millions.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}M`;
    }
    return `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  },

  formatPercent(value) {
    if (value === undefined || value === null) return '0,00%';
    return `${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
  },

  init() {
    // Bind all cards with trace triggers
    document.querySelectorAll('.kpi-card[data-kpi]').forEach(card => {
      const kpiId = card.getAttribute('data-kpi');
      const btn = card.querySelector('.btn-trace-modal');
      if (btn) {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (window.DrillDownManager) {
            window.DrillDownManager.open(kpiId);
          }
        });
      }
      card.addEventListener('click', () => {
        if (window.DrillDownManager) {
          window.DrillDownManager.open(kpiId);
        }
      });
    });

    // Listen for period change
    const periodSelector = document.getElementById('period-selector');
    if (periodSelector) {
      periodSelector.addEventListener('change', (e) => {
        this.currentPeriod = e.target.value;
        this.updateTopKpis();
        if (window.DiagnosticsManager) {
          window.DiagnosticsManager.renderDreTable(this.currentPeriod);
        }
      });
    }
  },

  updateTopKpis() {
    if (!window.dashboardData || !window.dashboardData.dre) return;
    const dre = window.dashboardData.dre;
    const summary = dre.summary;

    const elGross = document.getElementById('kpi-gross-rev');
    const elContrib = document.getElementById('kpi-contrib-margin');
    const elDrain = document.getElementById('kpi-drain');
    const elPostFriction = document.getElementById('kpi-post-friction');

    const is12m = (this.currentPeriod === '12m');
    const factor = is12m ? (12.0 / 13.0) : 1.0;

    if (elGross) {
      elGross.textContent = this.formatCurrency(summary.gross_revenue * factor, true);
    }
    if (elContrib) {
      elContrib.textContent = this.formatCurrency(summary.contribution_margin * factor, true);
    }
    if (elDrain) {
      const drainVal = (summary.returns_drain || 1210000.0) * factor;
      elDrain.textContent = `R$ ${(drainVal / 1000).toFixed(1)}k`;
    }
    if (elPostFriction) {
      elPostFriction.textContent = this.formatCurrency(summary.post_friction_margin * factor, true);
    }
  }
};
