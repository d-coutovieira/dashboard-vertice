/**
 * diagnostics.js - Renders action-oriented diagnostic cards, ICE levers, and audit data tables.
 */

window.DiagnosticsManager = {
  init() {
    this.renderDreTable('13m');
    this.renderChannelsTable();
    this.renderMarketingTable();
    this.renderRfmTable();
    this.renderAiKpisTable();
  },

  renderDreTable(period = '13m') {
    const tbody = document.getElementById('tbody-dre');
    if (!tbody || !window.dashboardData || !window.dashboardData.dre) return;

    const items = window.dashboardData.dre.waterfall_items || [];
    tbody.innerHTML = items.map(row => {
      const isSubtotal = row.type === 'subtotal' || row.type === 'final_margin' || row.type === 'positive';
      const isNegative = row.type === 'negative' || row.type === 'subtotal_loss' || row.type === 'opportunity_cost';

      const val13m = (row.period_13m < 0 ? `- R$ ${Math.abs(row.period_13m).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : `R$ ${row.period_13m.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`);
      const val12m = (row.annualized_12m < 0 ? `- R$ ${Math.abs(row.annualized_12m).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : `R$ ${row.annualized_12m.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`);

      let colorClass = isSubtotal ? 'color:var(--accent-lime); font-weight:700;' : (isNegative ? 'color:var(--color-danger);' : '');
      let rowBg = row.type === 'final_margin' ? 'background:rgba(163, 230, 53, 0.08); font-weight:800;' : '';

      return `
        <tr style="${rowBg}">
          <td style="${isSubtotal ? 'font-weight:700;' : ''}">${row.name}</td>
          <td class="text-right" style="${colorClass}">${val13m}</td>
          <td class="text-right" style="${colorClass}">${val12m}</td>
          <td class="text-center" style="${colorClass}">${row.share_pct.toFixed(2)}%</td>
          <td style="color:var(--text-secondary); font-size:0.76rem;">${row.diagnosis}</td>
        </tr>
      `;
    }).join('');
  },

  channelPalette: {
    'Influenciador': '#a3e635',
    'Google Ads': '#3b82f6',
    'Instagram Ads': '#ec4899',
    'Marketplace': '#f59e0b',
    'Orgânico': '#10b981',
    'TikTok Ads': '#8b5cf6',
    'Email Marketing': '#06b6d4'
  },

  renderChannelsTable() {
    const tbody = document.getElementById('tbody-channels');
    if (!tbody || !window.dashboardData) return;

    const channels = window.dashboardData.channels || [];
    tbody.innerHTML = channels.map(c => {
      const dotColor = this.channelPalette[c.canal] || '#94a3b8';
      return `
      <tr>
        <td style="font-weight:600;"><span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:${dotColor}; margin-right:8px; vertical-align:middle;"></span>${c.canal}</td>
        <td class="text-right">${c.pedidos.toLocaleString('pt-BR')}</td>
        <td class="text-right">R$ ${c.receita_bruta.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
        <td class="text-right">R$ ${c.ticket_medio.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
        <td class="text-center" style="${c.frete_pct > 3.0 ? 'color:var(--color-danger); font-weight:700;' : ''}">${c.frete_pct.toFixed(2)}%</td>
        <td class="text-center">${c.taxa_devolucao_pct.toFixed(2)}%</td>
        <td class="text-center" style="color:var(--accent-lime); font-weight:700;">${c.margem_pct.toFixed(2)}%</td>
        <td style="font-size:0.75rem; color:var(--text-secondary);"><span class="kpi-badge ${c.frete_pct > 3 ? 'danger' : 'accent'}">${c.tier}</span> ${c.strategy}</td>
      </tr>
    `}).join('');
  },

  renderMarketingTable() {
    const tbody = document.getElementById('tbody-marketing');
    if (!tbody || !window.dashboardData) return;

    const channels = window.dashboardData.channels || [];
    tbody.innerHTML = channels.map(c => {
      const dotColor = this.channelPalette[c.canal] || '#94a3b8';
      return `
      <tr>
        <td style="font-weight:700;"><span style="display:inline-block; width:9px; height:9px; border-radius:50%; background:${dotColor}; margin-right:8px; vertical-align:middle;"></span>${c.canal}</td>
        <td><span class="kpi-badge ${c.roas >= 4.5 ? 'success' : (c.roas < 3.2 ? 'danger' : 'warning')}">${c.tier}</span></td>
        <td class="text-right">R$ ${c.investimento.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
        <td class="text-right">R$ ${c.receita_gerada.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
        <td class="text-center" style="font-weight:800; color:${c.roas >= 4.5 ? 'var(--accent-lime)' : 'var(--text-primary)'};">${c.roas.toFixed(2)}x</td>
        <td class="text-center">R$ ${c.cac_medio.toFixed(2)}</td>
        <td style="font-size:0.76rem; color:var(--text-secondary);">${c.strategy}</td>
      </tr>
    `}).join('');
  },

  renderRfmTable() {
    const tbody = document.getElementById('tbody-rfm');
    if (!tbody || !window.dashboardData) return;

    const segments = window.dashboardData.customers_rfm?.segments || [];
    tbody.innerHTML = segments.map(s => `
      <tr>
        <td style="font-weight:700; color:${s.color};">● ${s.segmento_rfm}</td>
        <td class="text-right">${s.clientes.toLocaleString('pt-BR')}</td>
        <td class="text-right">${s.pct_base.toFixed(1)}%</td>
        <td class="text-right">R$ ${s.ltv_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (${s.pct_ltv.toFixed(1)}%)</td>
        <td class="text-center" style="${s.pct_desconto > 10 ? 'color:var(--color-danger); font-weight:700;' : ''}">${s.pct_desconto.toFixed(2)}%</td>
        <td class="text-center">${(s.taxa_devolucao || 0).toFixed(2)}%</td>
        <td style="font-size:0.75rem; color:var(--text-secondary);"><strong>Ação:</strong> ${s.action}</td>
      </tr>
    `).join('');
  },

  renderAiKpisTable() {
    const tbody = document.getElementById('tbody-ai-kpis');
    if (!tbody || !window.dashboardData) return;

    const kpis = window.dashboardData.customer_service?.ai_productivity_kpis || [];
    tbody.innerHTML = kpis.map(k => `
      <tr>
        <td style="font-weight:700; color:var(--accent-lime);">${k.kpi}</td>
        <td class="text-center"><span class="kpi-badge accent" style="font-size:0.8rem; font-weight:800;">${k.estimated_value}</span></td>
        <td style="font-family:'Consolas', monospace; font-size:0.76rem; color:var(--accent-cyan);">${k.formula}</td>
        <td style="font-size:0.76rem; color:var(--text-secondary);">${k.premise}</td>
        <td class="text-center"><span class="kpi-badge success">${k.status}</span></td>
      </tr>
    `).join('');
  }
};
