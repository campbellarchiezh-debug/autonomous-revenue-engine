# Changelog

All notable changes to the **Autonomous Revenue Engine** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-21

### Added
- **Pillar 1: B2B Lead Sourcing & Audit Diagnostic Pipeline**:
  - High-AOV commercial dataset containing 15 fully validated enterprise targets across 5 service verticals (Luxury Roofing, Cosmetic Dentistry, Commercial HVAC, High-End Solar, Enterprise IT & Managed Services).
  - Algorithmic Conversion Leak Diagnostic Engine (`leak_calculator.py`) calculating estimated monthly lost pipeline revenue based on mobile bounce rates, page load latency, broken CTAs, and missing form validation.
  - 15 tailored 90-second video walkthrough pitch scripts and companion cold-email outreach templates with word count constraints (160–260 words).
  - Formal JSON Schema validation (`b2b_leads_schema.json`) and automated CRM CSV export.

- **Pillar 2: Production-Grade Web3 Micro-Utility & Developer Tools**:
  - Pure-Python zero-dependency CLI utility suite (`run_cli.py`) supporting address safety inspection, RPC latency benchmarking, and crypto unit/gas fee conversions.
  - Multi-chain Address Inspector module (`inspector.py`) implementing pure-Python Keccak-256 EIP-55 checksumming, Solana Base58 decoding, Bitcoin Bech32/Bech32m Taproot polymod validation, and Stellar StrKey CRC16 verification.
  - Address poisoning, zero-width Unicode injection, and mixed-script homoglyph safety scanners.
  - RPC Health Monitor (`rpc_monitor.py`) supporting failover endpoint benchmarking, block height tracking, and offline deterministic simulation.
  - Unit and Gas Fee Calculator (`converter.py`) utilizing `decimal.Decimal` precision for Wei/Gwei/Eth, Lamports/SOL, Satoshis/BTC, and Stroops/XLM.
  - Zero-dependency client-side Web SPA (`web3_utility/src/web/index.html`) running cleanly from `file://` or static web servers.

- **Pillar 3: Turnkey Digital Assets & Distribution Kits**:
  - Turnkey Web3 Staking & Validator ROI Modeler SPA (`digital_assets/web3_saas_calculator/index.html`):
    - Interactive parameter sliders for capital, APR yield, compounding frequency, validator fee split, monthly OpEx, MEV boost, and asset growth.
    - Zero-dependency dynamic pure-SVG vector charting engine rendering area charts, gridlines, axis labels, and hover tooltips.
    - Sensitivity scenario matrix (Bear, Baseline, Bull) and annual amortization schedule table.
    - Pro/Sponsor donation card embedding verified multi-chain beneficiary payment rails with 1-click clipboard copying.
  - Turnkey Python RPC Failover Client template (`templates/rpc_client_template.py`) with adaptive SSL, retry backoff with jitter, and offline mock support.
  - Universal vanilla JavaScript Address Validator module (`templates/address_validator.js`) supporting UMD, CommonJS, and ES6 exports.

- **Pillar 4: Multi-Chain Payment Rails & Programmatic Telemetry**:
  - Embedded non-custodial crypto payment endpoints across Base EVM, Solana, Bitcoin, and Stellar.
  - Standalone programmatic verification script `verify_balances.py` with multi-chain RPC polling and offline simulation.
  - Master pipeline integrity audit script `audit_pipeline.py` verifying all 15 B2B leads, pitches, Web3 utilities, and wallet integrity.

- **Distribution & Documentation Kit**:
  - Flagship GitHub-grade `README.md` with visual architecture overview, badges, quickstart, and embedded donation rails.
  - `LICENSE` (MIT Permissive License).
  - `SETUP.md` (60-second setup and multi-platform deployment guide).
  - `CONTRIBUTING.md` (Code of conduct, zero-dependency philosophy, PR workflow).
  - `docs/PREVIEW.md` (ASCII UI wireframes, terminal simulations, and architecture flow).
  - `docs/ARCHITECTURE.md` (Technical deep-dive on zero-dependency engineering, cryptographic algorithms, and failover mechanics).
  - `docs/SPONSORSHIP.md` (Detailed crypto donation guide with explorer links).
  - `.github/FUNDING.yml` (GitHub Sponsors and custom cryptocurrency endpoints).
