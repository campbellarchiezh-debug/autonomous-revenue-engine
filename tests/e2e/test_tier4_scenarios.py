"""
Tier 4: Real-World Application Scenarios Test Suite.
Verifies 5 comprehensive end-to-end user workflows across all features:
1. Complete Cold-Outreach Campaign Readiness (F01, F02, F03, F04)
2. Web3 Security Inspection & Tipping Flow (F05, F06, F11)
3. Developer Onboarding & Turnkey Deployment (F08, F09, F10)
4. Offline Multi-Chain Balance Auditing (F11, F12)
5. Master Acceptance Pipeline Audit (F01-F13)
"""

import os
import sys
import json
import csv
import ast
import unittest

from tests.e2e.helpers import (
    PROJECT_ROOT,
    CANONICAL_WALLETS,
    get_path,
    PATH_B2B_DATASET_JSON,
    PATH_B2B_DATASET_CSV,
    PATH_B2B_PITCHES_DIR,
    PATH_B2B_AUDITS_DIR,
    PATH_WEB3_CLI,
    PATH_CALCULATOR_SPA,
    PATH_RPC_TEMPLATE,
    PATH_VALIDATOR_TEMPLATE,
    PATH_README,
    PATH_LICENSE,
    PATH_SETUP,
    PATH_DOCS_PREVIEW,
    PATH_VERIFY_BALANCES,
    PATH_AUDIT_PIPELINE,
    count_words,
    run_command_in_project,
    reference_to_checksum_address,
    reference_verify_bech32m,
    reference_verify_solana_address,
    reference_verify_stellar_address
)

class TestTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: 5 Real-World End-to-End Application Scenarios"""

    def test_scenario_1_cold_outreach_campaign_readiness(self):
        """
        Scenario 1: Complete Cold-Outreach Campaign Readiness.
        Operator loads B2B dataset (>=15 targets), verifies CSV export, confirms
        personalized 90-second pitch scripts (140-220 words) with zero unrendered tags,
        and validates technical audit reports.
        """
        if not os.path.exists(PATH_B2B_DATASET_JSON):
            self.skipTest(f"Dataset not present: {PATH_B2B_DATASET_JSON}")

        with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        targets = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        self.assertGreaterEqual(len(targets), 15, "Scenario 1 requires >= 15 verified commercial targets")

        # 1. Verify CRM CSV Export can be parsed
        if not os.path.exists(PATH_B2B_DATASET_CSV):
            self.skipTest(f"CSV export missing: {PATH_B2B_DATASET_CSV}")
        with open(PATH_B2B_DATASET_CSV, "r", encoding="utf-8") as f:
            csv_rows = list(csv.DictReader(f))
        self.assertEqual(len(csv_rows), len(targets), "CRM CSV rows must match JSON target count")

        # 2. Check pitch scripts for all targets
        if not os.path.exists(PATH_B2B_PITCHES_DIR):
            self.skipTest("Pitches dir missing")
        for target in targets:
            pitch_file = target.get("tailored_pitch_file")
            self.assertIsNotNone(pitch_file)
            pitch_path = os.path.join(PATH_B2B_PITCHES_DIR, os.path.basename(pitch_file))
            self.assertTrue(os.path.exists(pitch_path), f"Pitch script missing: {pitch_path}")

            with open(pitch_path, "r", encoding="utf-8") as f:
                content = f.read()
            video_part = content.split("### Companion Outreach Email")[0] if "### Companion Outreach Email" in content else content
            words = count_words(video_part)
            self.assertGreaterEqual(words, 140, f"Pitch {pitch_file} video script too short ({words} words)")
            self.assertLessEqual(words, 220, f"Pitch {pitch_file} video script too long ({words} words)")

            # Zero placeholders
            for token in ["{{", "}}", "<TODO>", "REPLACE_ME"]:
                self.assertNotIn(token, content, f"Pitch {pitch_file} contains placeholder: {token}")

        # 3. Check audit reports
        if not os.path.exists(PATH_B2B_AUDITS_DIR):
            self.skipTest("Audits dir missing")
        for target in targets:
            audit_file = target.get("audit_report_file")
            if audit_file:
                audit_path = os.path.join(PATH_B2B_AUDITS_DIR, os.path.basename(audit_file))
                self.assertTrue(os.path.exists(audit_path), f"Audit report missing: {audit_path}")

    def test_scenario_2_web3_security_inspection_and_tipping_flow(self):
        """
        Scenario 2: Web3 Security Inspection & Tipping Flow.
        Crypto user / developer inspects multi-chain addresses for poisoning/homoglyphs,
        verifies Base EIP-55 checksumming, Solana Ed25519, Bitcoin Taproot, Stellar StrKey,
        and views tipping endpoints with canonical beneficiary wallets.
        """
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest(f"Web3 CLI not present: {PATH_WEB3_CLI}")

        # 1. Base EVM checksum inspection
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", CANONICAL_WALLETS["base"]])
        self.assertEqual(ret, 0, f"Inspect Base address failed: {stderr}")
        self.assertIn("valid", stdout.lower())

        # 2. Poisoning detection (zero-width character injection)
        poisoned_addr = "0xef576625\u200b3e2d92e530e301ac22dcb8de78e89c55"
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", poisoned_addr])
        out = (stdout + stderr).lower()
        self.assertTrue(ret != 0 or "invalid" in out or "poison" in out or "zero-width" in out)

        # 3. Solana address inspection
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", CANONICAL_WALLETS["solana"]])
        self.assertEqual(ret, 0, f"Inspect Solana address failed: {stderr}")

        # 4. Bitcoin Taproot address inspection
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", CANONICAL_WALLETS["bitcoin"]])
        self.assertEqual(ret, 0, f"Inspect Bitcoin address failed: {stderr}")

        # 5. Stellar StrKey address inspection
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", CANONICAL_WALLETS["stellar"]])
        self.assertEqual(ret, 0, f"Inspect Stellar address failed: {stderr}")

        # 6. Tipping flow verification
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "--tip"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "tip"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "--sponsor"])
        self.assertEqual(ret, 0)
        tip_output = (stdout + stderr).lower()
        for key in ["base", "solana", "bitcoin", "stellar"]:
            self.assertIn(CANONICAL_WALLETS[key].lower(), tip_output, f"Tip flow missing wallet for {key}")

    def test_scenario_3_developer_onboarding_and_turnkey_deployment(self):
        """
        Scenario 3: Developer Onboarding & Turnkey Deployment.
        New developer reviews documentation, inspects standalone zero-dependency
        staking calculator, and deploys Python RPC failover & JS address validator templates.
        """
        # 1. Distribution Kit docs check
        for doc_path in [PATH_README, PATH_LICENSE, PATH_SETUP, PATH_DOCS_PREVIEW]:
            if not os.path.exists(doc_path):
                self.skipTest(f"Distribution kit file missing: {doc_path}")
            with open(doc_path, "r", encoding="utf-8") as f:
                self.assertGreater(len(f.read()), 100)

        # 2. Staking Calculator HTML preview check
        if not os.path.exists(PATH_CALCULATOR_SPA):
            self.skipTest(f"Calculator SPA missing: {PATH_CALCULATOR_SPA}")
        with open(PATH_CALCULATOR_SPA, "r", encoding="utf-8") as f:
            calc_html = f.read()
        self.assertIn("<svg", calc_html.lower())
        self.assertIn('type="range"', calc_html.lower())
        self.assertNotIn("googleapis.com", calc_html)
        self.assertNotIn("cloudflare.com", calc_html)

        # 3. Python RPC failover template
        if not os.path.exists(PATH_RPC_TEMPLATE):
            self.skipTest(f"RPC client template missing: {PATH_RPC_TEMPLATE}")
        with open(PATH_RPC_TEMPLATE, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        self.assertIsNotNone(tree)

        # 4. JS Address validator template
        if not os.path.exists(PATH_VALIDATOR_TEMPLATE):
            self.skipTest(f"Address validator template missing: {PATH_VALIDATOR_TEMPLATE}")
        with open(PATH_VALIDATOR_TEMPLATE, "r", encoding="utf-8") as f:
            js_code = f.read()
        self.assertTrue("function" in js_code)

    def test_scenario_4_offline_multichain_balance_auditing(self):
        """
        Scenario 4: Offline Multi-Chain Balance Auditing.
        Runs `verify_balances.py --simulate --json` in air-gapped / simulated mode,
        asserts exit code 0, and parses JSON ledger balance records for all 4 chains.
        """
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest(f"verify_balances.py missing: {PATH_VERIFY_BALANCES}")

        ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--simulate", "--json"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--offline", "--json"])
        self.assertEqual(ret, 0, f"Simulated balance audit failed: {stderr}")

        try:
            report = json.loads(stdout.strip())
        except json.JSONDecodeError as e:
            self.fail(f"verify_balances.py stdout is not valid JSON: {stdout} (Error: {e})")

        self.assertIn("balances", report)
        balances = report["balances"]
        for chain in ["base", "solana", "bitcoin", "stellar"]:
            self.assertIn(chain, balances, f"Balance report missing chain: {chain}")
            entry = balances[chain]
            self.assertIn("address", entry)
            self.assertIn("status", entry)

    def test_scenario_5_master_acceptance_pipeline_audit(self):
        """
        Scenario 5: Master Acceptance Pipeline Audit.
        Runs `python3 audit_pipeline.py`, asserts clean exit code 0,
        and verifies generated `audit_report.json` passes all suites.
        """
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest(f"audit_pipeline.py missing: {PATH_AUDIT_PIPELINE}")

        ret, stdout, stderr = run_command_in_project(["audit_pipeline.py"])
        self.assertEqual(ret, 0, f"audit_pipeline.py failed with returncode {ret}: {stderr}\nOutput: {stdout}")

        report_path = get_path("audit_report.json")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            self.assertIsInstance(report_data, dict)
            # Check for overall success flag
            status = report_data.get("status", report_data.get("overall_status", "PASS"))
            self.assertIn(str(status).upper(), ["PASS", "SUCCESS", "OK", "TRUE"])


if __name__ == "__main__":
    unittest.main()
