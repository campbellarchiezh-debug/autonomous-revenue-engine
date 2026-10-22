# Worker Assignment: Milestone 2 (Web3 Micro-Utility & Developer Tools)
Working Directory: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/worker_m2
Project Root: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine
Original Request: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/ORIGINAL_REQUEST.md
Project Specification: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/orchestrator/PROJECT.md
Survey Handoff Reference: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/explorer_survey_2/handoff.md

## Exclusive Write Ownership
You exclusively own:
- `web3_utility/` (all contents: `run_cli.py`, `src/`, `tests/`)

## Deliverables Required
1. `web3_utility/src/inspector.py`: Pure-Python zero-dependency multi-chain address inspector.
   - Base EVM: Keccak-256 and EIP-55 checksum validation.
   - Bitcoin: BIP-350 Bech32m Taproot validation (supporting `bc1p...`).
   - Solana: Base58 public key decoding to 32 bytes (Ed25519).
   - Stellar: Base32 StrKey decoding and CRC16-XMODEM checksum verification.
   - Security checks: Zero-width invisible unicode exploit detection, Cyrillic/Greek homoglyph detection, vanity address poisoning heuristics.
2. `web3_utility/src/rpc_monitor.py`: RPC health and latency benchmarking engine for Base, Ethereum, Solana, Bitcoin, Stellar.
   - Evaluates latency, block height, sync status, chain ID.
   - Multi-endpoint fallback hierarchy with adaptive SSL context.
   - Built-in offline/mock mode for deterministic CI/sandbox testing.
3. `web3_utility/src/converter.py`: Exact cryptocurrency unit and gas fee calculator across EVM (wei/gwei/eth), Solana (lamports/sol), Bitcoin (satoshis/btc), Stellar (stroops/xlm).
4. `web3_utility/run_cli.py`: Standalone CLI tool with commands: `inspect`, `monitor`, `convert`, `--tip`/`--sponsor` displaying user beneficiary wallets.
5. `web3_utility/src/web/`: Standalone zero-dependency Web SPA (`index.html`, `style.css`, `app.js`).
   - Clean, modern, responsive developer UI for inspector, RPC latency monitor, and unit converter.
   - Interactive payment/tipping modal with QR code rendering and beneficiary wallets.
6. `web3_utility/tests/`: Comprehensive pure-Python `unittest` test suite (`test_inspector.py`, `test_rpc_monitor.py`, `test_converter.py`, `test_cli.py`).
7. Verification: Run `python3 -m unittest discover -s web3_utility/tests` and ensure 100% pass. Document in handoff.md.
