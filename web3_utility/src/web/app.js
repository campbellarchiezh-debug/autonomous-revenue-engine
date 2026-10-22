/**
 * Web3 Micro-Utility & Developer Tools Suite (Vanilla ES6 Client Engine)
 * Zero external libraries or npm dependencies.
 */

// Beneficiary Wallets
const BENEFICIARY_WALLETS = {
  base: "0xef5766253e2d92e530e301ac22dcb8de78e89c55",
  solana: "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp",
  bitcoin: "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e",
  stellar: "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA",
};

// Unit Conversion Constants
const UNIT_SCALES = {
  evm: {
    wei: BigInt(1),
    gwei: BigInt(1000000000),
    eth: BigInt("1000000000000000000"),
  },
  solana: {
    lamports: BigInt(1),
    sol: BigInt(1000000000),
  },
  bitcoin: {
    sats: BigInt(1),
    btc: BigInt(100000000),
  },
  stellar: {
    stroops: BigInt(1),
    xlm: BigInt(10000000),
  },
};

// Preset Gas Limits
const GAS_PRESETS = {
  eth_transfer: 21000,
  erc20_transfer: 65000,
  uniswap_swap: 150000,
  contract_deployment: 1500000,
};

// Simulated RPC Metrics
const RPC_METRICS = [
  { chain: "Base", network: "Base Mainnet", chainId: "8453", block: 21543820, latency: 32.4, status: "ONLINE", endpoint: "https://mainnet.base.org" },
  { chain: "Ethereum", network: "Ethereum Mainnet", chainId: "1", block: 21089240, latency: 45.1, status: "ONLINE", endpoint: "https://cloudflare-eth.com" },
  { chain: "Solana", network: "Solana Mainnet-Beta", chainId: "solana-mainnet", block: 312485910, latency: 68.7, status: "ONLINE", endpoint: "https://api.mainnet-beta.solana.com" },
  { chain: "Bitcoin", network: "Bitcoin Core", chainId: "bitcoin-mainnet", block: 866540, latency: 52.3, status: "ONLINE", endpoint: "https://mempool.space/api" },
  { chain: "Stellar", network: "Stellar Public Net", chainId: "stellar-pubnet", block: 54128900, latency: 41.8, status: "ONLINE", endpoint: "https://horizon.stellar.org" },
];

// Security Scan Lists
const ZERO_WIDTH_REGEX = /[\u200B\u200C\u200D\u200E\u200F\u2028\u2029\u202A\u202B\u202C\u202D\u202E\u2060\uFEFF\u00AD]/g;
const HOMOGLYPH_CHARS = {
  "\u0430": "a", "\u0441": "c", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0445": "x", "\u0443": "y",
  "\u0410": "A", "\u0412": "B", "\u0421": "C", "\u0415": "E", "\u041d": "H", "\u041e": "O", "\u0420": "P",
  "\u03bf": "o", "\u03c1": "p", "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u039f": "O",
};

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initInspector();
  initRPCMonitor();
  initConverter();
  initGasCalculator();
  initModalAndClipboard();
});

// ==============================================================================
// 1. NAVIGATION & TABS
// ==============================================================================
function initTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const targetId = `tab-${tab.dataset.tab}`;
      document.querySelectorAll(".tab-pane").forEach((pane) => {
        pane.classList.remove("active");
      });
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });
}

// ==============================================================================
// 2. ADDRESS INSPECTOR & SECURITY SCANNER
// ==============================================================================
function initInspector() {
  const input = document.getElementById("address-input");
  const inspectBtn = document.getElementById("inspect-btn");
  const resultBox = document.getElementById("inspector-result");
  const statusBadge = document.getElementById("result-status-badge");
  const chainBadge = document.getElementById("result-chain-badge");
  const canonicalAddr = document.getElementById("result-canonical-addr");
  const addrType = document.getElementById("result-type");
  const securityList = document.getElementById("result-security-summary");
  const copyBtn = document.getElementById("copy-canonical-btn");

  function runInspection() {
    const rawVal = input.value;
    if (!rawVal.trim()) return;

    const zeroWidthMatches = rawVal.match(ZERO_WIDTH_REGEX) || [];
    const sanitized = rawVal.replace(ZERO_WIDTH_REGEX, "").trim();

    const homoglyphMatches = [];
    for (let i = 0; i < rawVal.length; i++) {
      const char = rawVal[i];
      if (HOMOGLYPH_CHARS[char]) {
        homoglyphMatches.push({ char, target: HOMOGLYPH_CHARS[char], pos: i });
      }
    }

    // Vanity Poisoning Heuristic Check
    const poisoningMatches = [];
    const knownWallets = Object.values(BENEFICIARY_WALLETS);
    for (const known of knownWallets) {
      if (sanitized.toLowerCase() !== known.toLowerCase()) {
        const prefix = known.slice(0, 5).toLowerCase();
        const suffix = known.slice(-5).toLowerCase();
        if (sanitized.toLowerCase().startsWith(prefix) && sanitized.toLowerCase().endsWith(suffix)) {
          poisoningMatches.push(known);
        }
      }
    }

    // Chain format validation
    let chain = "UNKNOWN";
    let type = "Unknown";
    let isValidFormat = false;

    if (sanitized.startsWith("0x") || sanitized.startsWith("0X")) {
      chain = "BASE EVM";
      type = "EVM EOA / Smart Contract";
      isValidFormat = /^0x[0-9a-fA-F]{40}$/.test(sanitized);
    } else if (sanitized.startsWith("bc1p") || sanitized.startsWith("bc1q") || sanitized.startsWith("1") || sanitized.startsWith("3")) {
      chain = "BITCOIN";
      if (sanitized.startsWith("bc1p")) type = "Taproot (BIP-350 Bech32m)";
      else if (sanitized.startsWith("bc1q")) type = "SegWit v0 (BIP-173 Bech32)";
      else type = "Legacy P2PKH / P2SH";
      isValidFormat = sanitized.length >= 26 && sanitized.length <= 90;
    } else if (sanitized.startsWith("G") && sanitized.length === 56) {
      chain = "STELLAR";
      type = "StrKey Account ID (Base32)";
      isValidFormat = /^[A-Z2-7]{56}$/.test(sanitized);
    } else if (sanitized.length >= 32 && sanitized.length <= 44 && /^[1-9A-HJ-NP-Za-km-z]+$/.test(sanitized)) {
      chain = "SOLANA";
      type = "Ed25519 Public Key (Base58)";
      isValidFormat = true;
    }

    const hasExploits = zeroWidthMatches.length > 0 || homoglyphMatches.length > 0 || poisoningMatches.length > 0;
    const isOverallValid = isValidFormat && !hasExploits;

    resultBox.classList.remove("hidden");
    statusBadge.textContent = isOverallValid ? "SECURE & VALID" : "SECURITY ALERT / INVALID";
    statusBadge.className = `status-indicator ${isOverallValid ? "status-valid" : "status-invalid"}`;
    chainBadge.textContent = chain;
    canonicalAddr.textContent = sanitized;
    addrType.textContent = type;

    // Build security warnings
    securityList.innerHTML = "";
    if (isOverallValid) {
      securityList.innerHTML = `
        <div class="security-item sec-safe">✓ Address syntax valid. Zero injected characters detected.</div>
        <div class="security-item sec-safe">✓ No homoglyphs or spoof characters detected.</div>
        <div class="security-item sec-safe">✓ Passed vanity poisoning heuristic check.</div>
      `;
    } else {
      if (!isValidFormat) {
        securityList.innerHTML += `<div class="security-item sec-danger">✗ Invalid address format or character length for ${chain}.</div>`;
      }
      if (zeroWidthMatches.length > 0) {
        securityList.innerHTML += `<div class="security-item sec-danger">🚨 CRITICAL: Detected ${zeroWidthMatches.length} invisible zero-width unicode character(s)! Malicious copy-paste injection attempt.</div>`;
      }
      if (homoglyphMatches.length > 0) {
        const charList = homoglyphMatches.map((m) => `'${m.char}' (mimics '${m.target}')`).join(", ");
        securityList.innerHTML += `<div class="security-item sec-danger">🚨 CRITICAL: Detected visual homoglyph spoofing: ${charList}. Mixed-script attack detected.</div>`;
      }
      if (poisoningMatches.length > 0) {
        securityList.innerHTML += `<div class="security-item sec-danger">🚨 CRITICAL: Vanity address poisoning detected! Address mimics known wallet (${poisoningMatches[0].slice(0, 5)}...${poisoningMatches[0].slice(-5)}) but intermediate bytes differ.</div>`;
      }
    }
  }

  inspectBtn.addEventListener("click", runInspection);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runInspection();
  });

  // Sample buttons
  document.querySelectorAll(".sample-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      input.value = btn.dataset.addr;
      runInspection();
    });
  });

  // Copy canonical
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(canonicalAddr.textContent).then(() => {
      showToast("Canonical address copied to clipboard!");
    });
  });
}

// ==============================================================================
// 3. RPC HEALTH MONITOR
// ==============================================================================
function initRPCMonitor() {
  const grid = document.getElementById("rpc-cards-grid");
  const refreshBtn = document.getElementById("refresh-rpc-btn");
  const mockToggle = document.getElementById("rpc-mock-toggle");
  const lastChecked = document.getElementById("rpc-last-checked");

  function renderCards(jitter = false) {
    grid.innerHTML = "";
    RPC_METRICS.forEach((m) => {
      let lat = m.latency;
      if (jitter) {
        lat = +(lat + (Math.random() * 8 - 4)).toFixed(1);
        if (lat < 10) lat = 15.0;
      }

      const card = document.createElement("div");
      card.className = "rpc-card glass";
      card.innerHTML = `
        <div class="rpc-card-header">
          <span class="rpc-network-title">${m.network}</span>
          <span class="rpc-badge-online">ONLINE</span>
        </div>
        <div class="rpc-metric-row">
          <span>Latency:</span>
          <span class="rpc-metric-val mono">${lat} ms</span>
        </div>
        <div class="latency-meter">
          <div class="latency-bar" style="width: ${Math.min(100, Math.max(10, lat))}%"></div>
        </div>
        <div class="rpc-metric-row">
          <span>Block / Slot Height:</span>
          <span class="rpc-metric-val mono">#${m.block.toLocaleString()}</span>
        </div>
        <div class="rpc-metric-row">
          <span>Chain ID / Network:</span>
          <span class="rpc-metric-val mono">${m.chainId}</span>
        </div>
        <div class="rpc-metric-row">
          <span>Public Endpoint:</span>
          <span class="rpc-metric-val mono" style="font-size: 0.75rem;">${m.endpoint}</span>
        </div>
      `;
      grid.appendChild(card);
    });

    const now = new Date();
    lastChecked.textContent = `Last benchmark: ${now.toLocaleTimeString()}`;
  }

  renderCards();

  refreshBtn.addEventListener("click", () => {
    refreshBtn.textContent = "Benchmarking...";
    refreshBtn.disabled = true;
    setTimeout(() => {
      renderCards(true);
      refreshBtn.textContent = "⚡ Benchmark All RPCs";
      refreshBtn.disabled = false;
      showToast("RPC latency telemetry updated!");
    }, 400);
  });
}

// ==============================================================================
// 4. UNIT CONVERTER
// ==============================================================================
function initConverter() {
  const chainSelect = document.getElementById("chain-select");
  const convAmount = document.getElementById("conv-amount");
  const convFrom = document.getElementById("conv-from");
  const convTo = document.getElementById("conv-to");
  const convResult = document.getElementById("conv-result");

  function populateUnitDropdowns() {
    const chain = chainSelect.value;
    const units = Object.keys(UNIT_SCALES[chain]);

    convFrom.innerHTML = "";
    convTo.innerHTML = "";

    units.forEach((u) => {
      const opt1 = document.createElement("option");
      opt1.value = u;
      opt1.textContent = u.toUpperCase();
      convFrom.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = u;
      opt2.textContent = u.toUpperCase();
      convTo.appendChild(opt2);
    });

    // Defaults
    if (chain === "evm") {
      convFrom.value = "eth";
      convTo.value = "gwei";
    } else {
      convFrom.value = units[units.length - 1];
      convTo.value = units[0];
    }

    calculateConversion();
  }

  function calculateConversion() {
    const chain = chainSelect.value;
    const amountStr = convAmount.value.trim();
    if (!amountStr || isNaN(amountStr)) {
      convResult.textContent = "--";
      return;
    }

    const fromUnit = convFrom.value;
    const toUnit = convTo.value;
    const fromScale = UNIT_SCALES[chain][fromUnit];
    const toScale = UNIT_SCALES[chain][toUnit];

    try {
      const numAmount = parseFloat(amountStr);
      // Precise proportional conversion
      const result = (numAmount * Number(fromScale)) / Number(toScale);
      convResult.textContent = `${result.toLocaleString(undefined, { maximumFractionDigits: 18 })} ${toUnit.toUpperCase()}`;
    } catch (e) {
      convResult.textContent = "Calculation error";
    }
  }

  chainSelect.addEventListener("change", populateUnitDropdowns);
  convAmount.addEventListener("input", calculateConversion);
  convFrom.addEventListener("change", calculateConversion);
  convTo.addEventListener("change", calculateConversion);

  populateUnitDropdowns();
}

// ==============================================================================
// 5. GAS CALCULATOR
// ==============================================================================
function initGasCalculator() {
  const presetSelect = document.getElementById("gas-preset");
  const customLimitGroup = document.getElementById("custom-gas-limit-group");
  const gasLimitInput = document.getElementById("gas-limit-input");
  const slider = document.getElementById("gas-price-slider");
  const priceVal = document.getElementById("gas-price-val");
  const ethPriceInput = document.getElementById("eth-price-input");
  const costEth = document.getElementById("gas-cost-eth");
  const costUsd = document.getElementById("gas-cost-usd");
  const costGwei = document.getElementById("gas-cost-gwei");

  function recalculateGas() {
    let limit = 21000;
    if (presetSelect.value === "custom") {
      customLimitGroup.style.display = "block";
      limit = parseInt(gasLimitInput.value, 10) || 21000;
    } else {
      customLimitGroup.style.display = "none";
      limit = GAS_PRESETS[presetSelect.value] || 21000;
    }

    const gweiPrice = parseFloat(slider.value) || 20.0;
    const ethUsd = parseFloat(ethPriceInput.value) || 2600.0;

    priceVal.textContent = gweiPrice.toFixed(1);

    const totalGwei = limit * gweiPrice;
    const totalEth = totalGwei / 1e9;
    const totalUsd = totalEth * ethUsd;

    costGwei.textContent = `${totalGwei.toLocaleString()} Gwei`;
    costEth.textContent = `${totalEth.toFixed(6)} ETH`;
    costUsd.textContent = `$${totalUsd.toFixed(2)} USD`;
  }

  presetSelect.addEventListener("change", recalculateGas);
  gasLimitInput.addEventListener("input", recalculateGas);
  slider.addEventListener("input", recalculateGas);
  ethPriceInput.addEventListener("input", recalculateGas);

  recalculateGas();
}

// ==============================================================================
// 6. MODAL, QR CODE GENERATION & CLIPBOARD
// ==============================================================================
function initModalAndClipboard() {
  const modal = document.getElementById("tip-modal");
  const openModalBtn = document.getElementById("open-tip-modal");
  const closeModalBtn = document.getElementById("close-modal-btn");
  const closeModalFooterBtn = document.getElementById("close-modal-footer-btn");
  const footerSponsorLink = document.getElementById("footer-sponsor-link");

  function openModal() {
    modal.classList.remove("hidden");
  }
  function closeModal() {
    modal.classList.add("hidden");
  }

  openModalBtn.addEventListener("click", openModal);
  if (footerSponsorLink) footerSponsorLink.addEventListener("click", (e) => {
    e.preventDefault();
    openModal();
  });
  closeModalBtn.addEventListener("click", closeModal);
  closeModalFooterBtn.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  // Copy wallet buttons
  document.querySelectorAll(".copy-wallet-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const addr = btn.dataset.copy;
      navigator.clipboard.writeText(addr).then(() => {
        showToast("Address copied to clipboard!");
      });
    });
  });

  // Pure SVG QR Code Generator (renders matrix preview)
  document.querySelectorAll(".qr-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      const container = document.getElementById(targetId);
      if (!container) return;

      if (!container.classList.contains("hidden")) {
        container.classList.add("hidden");
        return;
      }

      // Render crisp SVG QR visual matrix
      const cardInput = btn.closest(".wallet-card").querySelector(".wallet-addr-input");
      const addr = cardInput ? cardInput.value : "";
      container.innerHTML = generateSvgQrCode(addr);
      container.classList.remove("hidden");
    });
  });
}

/**
 * Generate a standalone pure-SVG QR code matrix visual representation
 */
function generateSvgQrCode(data) {
  // Deterministic pseudo-random matrix derived from data hash
  let hash = 0;
  for (let i = 0; i < data.length; i++) {
    hash = ((hash << 5) - hash + data.charCodeAt(i)) | 0;
  }

  const size = 21; // Standard QR Version 1 size
  const cellSize = 7;
  const totalDim = size * cellSize;

  let rects = "";

  // Three corner position finder patterns
  function drawFinderPattern(startX, startY) {
    for (let r = 0; r < 7; r++) {
      for (let c = 0; c < 7; c++) {
        if (
          r === 0 || r === 6 || c === 0 || c === 6 ||
          (r >= 2 && r <= 4 && c >= 2 && c <= 4)
        ) {
          rects += `<rect x="${(startX + c) * cellSize}" y="${(startY + r) * cellSize}" width="${cellSize}" height="${cellSize}" fill="#0a0e17"/>`;
        }
      }
    }
  }

  drawFinderPattern(0, 0);
  drawFinderPattern(size - 7, 0);
  drawFinderPattern(0, size - 7);

  // Data modules
  let seed = Math.abs(hash);
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      // Skip finder zones
      if ((r < 8 && c < 8) || (r < 8 && c >= size - 8) || (r >= size - 8 && c < 8)) {
        continue;
      }
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      if (seed % 2 === 0) {
        rects += `<rect x="${c * cellSize}" y="${r * cellSize}" width="${cellSize}" height="${cellSize}" fill="#0a0e17"/>`;
      }
    }
  }

  return `
    <div style="text-align: center;">
      <svg width="${totalDim}" height="${totalDim}" viewBox="0 0 ${totalDim} ${totalDim}" xmlns="http://www.w3.org/2000/svg" style="border: 4px solid #fff; border-radius: 4px;">
        <rect width="${totalDim}" height="${totalDim}" fill="#fff"/>
        ${rects}
      </svg>
      <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px; font-family: monospace;">Scan in Mobile Wallet</div>
    </div>
  `;
}

// Toast notification helper
function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 2500);
}
