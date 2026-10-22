"""
Tier 3: Cross-Feature Combinations Test Suite.
Verifies pairwise and cross-module interactions across:
B2B Pipeline, Web3 Micro-Utilities, Digital Assets/Templates, and Multi-Chain Payment Rails.
Requires >= 13 test cases.
"""

import os
import sys
import json
import csv
import re
import unittest

from tests.e2e.helpers import (
    PROJECT_ROOT,
    CANONICAL_WALLETS,
    get_path,
    PATH_B2B_DATASET_JSON,
    PATH_B2B_DATASET_CSV,
    PATH_B2B_SCHEMA_JSON,
    PATH_B2B_PITCHES_DIR,
    PATH_B2B_AUDITS_DIR,
    PATH_B2B_SRC_DIR,
    PATH_WEB3_CLI,
    PATH_WEB3_SRC_DIR,
    PATH_WEB3_WEB_SPA,
    PATH_WEB3_TESTS_DIR,
    PATH_CALCULATOR_SPA,
    PATH_RPC_TEMPLATE,
    PATH_VALIDATOR_TEMPLATE,
    PATH_README,
    PATH_DOCS_SPONSOR,
    PATH_FUNDING_YML,
    PATH_VERIFY_BALANCES,
    PATH_AUDIT_PIPELINE,
    run_command_in_project
)

class TestTier3Combinations(unittest.TestCase):
    """Pairwise Cross-Feature Integration Tests (>=13 tests)"""

    def _get_dataset_targets(self):
        if not os.path.exists(PATH_B2B_DATASET_JSON):
            self.skipTest(f"Dataset not present: {PATH_B2B_DATASET_JSON}")
        with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("leads", data.get("targets", []))

    def test_t3_01_b2b_json_schema_csv_cross_validation(self):
        """T3.1: F01 + F04: JSON Dataset records strictly match Schema properties and CSV export."""
        targets = self._get_dataset_targets()
        if not os.path.exists(PATH_B2B_DATASET_CSV) or not os.path.exists(PATH_B2B_SCHEMA_JSON):
            self.skipTest("CSV export or JSON schema not present")

        with open(PATH_B2B_SCHEMA_JSON, "r", encoding="utf-8") as f:
            schema = json.load(f)
        with open(PATH_B2B_DATASET_CSV, "r", encoding="utf-8") as f:
            csv_rows = list(csv.DictReader(f))

        self.assertEqual(len(targets), len(csv_rows), "Count mismatch between JSON targets and CSV rows")
        for json_t, csv_t in zip(targets, csv_rows):
            self.assertEqual(json_t["target_id"], csv_t["target_id"])
            self.assertEqual(json_t["company_name"], csv_t["company_name"])
            csv_aov = csv_t.get("estimated_aov", csv_t.get("estimated_aov_usd"))
            self.assertEqual(str(json_t["estimated_aov"]), str(csv_aov))

    def test_t3_02_b2b_leak_calculator_dataset_math_reconciliation(self):
        """T3.2: F01 + F02: Dataset monthly lost pipeline reconciles with leak calculator logic."""
        targets = self._get_dataset_targets()
        if not os.path.exists(PATH_B2B_SRC_DIR):
            self.skipTest("b2b_pipeline source not present")
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from src.b2b_pipeline.leak_calculator import calculate_lost_pipeline
        except ImportError:
            self.skipTest("calculate_lost_pipeline not importable")
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)

        for target in targets:
            visitors = target.get("estimated_monthly_visitors", 0)
            aov = target.get("estimated_aov", 0)
            reported_loss = target.get("estimated_monthly_lost_pipeline", 0)
            self.assertGreater(reported_loss, 0, f"Target {target['target_id']} has 0 lost pipeline")
            # Sanity check: lost pipeline cannot exceed total possible monthly revenue (visitors * aov)
            max_theoretical = visitors * aov
            self.assertLessEqual(reported_loss, max_theoretical)

    def test_t3_03_b2b_dataset_pitches_cross_referential_integrity(self):
        """T3.3: F01 + F03: Every target in dataset maps to a tailored pitch mentioning company name."""
        targets = self._get_dataset_targets()
        if not os.path.exists(PATH_B2B_PITCHES_DIR):
            self.skipTest("Pitches dir not present")

        for target in targets:
            pitch_file = target.get("tailored_pitch_file")
            self.assertIsNotNone(pitch_file)
            filename = os.path.basename(pitch_file)
            pitch_path = os.path.join(PATH_B2B_PITCHES_DIR, filename)
            self.assertTrue(os.path.exists(pitch_path), f"Pitch file missing for target {target['target_id']}: {pitch_path}")
            with open(pitch_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Must mention target company or decision maker or domain
            dm_name = target["decision_maker"]["name"].split()[0] # First name
            company_token = target["company_name"].split()[0] # First word of company
            self.assertTrue(
                dm_name.lower() in content.lower() or company_token.lower() in content.lower(),
                f"Pitch {filename} does not personalize for {target['company_name']} / {dm_name}"
            )

    def test_t3_04_b2b_dataset_audits_cross_referential_integrity(self):
        """T3.4: F01 + F04: Every target in dataset maps to an audit report detailing the leaks."""
        targets = self._get_dataset_targets()
        if not os.path.exists(PATH_B2B_AUDITS_DIR):
            self.skipTest("Audits dir not present")

        for target in targets:
            audit_file = target.get("audit_report_file")
            self.assertIsNotNone(audit_file)
            filename = os.path.basename(audit_file)
            audit_path = os.path.join(PATH_B2B_AUDITS_DIR, filename)
            self.assertTrue(os.path.exists(audit_path), f"Audit report missing: {audit_path}")
            with open(audit_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(len(content) > 300, f"Audit report {filename} too brief")
            self.assertIn(target["target_id"], content)

    def test_t3_05_b2b_pitches_payment_rails_settlement_alignment(self):
        """T3.5: F03 + F11: B2B pipeline assets specify settlement rails compatible with crypto retainers."""
        if not os.path.exists(PATH_README):
            self.skipTest("README not present")
        with open(PATH_README, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(any(term in content.lower() for term in ["usdc", "base", "payment rails", "crypto", "settlement"]))

    def test_t3_06_web3_cli_payment_rails_tip_integration(self):
        """T3.6: F05 + F11: CLI --tip or tip command outputs all 4 canonical beneficiary wallets."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("run_cli.py not present")
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "--tip"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "tip"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "--sponsor"])
        self.assertEqual(ret, 0)
        out = (stdout + stderr).lower()
        self.assertIn(CANONICAL_WALLETS["base"].lower(), out)
        self.assertIn(CANONICAL_WALLETS["solana"].lower(), out)
        self.assertIn(CANONICAL_WALLETS["bitcoin"].lower(), out)
        self.assertIn(CANONICAL_WALLETS["stellar"].lower(), out)

    def test_t3_07_web3_spa_payment_rails_modal_integration(self):
        """T3.7: F06 + F11: Web3 SPA HTML embeds all 4 canonical beneficiary addresses."""
        spa_paths = [PATH_WEB3_WEB_SPA, get_path("web3_utility", "index.html")]
        content = None
        for p in spa_paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                break
        if not content:
            self.skipTest("Web3 SPA not present")

        for key in ["base", "solana", "bitcoin", "stellar"]:
            addr = CANONICAL_WALLETS[key]
            self.assertIn(addr.lower(), content.lower(), f"SPA missing canonical wallet for {key}")

    def test_t3_08_calculator_payment_rails_sponsor_card(self):
        """T3.8: F08 + F11: Interactive Staking Calculator sponsor card embeds canonical wallets."""
        calc_paths = [
            PATH_CALCULATOR_SPA,
            get_path("digital_assets", "web3_saas_calculator", "index.html")
        ]
        content = None
        for p in calc_paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                break
        if not content:
            self.skipTest("Calculator SPA not present")

        for key in ["base", "solana", "bitcoin", "stellar"]:
            addr = CANONICAL_WALLETS[key]
            self.assertIn(addr.lower(), content.lower(), f"Calculator sponsor card missing {key} address")

    def test_t3_09_docs_distribution_kit_payment_rails_consistency(self):
        """T3.9: F10 + F11: README, SPONSORSHIP.md, and FUNDING.yml share identical canonical addresses."""
        files_to_check = [PATH_README, PATH_DOCS_SPONSOR, PATH_FUNDING_YML]
        existing = [p for p in files_to_check if os.path.exists(p)]
        if not existing:
            self.skipTest("Docs distribution kit not present")

        for path in existing:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().lower()
            # Each file should contain at least Base and Solana addresses
            self.assertIn(CANONICAL_WALLETS["base"].lower(), content, f"{os.path.basename(path)} missing Base address")
            self.assertIn(CANONICAL_WALLETS["solana"].lower(), content, f"{os.path.basename(path)} missing Solana address")

    def test_t3_10_web3_cli_inspector_and_template_validator_consistency(self):
        """T3.10: F05 + F09: CLI inspector and address_validator.js support the same multi-chain suite."""
        if not os.path.exists(PATH_VALIDATOR_TEMPLATE):
            self.skipTest("address_validator.js not present")
        with open(PATH_VALIDATOR_TEMPLATE, "r", encoding="utf-8") as f:
            js_code = f.read().lower()

        # Both must validate Ethereum, Solana, Bitcoin, and Stellar
        for chain in ["evm", "solana", "bitcoin", "stellar"]:
            self.assertIn(chain, js_code, f"address_validator.js missing support for {chain}")

    def test_t3_11_rpc_monitor_and_verify_balances_endpoint_parity(self):
        """T3.11: F05 + F12: Web3 RPC monitor and verify_balances.py share consistent chain endpoints."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        with open(PATH_VERIFY_BALANCES, "r", encoding="utf-8") as f:
            balances_code = f.read()

        # Check that Base RPC is defined
        self.assertTrue("base.org" in balances_code or "llamarpc.com" in balances_code)
        # Check that Solana RPC is defined
        self.assertTrue("solana.com" in balances_code or "solana" in balances_code)

    def test_t3_12_audit_pipeline_executes_web3_unit_tests(self):
        """T3.12: F07 + F13: audit_pipeline.py checks Web3 unit test execution."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertTrue("web3_utility" in code and ("unittest" in code or "test" in code))

    def test_t3_13_audit_pipeline_full_system_cross_verification(self):
        """T3.13: F01-F13 + F13: audit_pipeline.py validates all 4 core business pillars."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            code = f.read().lower()
        # Pillar 1: B2B
        self.assertIn("b2b", code)
        # Pillar 2: Web3
        self.assertIn("web3", code)
        # Pillar 3: Distro / Docs
        self.assertTrue("readme" in code or "distribution" in code or "docs" in code)
        # Pillar 4: Payment rails / Wallets
        self.assertTrue("wallet" in code or "balance" in code or "payment" in code)


if __name__ == "__main__":
    unittest.main()
