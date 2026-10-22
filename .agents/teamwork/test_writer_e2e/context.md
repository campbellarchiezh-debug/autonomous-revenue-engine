# Test Writer Assignment: E2E Testing Track (Opaque-Box Requirement-Driven Test Suite)
Working Directory: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/test_writer_e2e
Project Root: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine
Original Request: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/ORIGINAL_REQUEST.md
Test Infrastructure Specification: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/orchestrator/TEST_INFRA.md
Project Specification: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/orchestrator/PROJECT.md

## Exclusive Write Ownership
You exclusively own:
- `tests/e2e/` (test runner, test cases Tiers 1-4)
- `TEST_READY.md` (publish when test suite is complete)

## Deliverables Required
1. `tests/e2e/run_e2e_tests.py`: Master test runner supporting `--tier 1|2|3|4|all`, verbose logging, and structured summary table. Exit code 0 if all tests pass.
2. `tests/e2e/test_tier1_features.py`: Tier 1 Feature Coverage (>=5 test cases per feature for F01-F13, total >=65 tests) testing features in isolation.
3. `tests/e2e/test_tier2_boundaries.py`: Tier 2 Boundary & Corner Cases (>=5 test cases per feature, total >=65 tests) testing invalid inputs, malformed addresses, corrupt JSON, extreme values, offline modes.
4. `tests/e2e/test_tier3_combinations.py`: Tier 3 Cross-Feature Combinations (pairwise interactions across B2B data, Web3 tools, templates, payment rails, >=13 tests).
5. `tests/e2e/test_tier4_scenarios.py`: Tier 4 Real-World Application Scenarios (5 realistic end-to-end user workflows).
6. Total test case count: >= 148 test cases.
7. `TEST_READY.md`: Published at project root once the suite is fully written and runnable.
8. Verification: Ensure all tests load cleanly with `python3 -m unittest discover -s tests/e2e`. Document in handoff.md.
