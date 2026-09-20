/**
 * stock-alerts.js - Compact Tactical Stock Alerts Manager for EloGroup Executive Dashboard
 * Manages:
 * 1. Discontinued SKUs summary & top immobilized list
 * 2. Critical Shelf Life table (10-20 days actionable window with traceable formula)
 * 3. Rupture Risk table (coverage < lead time ordered by criticality)
 */

window.StockAlertsManager = {
  activeTab: 'shelflife',
  isCollapsed: false,

  init() {
    this.bindEvents();
    this.render();
  },

  bindEvents() {
    // Collapse / Expand toggle
    const btnToggle = document.getElementById('btn-toggle-stock-alerts');
    const content = document.getElementById('stock-alerts-collapsible-content');
    if (btnToggle && content) {
      btnToggle.addEventListener('click', () => {
        this.isCollapsed = !this.isCollapsed;
        content.style.display = this.isCollapsed ? 'none' : 'block';
        const icon = btnToggle.querySelector('.toggle-icon');
        const text = btnToggle.querySelector('.toggle-text');
        if (icon) icon.textContent = this.isCollapsed ? '▸' : '▾';
        if (text) text.textContent = this.isCollapsed ? 'Expandir Detalhes' : 'Recolher';
      });
    }

    // Tab buttons
    const tabBtns = document.querySelectorAll('.btn-stock-alert-tab');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeTab = btn.getAttribute('data-tab');
        this.renderActiveTab();
      });
    });
  },

  render() {
    const inv = window.dashboardData?.inventory;
    if (!inv) return;

    // Render 3 Metric Summary Cards
    const elDiscVal = document.getElementById('stat-alert-disc-val');
    const elDiscSub = document.getElementById('stat-alert-disc-sub');
    if (elDiscVal && elDiscSub) {
      elDiscVal.textContent = `${inv.discontinued_skus || 207} SKUs`;
      elDiscSub.textContent = `R$ ${((inv.discontinued_capital || 0) / 1e6).toFixed(2)}M imobilizado (${(inv.discontinued_units || 0).toLocaleString('pt-BR')} peças)`;
    }

    const elShelfVal = document.getElementById('stat-alert-shelf-val');
    const elShelfSub = document.getElementById('stat-alert-shelf-sub');
    const shelfData = inv.shelf_life_actionable_window;
    if (elShelfVal && elShelfSub && shelfData) {
      elShelfVal.textContent = `${shelfData.total_skus_in_window || 0} SKUs`;
      elShelfSub.textContent = `Janela acionável 10 a 20 dias até vencimento`;
    }

    const elRuptureVal = document.getElementById('stat-alert-rupture-val');
    const elRuptureSub = document.getElementById('stat-alert-rupture-sub');
    const ruptureData = inv.rupture_risk;
    if (elRuptureVal && elRuptureSub && ruptureData) {
      elRuptureVal.textContent = `${ruptureData.total_skus_at_risk || 0} SKUs`;
      elRuptureSub.textContent = `Cobertura menor que lead time de entrega`;
    }

    this.renderActiveTab();
  },

  renderActiveTab() {
    const inv = window.dashboardData?.inventory;
    if (!inv) return;

    const secShelf = document.getElementById('alert-tab-shelflife');
    const secRupture = document.getElementById('alert-tab-rupture');
    const secDisc = document.getElementById('alert-tab-discontinued');

    if (secShelf) secShelf.style.display = this.activeTab === 'shelflife' ? 'block' : 'none';
    if (secRupture) secRupture.style.display = this.activeTab === 'rupture' ? 'block' : 'none';
    if (secDisc) secDisc.style.display = this.activeTab === 'discontinued' ? 'block' : 'none';

    if (this.activeTab === 'shelflife') {
      this.renderShelfLifeTable(inv.shelf_life_actionable_window?.items || []);
    } else if (this.activeTab === 'rupture') {
      this.renderRuptureTable(inv.rupture_risk?.items || []);
    } else if (this.activeTab === 'discontinued') {
      this.renderDiscontinuedTable(inv.discontinued_detail || []);
    }
  },

  renderShelfLifeTable(items) {
    const tbody = document.getElementById('tbody-stock-shelflife');
    if (!tbody) return;

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:20px; color:var(--text-muted);">Nenhum SKU na janela de 10 a 20 dias.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => {
      const badgeClass = item.action_tag === 'urgent' ? 'badge-alert-urgent' :
                         item.action_tag === 'warning' ? 'badge-alert-warning' : 'badge-alert-caution';
      return `
        <tr>
          <td style="font-family:'Consolas', monospace; font-size:0.75rem; color:var(--accent-cyan); font-weight:600;">${item.sku_id}</td>
          <td style="font-weight:600; color:var(--text-primary);">${item.nome_produto}</td>
          <td style="color:var(--text-secondary); font-size:0.75rem;">${item.categoria}</td>
          <td class="text-right">${item.quantidade.toLocaleString('pt-BR')} un</td>
          <td class="text-center">
            <span class="stock-badge-pill ${item.dias_ate_vencer <= 13 ? 'danger' : 'warning'}">${item.dias_ate_vencer} dias</span>
          </td>
          <td class="text-right">R$ ${item.custo_unitario.toFixed(2)}</td>
          <td>
            <span class="stock-action-badge ${badgeClass}">${item.acao_sugerida}</span>
          </td>
        </tr>
      `;
    }).join('');
  },

  renderRuptureTable(items) {
    const tbody = document.getElementById('tbody-stock-rupture');
    if (!tbody) return;

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding:20px; color:var(--text-muted);">Nenhum SKU com risco de ruptura iminente.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => {
      const isDanger = item.criticidade_tag === 'danger';
      return `
        <tr>
          <td style="font-family:'Consolas', monospace; font-size:0.75rem; color:var(--accent-cyan); font-weight:600;">${item.sku_id}</td>
          <td style="font-weight:600; color:var(--text-primary);">${item.nome_produto}</td>
          <td style="color:var(--text-secondary); font-size:0.75rem;">${item.categoria}</td>
          <td class="text-right" style="font-weight:700; ${isDanger ? 'color:var(--color-danger);' : ''}">${item.estoque_disponivel} un</td>
          <td class="text-center">
            <span class="stock-badge-pill ${isDanger ? 'danger' : 'warning'}">${item.cobertura_dias.toFixed(1)} dias</span>
          </td>
          <td class="text-center">${item.lead_time_reposicao} dias</td>
          <td class="text-right" style="color:var(--text-muted); font-size:0.75rem;">${item.ponto_pedido} un</td>
          <td>
            <span class="stock-action-badge ${isDanger ? 'badge-alert-urgent' : 'badge-alert-warning'}">${item.criticidade}</span>
          </td>
        </tr>
      `;
    }).join('');
  },

  renderDiscontinuedTable(items) {
    const tbody = document.getElementById('tbody-stock-discontinued');
    if (!tbody) return;

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:20px; color:var(--text-muted);">Nenhum SKU descontinuado com estoque disponível.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => `
      <tr>
        <td style="font-family:'Consolas', monospace; font-size:0.75rem; color:var(--accent-cyan); font-weight:600;">${item.sku_id}</td>
        <td style="font-weight:600; color:var(--text-primary);">${item.nome_produto}</td>
        <td style="color:var(--text-secondary); font-size:0.75rem;">${item.categoria}</td>
        <td class="text-right">${item.estoque_fisico.toLocaleString('pt-BR')} un</td>
        <td class="text-right">R$ ${item.custo_unitario.toFixed(2)}</td>
        <td class="text-right" style="font-weight:700; color:var(--accent-lime);">R$ ${item.custo_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
        <td class="text-right" style="color:var(--text-muted);">R$ ${item.preco_venda_sugerido.toFixed(2)}</td>
      </tr>
    `).join('');
  }
};
