/**
 * app.js - Main Application Orchestrator for EloGroup Executive Dashboard
 */

document.addEventListener('DOMContentLoaded', async () => {
  console.log('[EloGroup Dashboard] Inicializando aplicação...');

  // 1. Carregar dados do JSON gerado
  try {
    const response = await fetch('data/dashboard_data.json');
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    window.dashboardData = await response.json();
    console.log('[EloGroup Dashboard] Dados carregados com sucesso via fetch.');
  } catch (err) {
    console.warn('[EloGroup Dashboard] Falha no fetch (possível abertura local file://). Tentando fallback.', err);
    // Se a tentativa falhar, aguardar script ou usar objeto existente se injetado
    if (!window.dashboardData) {
      console.error('[EloGroup Dashboard] Dados não encontrados.');
    }
  }

  // 2. Inicializar Gerenciadores de Componentes
  if (window.DrillDownManager) window.DrillDownManager.init();
  if (window.KpiManager) window.KpiManager.init();
  if (window.DiagnosticsManager) window.DiagnosticsManager.init();
  if (window.SimulatorsManager) window.SimulatorsManager.init();
  if (window.StockAlertsManager) window.StockAlertsManager.init();
  if (window.ChartsManager) window.ChartsManager.initAll();

  // 3. Gestão de Navegação das 7 Telas
  const navItems = document.querySelectorAll('.nav-item[data-view]');
  const views = document.querySelectorAll('.dashboard-view');
  const pageTitle = document.getElementById('page-title');
  const pageBadge = document.getElementById('page-badge');

  const viewTitles = {
    'visao-geral': { title: 'Visão Geral & DRE Conciliada', badge: 'Estratégico' },
    'vendas-canais': { title: 'Vendas & Dinâmica de Canais', badge: 'Operacional' },
    'marketing-roas': { title: 'Marketing, CAC & Retorno de Mídia', badge: 'Aquisição' },
    'clientes-rfm': { title: 'Comportamento de Clientes & RFM', badge: 'CRM' },
    'sac-atrito': { title: 'Atendimento (SAC) & Produtividade IA', badge: 'Pós-Venda' },
    'estoque-supply': { title: 'Estoque, Giro & Capital de Giro', badge: 'Supply Chain' },
    'relatorios-ia': { title: 'Relatórios Analíticos por IA', badge: 'Módulo D' }
  };

  // Topbar shortcut button to trigger the Relatórios IA view
  const btnTopReport = document.getElementById('btn-open-ai-report');
  if (btnTopReport) {
    btnTopReport.addEventListener('click', () => {
      const targetNav = document.querySelector('.nav-item[data-view="relatorios-ia"]');
      if (targetNav) targetNav.click();
    });
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetView = item.getAttribute('data-view');

      // Atualizar classes ativas no menu
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      // Atualizar exibição das seções
      views.forEach(v => {
        if (v.id === `view-${targetView}`) {
          v.classList.add('active');
        } else {
          v.classList.remove('active');
        }
      });

      // Atualizar título e badge do topo
      if (viewTitles[targetView]) {
        if (pageTitle) pageTitle.innerHTML = `<span>${viewTitles[targetView].title}</span>`;
        if (pageBadge) pageBadge.textContent = viewTitles[targetView].badge;
      }

      // Redimensionar gráficos do ECharts para garantir layout perfeito
      if (window.ChartsManager) {
        window.ChartsManager.resizeActiveView();
      }
    });
  });

  console.log('[EloGroup Dashboard] Dashboard pronto para uso.');
});
