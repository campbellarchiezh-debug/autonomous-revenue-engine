# Contributing to Autonomous Revenue Engine

Thank you for your interest in contributing to the **Autonomous Revenue Engine**! This project is an open-source, zero-dependency multi-pillar system spanning B2B diagnostic outreach pipelines, developer Web3 micro-utilities, and turnkey financial modeling software assets.

---

## 1. Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors, regardless of experience level, background, or identity. Please treat everyone with respect, kindness, and professional courtesy.

---

## 2. Core Architectural Philosophy: Zero External Dependencies

Before submitting code, please understand our strict **Zero External Dependencies Mandate**:

1. **Python Standard Library Only**:
   - All Python code (`src/`, `web3_utility/`, `templates/`, `verify_balances.py`, `audit_pipeline.py`) must execute cleanly using only the **Python 3.9+ standard library** (`urllib.request`, `json`, `hashlib`, `ssl`, `decimal`, `time`, `re`, `argparse`, `sys`, etc.).
   - Do **NOT** add third-party pip dependencies (such as `requests`, `web3.py`, `pydantic`, `pandas`, `eth-account`).
   - Pure-Python cryptographic primitives (Keccak-256, Bech32/Bech32m, Base58, Base32 CRC16) ensure 100% portability, air-gapped security, and zero supply chain vulnerabilities.

2. **Vanilla Web Technologies Only**:
   - All frontend applications (`digital_assets/web3_saas_calculator/`, `web3_utility/src/web/`) must be written in vanilla **HTML5, CSS3, and ES6 JavaScript**.
   - Do **NOT** introduce Node.js build pipelines, `npm`, Webpack, Babel, Vite, React, or external CDN dependencies.
   - Applications must function directly from `file://` or via `python3 -m http.server`.
   - Dynamic charts must use native pure SVG math without external charting libraries.

3. **Deterministic Offline Testing**:
   - Because network environments may be air-gapped or sandboxed, all network-facing tools (RPC monitors, balance verifiers) must support an offline/mock mode (`--simulate` or `--mock`) for continuous integration.

---

## 3. Development Workflow

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/your-username/autonomous_revenue_engine.git
   cd autonomous_revenue_engine
   ```

2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Verify Existing Tests**:
   Before modifying code, confirm that the existing test suites pass:
   ```bash
   # Test Web3 utility suites
   python3 -m unittest discover -s web3_utility/tests

   # Test master audit pipeline
   python3 audit_pipeline.py

   # Test code templates
   python3 templates/rpc_client_template.py --mock --health
   ```

4. **Implement Your Changes**:
   - Write clean, well-documented code adhering to PEP 8 (Python) and standard ES6 conventions (JavaScript).
   - Add unit tests for every new function, class, or edge case.

5. **Run Verification**:
   - Ensure all files compile without syntax errors:
     ```bash
     python3 -m py_compile templates/*.py
     ```
   - Ensure `audit_pipeline.py` returns exit code 0.

6. **Submit a Pull Request**:
   - Provide a clear, detailed PR description outlining:
     - The problem being solved or feature added
     - Verification commands executed and test outputs
     - Confirmation of zero new external dependencies

---

## 4. Beneficiary Wallets & Non-Custodial Payment Rails

When editing documentation, templates, or UI cards, do not modify or tamper with the canonical beneficiary wallet addresses:
- **Base EVM**: `0xef5766253e2d92e530e301ac22dcb8de78e89c55`
- **Solana**: `3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp`
- **Bitcoin**: `bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e`
- **Stellar**: `GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA`

---

## 5. Security Vulnerability Disclosure

If you discover a security vulnerability or address spoofing exploit, please **do not** open a public issue. Instead, submit a security advisory or email the maintainers directly.
