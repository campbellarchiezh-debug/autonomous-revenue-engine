# ⚡ 60-Second Setup & Deployment Guide

This guide gets the **Autonomous Revenue Engine** running locally or in production within 60 seconds.

---

## 🚀 Quickstart: Zero Prerequisites, Zero Installs

Because the entire engine is architected with a **Zero External Dependencies** standard, you do not need `npm`, `pip install`, virtual environments, or Node.js. 

### Prerequisites
- **Python 3.9+** (Native standard library)
- Any modern web browser (Chrome, Firefox, Safari, Edge)

Verify your Python version:
```bash
python3 --version
# Expected: Python 3.9.0 or higher
```

---

## 1. Local Interactive Exploration

### A. Run the Web3 CLI Suite
Run multi-chain address safety inspection, RPC latency benchmarking, and fee conversions directly:
```bash
# Inspect Base EVM address for EIP-55 checksumming and poisoning
python3 web3_utility/run_cli.py inspect 0xef5766253e2d92e530e301ac22dcb8de78e89c55

# Inspect Solana Base58 address
python3 web3_utility/run_cli.py inspect 3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp

# Benchmark RPC latency across multi-chain endpoints (mock mode for offline/CI)
python3 web3_utility/run_cli.py monitor --offline

# Convert Wei / Gwei / Ether with high-precision decimal math
python3 web3_utility/run_cli.py convert 1000000000000000000 wei ether
```

### B. Launch the Web Applications
Launch the built-in zero-dependency Python web server:
```bash
# Serve the repository root
python3 -m http.server 8080
```
Open your browser to:
- **Turnkey Web3 Staking & Node ROI Calculator SPA**:  
  `http://localhost:8080/digital_assets/web3_saas_calculator/index.html`
- **Web3 Micro-Utility Web SPA**:  
  `http://localhost:8080/web3_utility/src/web/index.html`

*Note: Both SPAs can also be opened directly via `file://` protocol by double-clicking the `index.html` files!*

---

## 2. Developer Code Templates

Drop-in templates are located in `templates/`:

### A. Multi-Chain RPC Failover Client (`templates/rpc_client_template.py`)
Run directly from terminal:
```bash
# Query block height with automatic failover (mock mode)
python3 templates/rpc_client_template.py --chain base --method eth_blockNumber --mock

# Run health check across RPC endpoint pool
python3 templates/rpc_client_template.py --health --mock

# View embedded beneficiary wallets
python3 templates/rpc_client_template.py --wallets
```

Import into your own Python projects:
```python
from templates.rpc_client_template import RpcClient, RpcConfig

client = RpcClient(RpcConfig(chain="base", timeout=5.0))
block_number = client.get_block_number()
print(f"Latest Base Block: {block_number}")
```

### B. Multi-Chain Address Validator (`templates/address_validator.js`)
Use in browser or vanilla JavaScript:
```html
<script src="templates/address_validator.js"></script>
<script>
  const result = AddressValidator.validate("0xef5766253e2d92e530e301ac22dcb8de78e89c55");
  console.log("Valid EVM:", result.valid, result.checksumAddress);

  // Address poisoning and zero-width injection check
  const safety = AddressValidator.scanSecurity("0x...", "0xReference...");
  console.log("Safe from poisoning:", safety.safe);
</script>
```

---

## 3. Master Integrity & Balance Verification

Run the automated verification scripts:

### A. Pipeline Integrity Audit
Validates all 15 B2B leads, pitch word counts, Web3 utilities, and wallet integrity:
```bash
python3 audit_pipeline.py
```
*Expected: Exit code 0, 100% check pass, outputs `audit_report.json`.*

### B. On-Chain Balance Polling Script
Polls public blockchain RPCs or runs offline simulation:
```bash
# Simulated / Offline verification (CI-safe)
python3 verify_balances.py --simulate --json

# Live verification (queries Base, Solana, Bitcoin, Stellar RPCs)
python3 verify_balances.py --chain all
```

---

## 4. Production Deployment

### Static Hosting (GitHub Pages, Cloudflare Pages, Netlify, Vercel)
Because both web applications require **zero compilation steps**, you can deploy them directly as static assets:
1. **GitHub Pages**:
   - Go to Repository **Settings** -> **Pages**.
   - Source: Deploy from branch `main` -> folder `/` (root) or `/digital_assets/web3_saas_calculator`.
2. **Netlify / Vercel**:
   - Set Build Command: *(leave blank)*
   - Set Publish Directory: `digital_assets/web3_saas_calculator/` (or root `.`).

### Docker Deployment
Run via minimal Alpine Nginx:
```dockerfile
FROM nginx:alpine
COPY digital_assets/web3_saas_calculator/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```
Build and run:
```bash
docker build -t web3-staking-calculator .
docker run -d -p 80:80 web3-staking-calculator
```

---

## 5. Support & Sponsorship Rails

All components embed non-custodial direct payment endpoints:
- **Base EVM**: `0xef5766253e2d92e530e301ac22dcb8de78e89c55`
- **Solana**: `3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp`
- **Bitcoin**: `bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e`
- **Stellar**: `GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA`
