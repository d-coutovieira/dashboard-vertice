/**
 * simulators.js - Interactive Strategic Simulators.
 * Preserves the Discontinued Inventory Liquidation Simulator in Estoque & Capital.
 */

window.SimulatorsManager = {
  init() {
    this.initStockSimulator();
  },

  // Discontinued Inventory Liquidation Simulator (Integrated in Estoque Tab)
  initStockSimulator() {
    const slDisc = document.getElementById('slider-liq-disc');
    const slTime = document.getElementById('slider-liq-time');

    const valDisc = document.getElementById('val-sim-liq-disc');
    const valTime = document.getElementById('val-sim-liq-time');

    const outCash = document.getElementById('sim-stock-cash');
    const outInterest = document.getElementById('sim-stock-interest');
    const btnReset = document.getElementById('btn-reset-sim-stock');

    const calculate = () => {
      if (!slDisc || !slTime) return;
      const discPct = parseFloat(slDisc.value);
      const months = parseFloat(slTime.value);

      if (valDisc) valDisc.textContent = `${discPct.toFixed(0)}%`;
      if (valTime) valTime.textContent = `${months.toFixed(0)} ${months === 1 ? 'mês' : 'meses'}`;

      const discontinuedCost = 17714096.89; // R$ 17.71M
      const waccRate = 0.18; // 18% a.a.

      // Cash generated considering recovery rate
      const cashUnlocked = discontinuedCost * (1.0 - (discPct / 100.0));
      const interestSavings = discontinuedCost * waccRate;

      if (outCash) outCash.textContent = `R$ ${(cashUnlocked / 1e6).toFixed(2)}M`;
      if (outInterest) outInterest.textContent = `+ R$ ${(interestSavings / 1e6).toFixed(2)}M/ano`;
    };

    if (slDisc) slDisc.addEventListener('input', calculate);
    if (slTime) slTime.addEventListener('input', calculate);

    if (btnReset) {
      btnReset.addEventListener('click', () => {
        if (slDisc) slDisc.value = 35;
        if (slTime) slTime.value = 3;
        calculate();
      });
    }

    calculate();
  }
};
