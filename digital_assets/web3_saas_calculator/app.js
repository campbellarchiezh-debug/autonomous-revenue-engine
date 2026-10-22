/**
 * Web3 Staking & Node ROI Calculator Engine
 * Standalone turnkey financial modeling & pure-SVG charting engine.
 * Zero external libraries or frameworks (Vanilla ES6).
 */

(function () {
  'use strict';

  // Default initial configuration
  const DEFAULTS = {
    initialPrincipal: 50000,
    aprRate: 8.5,
    compoundingFreq: 365,
    commissionRate: 5.0,
    monthlyOpEx: 120,
    mevBoost: 2.5,
    tokenAppreciation: 10,
    horizonYears: 5
  };

  // State object
  const state = { ...DEFAULTS };

  // DOM Elements
  const inputs = {
    initialPrincipal: document.getElementById('initialPrincipal'),
    initialPrincipalNum: document.getElementById('initialPrincipalNum'),
    aprRate: document.getElementById('aprRate'),
    aprRateNum: document.getElementById('aprRateNum'),
    compoundingFreq: document.getElementById('compoundingFreq'),
    commissionRate: document.getElementById('commissionRate'),
    commissionRateNum: document.getElementById('commissionRateNum'),
    monthlyOpEx: document.getElementById('monthlyOpEx'),
    monthlyOpExNum: document.getElementById('monthlyOpExNum'),
    mevBoost: document.getElementById('mevBoost'),
    mevBoostNum: document.getElementById('mevBoostNum'),
    tokenAppreciation: document.getElementById('tokenAppreciation'),
    tokenAppreciationNum: document.getElementById('tokenAppreciationNum'),
    horizonYears: document.getElementById('horizonYears'),
    horizonYearsNum: document.getElementById('horizonYearsNum')
  };

  const metrics = {
    netApy: document.getElementById('metricNetApy'),
    apySpread: document.getElementById('metricApySpread'),
    grossAnnual: document.getElementById('metricGrossAnnual'),
    monthlyYield: document.getElementById('metricMonthlyYield'),
    netCashflow: document.getElementById('metricNetCashflow'),
    opExDeducted: document.getElementById('metricOpExDeducted'),
    breakEven: document.getElementById('metricBreakEven'),
    totalWealth: document.getElementById('metricTotalWealth'),
    totalGain: document.getElementById('metricTotalGain')
  };

  const svgChart = document.getElementById('projectionChart');
  const chartTooltip = document.getElementById('chartTooltip');
  const scheduleTableBody = document.getElementById('scheduleTableBody');
  const scenarioTableBody = document.getElementById('scenarioTableBody');
  const resetBtn = document.getElementById('resetDefaultsBtn');
  const exportBtn = document.getElementById('exportCsvBtn');

  // Format currency
  function formatUSD(val, maxDecimals = 0) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: maxDecimals,
      minimumFractionDigits: maxDecimals
    }).format(val);
  }

  // Format percentage
  function formatPct(val, decimals = 2) {
    return `${val.toFixed(decimals)}%`;
  }

  // Setup 2-way data binding between slider and number inputs
  function setupBinding(sliderKey, numKey) {
    const slider = inputs[sliderKey];
    const num = inputs[numKey];
    if (!slider || !num) return;

    slider.addEventListener('input', () => {
      num.value = slider.value;
      state[sliderKey] = parseFloat(slider.value);
      recalculate();
    });

    num.addEventListener('input', () => {
      slider.value = num.value;
      state[sliderKey] = parseFloat(num.value) || 0;
      recalculate();
    });
  }

  // Initialize input bindings
  function initInputs() {
    setupBinding('initialPrincipal', 'initialPrincipalNum');
    setupBinding('aprRate', 'aprRateNum');
    setupBinding('commissionRate', 'commissionRateNum');
    setupBinding('monthlyOpEx', 'monthlyOpExNum');
    setupBinding('mevBoost', 'mevBoostNum');
    setupBinding('tokenAppreciation', 'tokenAppreciationNum');
    setupBinding('horizonYears', 'horizonYearsNum');

    if (inputs.compoundingFreq) {
      inputs.compoundingFreq.addEventListener('change', () => {
        state.compoundingFreq = parseInt(inputs.compoundingFreq.value, 10);
        recalculate();
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        Object.assign(state, DEFAULTS);
        Object.keys(DEFAULTS).forEach(key => {
          if (inputs[key]) inputs[key].value = DEFAULTS[key];
          if (inputs[key + 'Num']) inputs[key + 'Num'].value = DEFAULTS[key];
        });
        recalculate();
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener('click', exportSimulationReport);
    }
  }

  // Core Financial Calculation Logic
  function calculateModel(params) {
    const P = params.initialPrincipal;
    const aprNominal = (params.aprRate / 100) * (1 + params.mevBoost / 100);
    const netAprRate = aprNominal * (1 - params.commissionRate / 100);
    const n = params.compoundingFreq;
    const opexAnnual = params.monthlyOpEx * 12;
    const growthRate = params.tokenAppreciation / 100;
    const years = params.horizonYears;

    // Calculate effective APY
    let effectiveApy;
    if (n > 0) {
      effectiveApy = Math.pow(1 + netAprRate / n, n) - 1;
    } else {
      effectiveApy = netAprRate;
    }

    const year1GrossYield = P * aprNominal;
    const year1NetYield = P * effectiveApy;
    const year1NetCashflow = year1NetYield - opexAnnual;

    // Break-even horizon (months to recoup OpEx from staking yield)
    let breakEvenMonths = 0;
    const monthlyNetYield = year1NetYield / 12;
    if (monthlyNetYield <= 0) {
      breakEvenMonths = Infinity;
    } else if (params.monthlyOpEx <= 0) {
      breakEvenMonths = 0;
    } else {
      breakEvenMonths = (params.monthlyOpEx / monthlyNetYield) * 12; // annualized ratio * 12
    }

    // Multi-year compounding timeline
    const timeline = [];
    let currentBalance = P;
    let cumulativeRewards = 0;
    let cumulativeOpEx = 0;

    // Initial Year 0 point
    timeline.push({
      year: 0,
      startPrincipal: P,
      grossRewards: 0,
      netRewards: 0,
      annualOpEx: 0,
      netCashflow: 0,
      endingBalance: P,
      cumulativeRewards: 0,
      cumulativeOpEx: 0,
      cumulativeRoi: 0
    });

    for (let yr = 1; yr <= years; yr++) {
      const startOfYr = currentBalance;
      // Staking yield earned this year on the balance
      const yrGrossRewards = startOfYr * aprNominal;
      const yrNetRewards = startOfYr * effectiveApy;
      const yrOpEx = opexAnnual;
      const yrNetCashflow = yrNetRewards - yrOpEx;

      cumulativeRewards += yrNetRewards;
      cumulativeOpEx += yrOpEx;

      // End of year balance includes staking gains + asset appreciation - OpEx
      currentBalance = (startOfYr + yrNetRewards) * (1 + growthRate) - yrOpEx;
      if (currentBalance < 0) currentBalance = 0;

      const totalGain = currentBalance - P;
      const cumulativeRoi = P > 0 ? (totalGain / P) * 100 : 0;

      timeline.push({
        year: yr,
        startPrincipal: startOfYr,
        grossRewards: yrGrossRewards,
        netRewards: yrNetRewards,
        annualOpEx: yrOpEx,
        netCashflow: yrNetCashflow,
        endingBalance: currentBalance,
        cumulativeRewards: cumulativeRewards,
        cumulativeOpEx: cumulativeOpEx,
        cumulativeRoi: cumulativeRoi
      });
    }

    const finalPoint = timeline[timeline.length - 1];

    return {
      effectiveApy,
      year1GrossYield,
      year1NetYield,
      year1NetCashflow,
      breakEvenMonths,
      endingWealth: finalPoint.endingBalance,
      cumulativeRoi: finalPoint.cumulativeRoi,
      timeline
    };
  }

  // Recalculate metrics, chart, and tables
  function recalculate() {
    const result = calculateModel(state);

    // Update KPI metrics
    if (metrics.netApy) {
      metrics.netApy.textContent = formatPct(result.effectiveApy * 100);
    }
    if (metrics.apySpread) {
      const spread = (result.effectiveApy * 100) - state.aprRate;
      metrics.apySpread.textContent = `${spread >= 0 ? '+' : ''}${spread.toFixed(2)}% vs ${state.aprRate}% nominal`;
    }
    if (metrics.grossAnnual) {
      metrics.grossAnnual.textContent = formatUSD(result.year1GrossYield);
    }
    if (metrics.monthlyYield) {
      metrics.monthlyYield.textContent = `~${formatUSD(result.year1GrossYield / 12)} / month`;
    }
    if (metrics.netCashflow) {
      metrics.netCashflow.textContent = formatUSD(result.year1NetCashflow);
      metrics.netCashflow.className = result.year1NetCashflow >= 0 ? 'kpi-value text-green' : 'kpi-value text-accent';
    }
    if (metrics.opExDeducted) {
      metrics.opExDeducted.textContent = `OpEx: -${formatUSD(state.monthlyOpEx * 12)} / yr`;
    }
    if (metrics.breakEven) {
      if (result.breakEvenMonths === Infinity || result.breakEvenMonths < 0) {
        metrics.breakEven.textContent = 'Unprofitable';
      } else {
        metrics.breakEven.textContent = `${result.breakEvenMonths.toFixed(1)} Months`;
      }
    }
    if (metrics.totalWealth) {
      metrics.totalWealth.textContent = formatUSD(result.endingWealth);
    }
    if (metrics.totalGain) {
      const sign = result.cumulativeRoi >= 0 ? '+' : '';
      metrics.totalGain.textContent = `${sign}${result.cumulativeRoi.toFixed(1)}% net gain over ${state.horizonYears} yrs`;
    }

    // Render SVG chart
    renderSvgChart(result.timeline);

    // Render schedule table
    renderScheduleTable(result.timeline);

    // Render scenarios
    renderScenarioMatrix();
  }

  // Pure SVG Chart Renderer (Zero external libraries)
  function renderSvgChart(timeline) {
    if (!svgChart || !timeline || timeline.length === 0) return;

    const width = 760;
    const height = 320;
    const pad = { top: 30, right: 35, bottom: 40, left: 75 };
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;

    // Determine scale limits
    let maxVal = 0;
    timeline.forEach(pt => {
      if (pt.endingBalance > maxVal) maxVal = pt.endingBalance;
      if (pt.cumulativeRewards > maxVal) maxVal = pt.cumulativeRewards;
      if (pt.cumulativeOpEx > maxVal) maxVal = pt.cumulativeOpEx;
    });
    maxVal = maxVal * 1.15; // 15% headroom
    if (maxVal <= 0) maxVal = 1000;

    const numPoints = timeline.length;
    const getX = (idx) => pad.left + (idx / (numPoints - 1)) * chartW;
    const getY = (val) => pad.top + chartH - (Math.max(0, val) / maxVal) * chartH;

    // Build SVG inner elements
    let svgHtml = `
      <defs>
        <linearGradient id="wealthGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#10b981" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
        </linearGradient>
        <linearGradient id="rewardsGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
    `;

    // Horizontal Grid Lines & Y-axis labels
    const gridSteps = 4;
    for (let i = 0; i <= gridSteps; i++) {
      const v = (maxVal / gridSteps) * i;
      const yPos = getY(v);
      svgHtml += `
        <line x1="${pad.left}" y1="${yPos}" x2="${pad.left + chartW}" y2="${yPos}" stroke="rgba(75, 85, 99, 0.25)" stroke-dasharray="3 3" />
        <text x="${pad.left - 10}" y="${yPos + 4}" fill="#9ca3af" font-size="11" font-family="ui-monospace, monospace" text-anchor="end">${formatUSD(v, 0)}</text>
      `;
    }

    // X-axis baseline & labels
    timeline.forEach((pt, idx) => {
      const xPos = getX(idx);
      svgHtml += `
        <line x1="${xPos}" y1="${pad.top}" x2="${xPos}" y2="${pad.top + chartH}" stroke="rgba(75, 85, 99, 0.15)" stroke-dasharray="2 2" />
        <text x="${xPos}" y="${pad.top + chartH + 24}" fill="#9ca3af" font-size="11" font-family="ui-monospace, monospace" text-anchor="middle">Yr ${pt.year}</text>
      `;
    });

    // Generate Path Data
    function buildPath(accessor) {
      let d = '';
      timeline.forEach((pt, idx) => {
        const x = getX(idx);
        const y = getY(accessor(pt));
        d += (idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
      });
      return d;
    }

    function buildAreaPath(accessor) {
      const lineD = buildPath(accessor);
      const firstX = getX(0);
      const lastX = getX(timeline.length - 1);
      const baseY = getY(0);
      return `${lineD} L ${lastX} ${baseY} L ${firstX} ${baseY} Z`;
    }

    const wealthLine = buildPath(pt => pt.endingBalance);
    const wealthArea = buildAreaPath(pt => pt.endingBalance);

    const rewardsLine = buildPath(pt => pt.cumulativeRewards);
    const rewardsArea = buildAreaPath(pt => pt.cumulativeRewards);

    const opexLine = buildPath(pt => pt.cumulativeOpEx);

    // Render Area Fills
    svgHtml += `<path d="${wealthArea}" fill="url(#wealthGrad)" />`;
    svgHtml += `<path d="${rewardsArea}" fill="url(#rewardsGrad)" />`;

    // Render Lines
    svgHtml += `<path d="${opexLine}" fill="none" stroke="#f43f5e" stroke-width="2.5" stroke-dasharray="4 4" />`;
    svgHtml += `<path d="${rewardsLine}" fill="none" stroke="#06b6d4" stroke-width="2.5" />`;
    svgHtml += `<path d="${wealthLine}" fill="none" stroke="#10b981" stroke-width="3" />`;

    // Render Data Dot Nodes with interactivity
    timeline.forEach((pt, idx) => {
      const x = getX(idx);
      const yWealth = getY(pt.endingBalance);
      const yRewards = getY(pt.cumulativeRewards);

      svgHtml += `
        <circle class="chart-dot" cx="${x}" cy="${yWealth}" r="5" fill="#10b981" stroke="#0a0e17" stroke-width="2" 
          data-year="${pt.year}" data-wealth="${pt.endingBalance}" data-rewards="${pt.cumulativeRewards}" data-opex="${pt.cumulativeOpEx}" />
        <circle class="chart-dot" cx="${x}" cy="${yRewards}" r="4" fill="#06b6d4" stroke="#0a0e17" stroke-width="2" 
          data-year="${pt.year}" data-wealth="${pt.endingBalance}" data-rewards="${pt.cumulativeRewards}" data-opex="${pt.cumulativeOpEx}" />
      `;
    });

    svgChart.innerHTML = svgHtml;

    // Attach hover listeners to dots
    const dots = svgChart.querySelectorAll('.chart-dot');
    dots.forEach(dot => {
      dot.addEventListener('mouseenter', (e) => {
        const yr = e.target.getAttribute('data-year');
        const wealth = parseFloat(e.target.getAttribute('data-wealth'));
        const rew = parseFloat(e.target.getAttribute('data-rewards'));
        const opx = parseFloat(e.target.getAttribute('data-opex'));

        if (chartTooltip) {
          chartTooltip.innerHTML = `
            <strong>Year ${yr} Breakdown</strong><br>
            Total Portfolio: ${formatUSD(wealth)}<br>
            Staking Yield: +${formatUSD(rew)}<br>
            Cumulative OpEx: -${formatUSD(opx)}
          `;
          chartTooltip.style.display = 'block';
          const rect = svgChart.getBoundingClientRect();
          const cx = parseFloat(e.target.getAttribute('cx'));
          const cy = parseFloat(e.target.getAttribute('cy'));
          chartTooltip.style.left = `${(cx / width) * 100}%`;
          chartTooltip.style.top = `${(cy / height) * 100}%`;
        }
      });

      dot.addEventListener('mouseleave', () => {
        if (chartTooltip) chartTooltip.style.display = 'none';
      });
    });
  }

  // Render Amortization Schedule Table
  function renderScheduleTable(timeline) {
    if (!scheduleTableBody) return;
    let html = '';

    timeline.forEach((row, idx) => {
      if (idx === 0) return; // skip initial seed year
      const roiColor = row.cumulativeRoi >= 0 ? '#34d399' : '#f87171';
      html += `
        <tr>
          <td>Year ${row.year}</td>
          <td>${formatUSD(row.startPrincipal)}</td>
          <td class="text-accent">+${formatUSD(row.netRewards)}</td>
          <td style="color: #f87171;">-${formatUSD(row.annualOpEx)}</td>
          <td>${formatUSD(row.netCashflow)}</td>
          <td><strong>${formatUSD(row.endingBalance)}</strong></td>
          <td style="color: ${roiColor}; font-weight: 600;">${row.cumulativeRoi >= 0 ? '+' : ''}${row.cumulativeRoi.toFixed(1)}%</td>
        </tr>
      `;
    });

    scheduleTableBody.innerHTML = html;
  }

  // Render Scenario Sensitivity Matrix
  function renderScenarioMatrix() {
    if (!scenarioTableBody) return;

    const scenarios = [
      {
        name: 'Bearish Stress-Test',
        tag: 'Bear (-25% Yield, -15% Growth)',
        params: {
          ...state,
          aprRate: state.aprRate * 0.75,
          mevBoost: state.mevBoost * 0.5,
          tokenAppreciation: -15
        }
      },
      {
        name: 'Baseline Projection',
        tag: 'Baseline (Current Input Assumptions)',
        params: { ...state }
      },
      {
        name: 'Bullish Outperformance',
        tag: 'Bull (+35% Yield, +25% Growth)',
        params: {
          ...state,
          aprRate: state.aprRate * 1.35,
          mevBoost: state.mevBoost * 1.5,
          tokenAppreciation: state.tokenAppreciation + 15
        }
      }
    ];

    let html = '';
    scenarios.forEach(sc => {
      const res = calculateModel(sc.params);
      const isBase = sc.name === 'Baseline Projection';
      const bgStyle = isBase ? 'background: rgba(99, 102, 241, 0.1); font-weight: 600;' : '';
      const roiColor = res.cumulativeRoi >= 0 ? '#34d399' : '#f87171';

      html += `
        <tr style="${bgStyle}">
          <td><strong>${sc.name}</strong><br><span style="font-size: 0.72rem; color: #9ca3af;">${sc.tag}</span></td>
          <td>${formatPct(res.effectiveApy * 100)}</td>
          <td>${formatPct(sc.params.tokenAppreciation)} / yr</td>
          <td>${formatUSD(res.year1NetCashflow)}</td>
          <td><strong>${formatUSD(res.endingWealth)}</strong></td>
          <td style="color: ${roiColor}; font-weight: 600;">${res.cumulativeRoi >= 0 ? '+' : ''}${res.cumulativeRoi.toFixed(1)}%</td>
        </tr>
      `;
    });

    scenarioTableBody.innerHTML = html;
  }

  // Export Simulation Report as JSON
  function exportSimulationReport() {
    const reportData = {
      timestamp: new Date().toISOString(),
      generator: "Web3 Staking & Validator ROI Modeler (Autonomous Revenue Engine)",
      license: "MIT",
      assumptions: state,
      results: calculateModel(state),
      beneficiaryWallets: {
        base_evm: "0xef5766253e2d92e530e301ac22dcb8de78e89c55",
        solana: "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp",
        bitcoin: "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e",
        stellar: "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA"
      }
    };

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(reportData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `web3_staking_model_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast("Simulation JSON exported successfully!");
  }

  // Copy to clipboard helper
  window.copyWallet = function (elementId, btnElement) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.textContent.trim();

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showCopyFeedback(btnElement);
      }).catch(() => {
        fallbackCopy(text, btnElement);
      });
    } else {
      fallbackCopy(text, btnElement);
    }
  };

  function fallbackCopy(text, btnElement) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      showCopyFeedback(btnElement);
    } catch (err) {
      console.error('Fallback copy failed', err);
    }
    document.body.removeChild(textArea);
  }

  function showCopyFeedback(btnElement) {
    if (btnElement) {
      const orig = btnElement.textContent;
      btnElement.textContent = "Copied!";
      btnElement.style.background = "#10b981";
      btnElement.style.color = "#ffffff";
      setTimeout(() => {
        btnElement.textContent = orig;
        btnElement.style.background = "";
        btnElement.style.color = "";
      }, 1800);
    }
    showToast("Address copied to clipboard!");
  }

  function showToast(msg) {
    const toast = document.getElementById('toastNotification');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2400);
  }

  // Start on load
  document.addEventListener('DOMContentLoaded', () => {
    initInputs();
    recalculate();
  });
})();
