/**
 * charts.js - Apache ECharts Visualizations with EloGroup Executive Palette
 * Handles all 12 charts across the 8 dashboard views.
 */

window.ChartsManager = {
  instances: {},

  theme: {
    backgroundColor: 'transparent',
    textStyle: {
      fontFamily: "'Inter', sans-serif",
      color: '#94a3b8'
    },
    tooltip: {
      backgroundColor: 'rgba(18, 18, 36, 0.95)',
      borderColor: '#27374d',
      borderWidth: 1,
      textStyle: { color: '#f8fafc', fontSize: 12 },
      padding: [8, 12]
    }
  },

  initAll() {
    this.renderDreWaterfall();
    this.renderSalesTemporal();
    this.renderChannelShare();
    this.renderMarketingScatter();
    this.renderMarketingTiers();
    this.renderRfmLtv();
    this.renderRfmBehavior();
    this.renderSacCategories();
    this.renderReturnsCauses();
    this.renderStockCategories();
    this.renderStockStatus();

    window.addEventListener('resize', () => {
      Object.values(this.instances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
          chart.resize();
        }
      });
    });
  },

  resizeActiveView() {
    setTimeout(() => {
      Object.values(this.instances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
          chart.resize();
        }
      });
    }, 50);
  },

  getChart(id) {
    const dom = document.getElementById(id);
    if (!dom) return null;
    if (this.instances[id]) return this.instances[id];
    const chart = echarts.init(dom, null, { renderer: 'canvas' });
    this.instances[id] = chart;
    return chart;
  },

  // 1. DRE Waterfall Chart
  renderDreWaterfall() {
    const chart = this.getChart('chart-dre-waterfall');
    if (!chart || !window.dashboardData) return;

    const categories = [
      'Rec. Bruta',
      'Descontos',
      'Rec. Líquida',
      'CMV',
      'Frete Envio',
      'Margem Bruta',
      'Frete Dev.',
      'Reversa',
      'SAC 2023',
      'Margem Pós-Atrito'
    ];

    // Values in Millions
    // Base, Assist (transparent helper), Value (bar)
    const rawValues = [
      20.53,  // Total
      -1.64,  // Deduct
      18.89,  // Subtotal
      -8.28,  // Deduct
      -0.34,  // Deduct
      10.27,  // Subtotal
      -0.05,  // Deduct
      -0.17,  // Deduct
      -0.18,  // Deduct
      9.87    // Final
    ];

    const assist = [
      0,
      18.89,
      0,
      10.61,
      10.27,
      0,
      10.22,
      10.05,
      9.87,
      0
    ];

    const barData = [
      { value: 20.53, itemStyle: { color: '#a3e635' } },
      { value: 1.64, itemStyle: { color: '#f87171' } },
      { value: 18.89, itemStyle: { color: '#38bdf8' } },
      { value: 8.28, itemStyle: { color: '#f87171' } },
      { value: 0.34, itemStyle: { color: '#f87171' } },
      { value: 10.27, itemStyle: { color: '#4ade80' } },
      { value: 0.05, itemStyle: { color: '#fb923c' } },
      { value: 0.17, itemStyle: { color: '#fb923c' } },
      { value: 0.18, itemStyle: { color: '#fb923c' } },
      { value: 9.87, itemStyle: { color: '#a3e635' } }
    ];

    const option = {
      ...this.theme,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          const tar = params[1];
          return `${tar.name}<br/>Impacto: <strong>R$ ${tar.value.toFixed(2)}M</strong>`;
        }
      },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '12%', containLabel: true },
      xAxis: {
        type: 'category',
        data: categories,
        axisLine: { lineStyle: { color: '#27374d' } },
        axisLabel: { color: '#94a3b8', fontSize: 10, interval: 0, rotate: 18 }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#94a3b8',
          formatter: (v) => `R$ ${v}M`
        },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      series: [
        {
          name: 'Placeholder',
          type: 'bar',
          stack: 'Total',
          itemStyle: { borderColor: 'transparent', color: 'transparent' },
          emphasis: { itemStyle: { borderColor: 'transparent', color: 'transparent' } },
          data: assist
        },
        {
          name: 'Valor',
          type: 'bar',
          stack: 'Total',
          label: {
            show: true,
            position: 'top',
            formatter: (p) => `R$ ${p.value.toFixed(2)}M`,
            color: '#f8fafc',
            fontSize: 10,
            fontWeight: 'bold'
          },
          data: barData
        }
      ]
    };

    chart.setOption(option);
  },


  // 3. Sales Temporal Evolution
  renderSalesTemporal() {
    const chart = this.getChart('chart-sales-temporal');
    if (!chart || !window.dashboardData) return;

    const series = window.dashboardData.temporal_series || [];
    const months = series.map(s => s.mes);
    const revenue = series.map(s => (s.receita_bruta / 1_000_000.0).toFixed(2));
    const marginPct = series.map(s => s.margem_pct);

    const option = {
      ...this.theme,
      tooltip: { trigger: 'axis' },
      legend: { data: ['Receita Bruta (R$ M)', 'Margem (%)'], textStyle: { color: '#94a3b8' } },
      grid: { left: '4%', right: '4%', bottom: '10%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: months,
        axisLine: { lineStyle: { color: '#27374d' } }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Receita (R$ M)',
          axisLabel: { formatter: 'R$ {value}M', color: '#94a3b8' },
          splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
        },
        {
          type: 'value',
          name: 'Margem (%)',
          min: 40,
          max: 60,
          axisLabel: { formatter: '{value}%', color: '#94a3b8' },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Receita Bruta (R$ M)',
          type: 'bar',
          data: revenue,
          itemStyle: { color: '#38bdf8', borderRadius: [4, 4, 0, 0] }
        },
        {
          name: 'Margem (%)',
          type: 'line',
          yAxisIndex: 1,
          data: marginPct,
          smooth: true,
          lineStyle: { color: '#a3e635', width: 3 },
          itemStyle: { color: '#a3e635' }
        }
      ]
    };

    chart.setOption(option);
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

  // 4. Channel Share Donut
  renderChannelShare() {
    const chart = this.getChart('chart-channel-share');
    if (!chart || !window.dashboardData) return;

    const channels = window.dashboardData.channels || [];
    const data = channels.map(c => ({
      name: c.canal,
      value: c.receita_bruta,
      itemStyle: {
        color: this.channelPalette[c.canal] || '#94a3b8'
      }
    }));

    const option = {
      ...this.theme,
      tooltip: {
        trigger: 'item',
        formatter: (p) => `${p.name}: <strong>R$ ${(p.value/1e6).toFixed(2)}M</strong> (${p.percent}%)`
      },
      legend: {
        bottom: '2%',
        left: 'center',
        textStyle: { color: '#94a3b8', fontSize: 11 },
        itemWidth: 10,
        itemHeight: 10
      },
      series: [
        {
          name: 'Canal',
          type: 'pie',
          radius: ['40%', '68%'],
          center: ['50%', '44%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#16213e',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#f8fafc',
              formatter: '{b}\n{d}%',
              lineHeight: 20
            }
          },
          data: data
        }
      ]
    };

    chart.setOption(option);
  },

  // 5. Marketing Scatter (ROAS vs Investimento)
  renderMarketingScatter() {
    const chart = this.getChart('chart-marketing-scatter');
    if (!chart || !window.dashboardData) return;

    const channels = window.dashboardData.channels || [];
    const data = channels.map(c => [
      (c.investimento / 1e6).toFixed(2),
      c.roas.toFixed(2),
      c.canal,
      c.tier
    ]);

    const option = {
      ...this.theme,
      tooltip: {
        formatter: (p) => `<strong>${p.data[2]}</strong> (${p.data[3]})<br/>
                           Investimento: R$ ${p.data[0]}M<br/>
                           ROAS: <strong>${p.data[1]}x</strong>`
      },
      grid: { left: '6%', right: '8%', bottom: '12%', top: '12%', containLabel: true },
      xAxis: {
        name: 'Investimento (R$ Milhões)',
        axisLine: { lineStyle: { color: '#27374d' } },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      yAxis: {
        name: 'ROAS Realizado (x)',
        axisLine: { lineStyle: { color: '#27374d' } },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      series: [
        {
          type: 'scatter',
          symbolSize: 22,
          data: data,
          itemStyle: {
            color: (param) => this.channelPalette[param.data[2]] || '#a3e635',
            shadowBlur: 8,
            shadowColor: 'rgba(0, 0, 0, 0.4)'
          },
          label: {
            show: true,
            formatter: (p) => p.data[2],
            position: 'top',
            distance: 6,
            color: '#f8fafc',
            fontSize: 11,
            fontWeight: '600'
          },
          labelLayout: { hideOverlap: true }
        }
      ]
    };

    chart.setOption(option);
  },

  // 6. Marketing Tiers Bar
  renderMarketingTiers() {
    const chart = this.getChart('chart-marketing-tiers');
    if (!chart || !window.dashboardData) return;

    const channels = window.dashboardData.channels || [];
    const sorted = [...channels].sort((a, b) => a.roas - b.roas);

    const names = sorted.map(c => c.canal);
    const roas = sorted.map(c => c.roas.toFixed(2));

    const option = {
      ...this.theme,
      tooltip: { trigger: 'axis' },
      grid: { left: '4%', right: '12%', bottom: '5%', top: '5%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'ROAS',
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: { lineStyle: { color: '#27374d' } }
      },
      series: [
        {
          type: 'bar',
          data: roas,
          itemStyle: {
            color: (p) => {
              const v = parseFloat(p.value);
              if (v >= 5.0) return '#a3e635';
              if (v >= 4.0) return '#38bdf8';
              if (v >= 3.2) return '#fbbf24';
              return '#f87171';
            },
            borderRadius: [0, 4, 4, 0]
          },
          label: {
            show: true,
            position: 'right',
            formatter: '{c}x',
            color: '#f8fafc',
            fontWeight: 'bold'
          }
        }
      ]
    };

    chart.setOption(option);
  },

  // 7. RFM LTV Concentration
  renderRfmLtv() {
    const chart = this.getChart('chart-rfm-ltv');
    if (!chart || !window.dashboardData) return;

    const segments = window.dashboardData.customers_rfm?.segments || [];
    const data = segments.map(s => ({
      name: s.segmento_rfm,
      value: s.ltv_total,
      itemStyle: { color: s.color }
    }));

    const option = {
      ...this.theme,
      tooltip: {
        trigger: 'item',
        formatter: (p) => `${p.name}: <strong>R$ ${(p.value/1e6).toFixed(2)}M</strong> (${p.percent}%)`
      },
      legend: {
        bottom: '2%',
        left: 'center',
        textStyle: { color: '#94a3b8', fontSize: 11 },
        itemWidth: 10,
        itemHeight: 10
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '68%'],
          center: ['50%', '44%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#16213e',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
              color: '#f8fafc',
              formatter: '{b}\n{d}%',
              lineHeight: 20
            }
          },
          data: data
        }
      ]
    };

    chart.setOption(option);
  },

  // 8. RFM Behavior (Desconto vs Devolução)
  renderRfmBehavior() {
    const chart = this.getChart('chart-rfm-behavior');
    if (!chart || !window.dashboardData) return;

    const segments = window.dashboardData.customers_rfm?.segments || [];
    const names = segments.map(s => s.segmento_rfm);
    const disc = segments.map(s => s.pct_desconto.toFixed(2));
    const ret = segments.map(s => (s.taxa_devolucao || 0).toFixed(2));

    const option = {
      ...this.theme,
      tooltip: { trigger: 'axis' },
      legend: { data: ['Desconto Médio (%)', 'Taxa Devolução (%)'], textStyle: { color: '#94a3b8' } },
      grid: { left: '4%', right: '4%', bottom: '10%', top: '15%', containLabel: true },
      xAxis: { type: 'category', data: names, axisLine: { lineStyle: { color: '#27374d' } } },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: '{value}%', color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      series: [
        {
          name: 'Desconto Médio (%)',
          type: 'bar',
          data: disc,
          itemStyle: { color: '#fbbf24', borderRadius: [4, 4, 0, 0] }
        },
        {
          name: 'Taxa Devolução (%)',
          type: 'bar',
          data: ret,
          itemStyle: { color: '#f87171', borderRadius: [4, 4, 0, 0] }
        }
      ]
    };

    chart.setOption(option);
  },

  // 9. SAC Categories & AI Deflection
  renderSacCategories() {
    const chart = this.getChart('chart-sac-categories');
    if (!chart || !window.dashboardData) return;

    const cats = window.dashboardData.customer_service?.categories || [];
    const sorted = [...cats].reverse();
    const names = sorted.map(c => c.categoria_normalizada);
    const tickets = sorted.map(c => c.tickets);

    const option = {
      ...this.theme,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: { left: '4%', right: '12%', bottom: '5%', top: '5%', containLabel: true },
      xAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: { lineStyle: { color: '#27374d' } }
      },
      series: [
        {
          type: 'bar',
          data: tickets,
          itemStyle: { color: '#38bdf8', borderRadius: [0, 4, 4, 0] },
          label: {
            show: true,
            position: 'right',
            formatter: '{c} tickets',
            color: '#f8fafc',
            fontSize: 10
          }
        }
      ]
    };

    chart.setOption(option);
  },

  // 10. Returns Causes Donut
  renderReturnsCauses() {
    const chart = this.getChart('chart-returns-causes');
    if (!chart) return;

    // Direct figures from diagnostico: 69.6% operational (Defeito 1.039, Tamanho 1.025, Atraso 808)
    const data = [
      { name: 'Defeito de Produto', value: 1039, itemStyle: { color: '#f87171' } },
      { name: 'Tamanho Errado', value: 1025, itemStyle: { color: '#fb923c' } },
      { name: 'Atraso na Entrega', value: 808, itemStyle: { color: '#fbbf24' } },
      { name: 'Arrependimento / Outros', value: 1255, itemStyle: { color: '#64748b' } }
    ];

    const option = {
      ...this.theme,
      tooltip: {
        trigger: 'item',
        formatter: (p) => `${p.name}: <strong>${p.value} pedidos</strong> (${p.percent}%)`
      },
      legend: {
        bottom: '2%',
        left: 'center',
        textStyle: { color: '#94a3b8', fontSize: 11 },
        itemWidth: 10,
        itemHeight: 10
      },
      series: [
        {
          type: 'pie',
          radius: ['42%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: true,
          label: {
            show: true,
            position: 'inside',
            formatter: '{d}%',
            color: '#f8fafc',
            fontSize: 11,
            fontWeight: 'bold'
          },
          data: data
        }
      ]
    };

    chart.setOption(option);
  },

  // 11. Stock by Product Category
  renderStockCategories() {
    const chart = this.getChart('chart-stock-categories');
    if (!chart || !window.dashboardData) return;

    const cats = window.dashboardData.inventory?.category_distribution || [];
    const names = cats.map(c => c.categoria);
    const costs = cats.map(c => (c.custo_total / 1e6).toFixed(2));

    const option = {
      ...this.theme,
      tooltip: { trigger: 'axis' },
      grid: { left: '4%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
      xAxis: { type: 'category', data: names, axisLine: { lineStyle: { color: '#27374d' } } },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: 'R$ {value}M', color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      series: [
        {
          type: 'bar',
          data: costs,
          itemStyle: { color: '#a3e635', borderRadius: [4, 4, 0, 0] },
          label: {
            show: true,
            position: 'top',
            formatter: 'R$ {c}M',
            color: '#f8fafc',
            fontWeight: 'bold'
          }
        }
      ]
    };

    chart.setOption(option);
  },

  stockStatusPalette: {
    'Em Estoque': '#10b981',
    'Estoque Crítico': '#f59e0b',
    'Estoque Critico': '#f59e0b',
    'Ruptura': '#ef4444',
    'Descontinuado': '#8b5cf6'
  },

  // 12. Stock Availability Status
  renderStockStatus() {
    const chart = this.getChart('chart-stock-status');
    if (!chart || !window.dashboardData) return;

    const status = window.dashboardData.inventory?.status_distribution || [];
    const data = status.map(s => {
      const name = s.status_disponibilidade || '';
      const color = this.stockStatusPalette[name] ||
        (name.toLowerCase().includes('crítico') || name.toLowerCase().includes('critico') ? '#f59e0b' :
         name.toLowerCase().includes('ruptura') ? '#ef4444' :
         name.toLowerCase().includes('descontinuado') ? '#8b5cf6' : '#10b981');

      return {
        name: name,
        value: s.custo_total,
        itemStyle: { color }
      };
    });

    const option = {
      ...this.theme,
      tooltip: {
        trigger: 'item',
        formatter: (p) => {
          const valStr = p.value >= 1e6
            ? `R$ ${(p.value / 1e6).toFixed(2)}M`
            : `R$ ${(p.value / 1e3).toFixed(1)}k`;
          return `${p.name}: <strong>${valStr}</strong> (${p.percent}%)`;
        }
      },
      legend: {
        bottom: '2%',
        left: 'center',
        textStyle: { color: '#94a3b8', fontSize: 11 },
        itemWidth: 10,
        itemHeight: 10
      },
      series: [
        {
          type: 'pie',
          radius: ['42%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: true,
          label: {
            show: true,
            position: 'inside',
            formatter: (p) => p.percent >= 2 ? `${p.percent}%` : '',
            color: '#f8fafc',
            fontSize: 11,
            fontWeight: 'bold'
          },
          data: data
        }
      ]
    };

    chart.setOption(option);
  }
};
