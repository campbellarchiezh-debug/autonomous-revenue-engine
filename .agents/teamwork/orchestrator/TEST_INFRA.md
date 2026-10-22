# E2E Test Infra: Autonomous Revenue Engine

## Test Philosophy
- Opaque-box, requirement-driven: Directly derived from `ORIGINAL_REQUEST.md`.
- No dependency on implementation internals. Exercises the system via standard entrypoints (CLI commands, JSON/CSV dataset files, Python scripts `verify_balances.py` and `audit_pipeline.py`, web asset files, and markdown documents).
- Methodology: 4-Tier Systematic Testing:
  - **Tier 1 - Feature Coverage**: Equivalence class representatives in isolation (>=5 tests per feature).
  - **Tier 2 - Boundary & Corner Cases**: Edge cases, invalid inputs, empty sets, oversized inputs, malformed addresses, corrupt JSON, offline network simulation (>=5 tests per feature).
  - **Tier 3 - Cross-Feature Combinations**: Pairwise interactions across B2B data, Web3 utilities, templates, and payment verification.
  - **Tier 4 - Real-World Application Scenarios**: End-to-end user workflows (e.g., executing full audit verification, running offline balance simulation, validating B2B cold-email campaign ready assets, checking web UI standalone rendering).

## Feature Inventory & Test Matrix
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | F01: B2B Lead Sourcing Dataset | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 2 | F02: Conversion Leak Diagnostic Engine | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 3 | F03: 15 Tailored Pitch Scripts | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 4 | F04: B2B Schemas, Formats & Export | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 5 | F05: Web3 Micro-Utility CLI Suite | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 6 | F06: Web3 Micro-Utility Web SPA | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 7 | F07: Web3 Micro-Utility Test Suites | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 8 | F08: Interactive Staking Calculator | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 9 | F09: Turnkey Code Templates | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 10 | F10: Distribution Kit & Docs | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 11 | F11: Multi-Chain Payment Rails Embedding | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |
| 12 | F12: Live Programmatic Balance Auditing | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |
| 13 | F13: Pipeline Integrity Verification | ORIGINAL_REQUEST §Acceptance | 5 | 5 | ✓ |

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Complete Cold-Outreach Campaign Readiness (15 leads imported, verified pitch word counts & revenue leakage math) | F01, F02, F03, F04 | High |
| 2 | Web3 Security Inspection & Tipping Flow (malicious address detection, EIP-55 checksumming, beneficiary tip display) | F05, F06, F11 | High |
| 3 | Developer Onboarding & Turnkey Deployment (standalone calculator preview, code template execution, docs checklist) | F08, F09, F10 | Medium |
| 4 | Offline Multi-Chain Balance Auditing (`verify_balances.py --simulate --json`) | F11, F12 | Medium |
| 5 | Master Acceptance Pipeline Audit (`python3 audit_pipeline.py`) exit code 0 and valid report | F01-F13 | High |

## Test Architecture
- Test runner location: `tests/e2e/run_e2e_tests.py`
- Invocation: `python3 tests/e2e/run_e2e_tests.py [--tier 1|2|3|4|all]`
- Pass/Fail Semantics: Exit code 0 only if 100% of asserted tests pass. Structured terminal summary and test results output.
- Zero external dependencies: Uses Python `unittest` standard library.
