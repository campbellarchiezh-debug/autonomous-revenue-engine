#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for audit_pipeline.py (Milestone 4).
Authored by: Challenger 1 (challenger_m4_1).

Empirically verifies:
- Draft-07 schema validator against invalid structures & edge cases
- Cryptographic address verification (EIP-55, Solana Base58, Bitcoin Bech32m, Stellar StrKey)
- Word count boundaries and markdown stripping behavior
- Detection of corrupted inputs vs false positives on healthy repository
- CLI flags (--fail-fast, --json, -v) and execution performance
"""

import os
import sys
import json
import copy
import time
import subprocess
import unittest
import unittest.mock as mock
import builtins

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import audit_pipeline as ap


class TestDraft07SchemaValidationAdversarial(unittest.TestCase):
    """Stress tests and adversarial mutation challenges for validate_draft07_schema."""

    def setUp(self):
        schema_path = os.path.join(PROJECT_ROOT, "data", "b2b_leads", "schema", "b2b_leads_schema.json")
        dataset_path = os.path.join(PROJECT_ROOT, "data", "b2b_leads", "leads_dataset.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.healthy_dataset = json.load(f)

    def test_healthy_dataset_passes_with_zero_violations(self):
        errors = ap.validate_draft07_schema(self.healthy_dataset, self.schema)
        self.assertEqual(len(errors), 0, f"Expected 0 violations on healthy dataset, got: {errors}")

    def test_top_level_type_mutation(self):
        for invalid_instance in [[], "string", 123, True]:
            errs = ap.validate_draft07_schema(invalid_instance, self.schema)
            self.assertTrue(len(errs) > 0, f"Failed to detect invalid top-level type: {type(invalid_instance)}")

    def test_missing_required_properties(self):
        for req in ["version", "generated_at", "total_targets", "targets"]:
            mutated = {k: v for k, v in self.healthy_dataset.items() if k != req}
            errs = ap.validate_draft07_schema(mutated, self.schema)
            self.assertTrue(any(f"missing required property '{req}'" in e for e in errs),
                            f"Did not detect missing required property: {req}")

    def test_total_targets_boundary_and_types(self):
        # Numeric minimum 15
        mutated_14 = {**self.healthy_dataset, "total_targets": 14}
        errs = ap.validate_draft07_schema(mutated_14, self.schema)
        self.assertTrue(any("numeric value 14 < minimum 15" in e for e in errs))

        # Float when integer expected
        mutated_float = {**self.healthy_dataset, "total_targets": 15.5}
        errs = ap.validate_draft07_schema(mutated_float, self.schema)
        self.assertTrue(any("expected integer, got float" in e for e in errs))

        # String when integer expected
        mutated_str = {**self.healthy_dataset, "total_targets": "15"}
        errs = ap.validate_draft07_schema(mutated_str, self.schema)
        self.assertTrue(any("expected integer, got str" in e for e in errs))

        # Boolean when integer expected
        mutated_bool = {**self.healthy_dataset, "total_targets": True}
        errs = ap.validate_draft07_schema(mutated_bool, self.schema)
        self.assertTrue(any("expected integer, got boolean" in e for e in errs))

    def test_targets_array_min_items(self):
        mutated = copy.deepcopy(self.healthy_dataset)
        mutated["targets"] = mutated["targets"][:14]
        errs = ap.validate_draft07_schema(mutated, self.schema)
        self.assertTrue(any("array length 14 < minItems 15" in e for e in errs))

    def test_target_item_mutations(self):
        # Target missing required field
        mutated = copy.deepcopy(self.healthy_dataset)
        del mutated["targets"][0]["company_name"]
        errs = ap.validate_draft07_schema(mutated, self.schema)
        self.assertTrue(any("missing required property 'company_name'" in e for e in errs))

        # Target ID regex mismatch
        for bad_id in ["TGT-12", "TGT-1234", "tgt-001", "TARGET-001"]:
            mutated = copy.deepcopy(self.healthy_dataset)
            mutated["targets"][0]["target_id"] = bad_id
            errs = ap.validate_draft07_schema(mutated, self.schema)
            self.assertTrue(any("does not match pattern" in e for e in errs),
                            f"Failed to reject invalid target_id: {bad_id}")

        # Empty string with minLength: 1
        mutated = copy.deepcopy(self.healthy_dataset)
        mutated["targets"][0]["vertical"] = ""
        errs = ap.validate_draft07_schema(mutated, self.schema)
        self.assertTrue(any("string length 0 < minLength 1" in e for e in errs))

        # Invalid website URI (non-http)
        mutated = copy.deepcopy(self.healthy_dataset)
        mutated["targets"][0]["website_url"] = "ftp://example.com"
        errs = ap.validate_draft07_schema(mutated, self.schema)
        self.assertTrue(any("invalid URI" in e for e in errs))

        # Invalid decision maker email
        for bad_email in ["notanemail", "user@", "@domain.com", "user@domain"]:
            mutated = copy.deepcopy(self.healthy_dataset)
            mutated["targets"][0]["decision_maker"]["email"] = bad_email
            errs = ap.validate_draft07_schema(mutated, self.schema)
            self.assertTrue(any("invalid email" in e for e in errs), f"Failed to reject bad email: {bad_email}")

        # Minimum thresholds
        mutated = copy.deepcopy(self.healthy_dataset)
        mutated["targets"][0]["estimated_aov"] = 4999.99
        errs = ap.validate_draft07_schema(mutated, self.schema)
        self.assertTrue(any("numeric value 4999.99 < minimum 5000" in e for e in errs))

        mutated = copy.deepcopy(self.healthy_dataset)
        mutated["targets"][0]["estimated_monthly_visitors"] = 499
        errs = ap.validate_draft07_schema(mutated, self.schema)
        self.assertTrue(any("numeric value 499 < minimum 500" in e for e in errs))

        mutated = copy.deepcopy(self.healthy_dataset)
        mutated["targets"][0]["estimated_ad_spend_monthly"] = -0.01
        errs = ap.validate_draft07_schema(mutated, self.schema)
        self.assertTrue(any("< minimum 0" in e for e in errs))

    def test_number_type_boolean_bleed_vulnerability(self):
        """
        Adversarial edge case: in Python, bool subclasses int.
        validate_draft07_schema checks if schema_type == 'integer' and isinstance(instance, bool),
        but DOES NOT check schema_type == 'number' for booleans.
        This test documents this known type-bleed limitation.
        """
        mutated = copy.deepcopy(self.healthy_dataset)
        mutated["targets"][0]["estimated_aov"] = True
        errs = ap.validate_draft07_schema(mutated, self.schema)
        # Because isinstance(True, (int, float)) is True, and minimum check is bypassed for bool,
        # validate_draft07_schema returns 0 errors for True in a 'number' field.
        # We empirically assert this edge case behavior.
        self.assertEqual(len(errs), 0, "Confirms bool bleed into number type in schema validator")


class TestCryptographicAddressVerificationAdversarial(unittest.TestCase):
    """Adversarial stress testing of cryptographic checksum algorithms."""

    def test_eip55_ethereum_official_test_vectors(self):
        """Verify against standard EIP-55 test vectors."""
        official_vectors = [
            ("0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed", "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"),
            ("0xfb6916095ca1df60bb79ce92ce3ea74c37c5d359", "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359"),
            ("0xdbf03b407c01e7cd3cbea99509d93f8dddc8c6fb", "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB"),
            ("0xd1220a0cf47c7b9be7a2e6ba89f429762e7b9adb", "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb"),
        ]
        for lower_addr, expected_chk in official_vectors:
            self.assertEqual(ap.to_checksum_address(lower_addr), expected_chk)

    def test_eip55_canonical_base_wallet(self):
        base_addr = ap.CANONICAL_WALLETS["base"]
        base_chk = ap.CANONICAL_WALLETS["base_checksum"]
        self.assertEqual(ap.to_checksum_address(base_addr), base_chk)

    def test_eip55_poisoned_hex_and_length(self):
        # Non-hex characters
        with self.assertRaises(ValueError):
            ap.to_checksum_address("0xef5766253e2d92e530e301ac22dcb8de78e89c5g")
        # Too short (< 40 hex chars)
        with self.assertRaises(ValueError):
            ap.to_checksum_address("0xef5766253e2d92e530e301ac22dcb8de78e89c5")
        # Too long (> 40 hex chars)
        with self.assertRaises(ValueError):
            ap.to_checksum_address("0xef5766253e2d92e530e301ac22dcb8de78e89c5555")

    def test_solana_base58_canonical_and_poisoned(self):
        sol_addr = ap.CANONICAL_WALLETS["solana"]
        self.assertTrue(ap.verify_solana_address(sol_addr))

        # Invalid Base58 characters
        for invalid_char in ["0", "O", "I", "l"]:
            poisoned = sol_addr[:-1] + invalid_char
            self.assertFalse(ap.verify_solana_address(poisoned))

        # Length deviations
        self.assertFalse(ap.verify_solana_address(sol_addr[:-2]))
        self.assertFalse(ap.verify_solana_address(sol_addr + "1"))

    def test_bitcoin_bech32m_canonical_and_poisoned(self):
        btc_addr = ap.CANONICAL_WALLETS["bitcoin"]
        self.assertTrue(ap.verify_bech32m(btc_addr))

        # Mutate witness data and checksum characters
        for idx in [4, 10, 20, 40, 50, len(btc_addr) - 1]:
            cur = btc_addr[idx]
            alt = "q" if cur != "q" else "p"
            poisoned = btc_addr[:idx] + alt + btc_addr[idx+1:]
            self.assertFalse(ap.verify_bech32m(poisoned), f"Bech32m failed to detect mutation at index {idx}")

        # Wrong HRP
        self.assertFalse(ap.verify_bech32m("ltc1" + btc_addr[3:]))

    def test_stellar_strkey_canonical_and_poisoned(self):
        xlm_addr = ap.CANONICAL_WALLETS["stellar"]
        self.assertTrue(ap.verify_stellar_address(xlm_addr))

        # Mutate characters in body and checksum
        for idx in [1, 10, 25, 45, len(xlm_addr) - 1]:
            cur = xlm_addr[idx]
            alt = "A" if cur != "A" else "B"
            poisoned = xlm_addr[:idx] + alt + xlm_addr[idx+1:]
            self.assertFalse(ap.verify_stellar_address(poisoned), f"Stellar failed to detect mutation at index {idx}")

        # Wrong prefix (must start with G)
        self.assertFalse(ap.verify_stellar_address("S" + xlm_addr[1:]))


class TestWordCountAndMarkdownStrippingAdversarial(unittest.TestCase):
    """Stress tests for count_spoken_words and pitch script boundaries."""

    def test_word_count_exact_boundaries(self):
        # 160-260 total word bounds
        self.assertFalse(ap.MIN_WORD_COUNT <= 159 <= ap.MAX_WORD_COUNT)
        self.assertTrue(ap.MIN_WORD_COUNT <= 160 <= ap.MAX_WORD_COUNT)
        self.assertTrue(ap.MIN_WORD_COUNT <= 260 <= ap.MAX_WORD_COUNT)
        self.assertFalse(ap.MIN_WORD_COUNT <= 261 <= ap.MAX_WORD_COUNT)

        # 140-220 video word bounds
        self.assertFalse(ap.MIN_VIDEO_WORD_COUNT <= 139 <= ap.MAX_VIDEO_WORD_COUNT)
        self.assertTrue(ap.MIN_VIDEO_WORD_COUNT <= 140 <= ap.MAX_VIDEO_WORD_COUNT)
        self.assertTrue(ap.MIN_VIDEO_WORD_COUNT <= 220 <= ap.MAX_VIDEO_WORD_COUNT)
        self.assertFalse(ap.MIN_VIDEO_WORD_COUNT <= 221 <= ap.MAX_VIDEO_WORD_COUNT)

    def test_markdown_stripping_behavior(self):
        text = "# Heading One\nThis is a **bold** and *italic* pitch with a [link](https://example.com)."
        # Expected tokens: 'This', 'is', 'a', 'bold', 'and', 'italic', 'pitch', 'with', 'a', 'link' (10 words)
        words = ap.count_spoken_words(text)
        self.assertEqual(words, 10)

    def test_inline_hash_stripping_observation(self):
        """
        Documents empirical observation: count_spoken_words uses re.sub(r'#.*', '', text)
        which strips all characters after '#' on that line, including inline text.
        """
        text = "Provider #1 in commercial HVAC services."
        words = ap.count_spoken_words(text)
        # 'Provider' is 1 word; '#1 in commercial HVAC services.' is stripped
        self.assertEqual(words, 1)


class TestCorruptionDetectionAcrossPillars(unittest.TestCase):
    """Verifies that PipelineAuditor detects faults and does not produce false positives."""

    def test_clean_pipeline_has_zero_failures(self):
        auditor = ap.PipelineAuditor()
        report = auditor.run_all()
        self.assertEqual(report["overall_status"], "PASS")
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(report["summary"]["total_checks"], 67)

    def test_detects_pitch_spam_trigger(self):
        auditor = ap.PipelineAuditor()
        real_open = builtins.open
        with real_open(os.path.join(PROJECT_ROOT, "data", "b2b_leads", "pitches", "pitch_tgt_001.md")) as f:
            orig = f.read()

        def mock_open_fn(file, *args, **kwargs):
            if "pitch_tgt_001.md" in str(file):
                return mock.mock_open(read_data=orig + "\nBuy now for a limited time!")()
            return real_open(file, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=mock_open_fn):
            auditor.audit_b2b_pitches()

        self.assertEqual(auditor.results["b2b_pitches"]["status"], "FAIL")
        checks = {c["name"]: c["status"] for c in auditor.results["b2b_pitches"]["checks"]}
        self.assertEqual(checks["pitch_no_spam_triggers"], "FAIL")

    def test_detects_pitch_placeholder_token(self):
        auditor = ap.PipelineAuditor()
        real_open = builtins.open
        with real_open(os.path.join(PROJECT_ROOT, "data", "b2b_leads", "pitches", "pitch_tgt_001.md")) as f:
            orig = f.read()

        def mock_open_fn(file, *args, **kwargs):
            if "pitch_tgt_001.md" in str(file):
                return mock.mock_open(read_data=orig + "\n[TODO] insert personalized note")()
            return real_open(file, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=mock_open_fn):
            auditor.audit_b2b_pitches()

        checks = {c["name"]: c["status"] for c in auditor.results["b2b_pitches"]["checks"]}
        self.assertEqual(checks["pitch_no_template_artifacts"], "FAIL")

    def test_detects_audit_missing_section(self):
        auditor = ap.PipelineAuditor()
        real_open = builtins.open
        with real_open(os.path.join(PROJECT_ROOT, "data", "b2b_leads", "audits", "audit_tgt_001.md")) as f:
            orig = f.read()

        corrupted = orig.replace("## 4. Three-Phase Technical Remediation Plan", "## Remediation")
        def mock_open_fn(file, *args, **kwargs):
            if "audit_tgt_001.md" in str(file):
                return mock.mock_open(read_data=corrupted)()
            return real_open(file, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=mock_open_fn):
            auditor.audit_b2b_audits()

        checks = {c["name"]: c["status"] for c in auditor.results["b2b_audits"]["checks"]}
        self.assertEqual(checks["audit_diagnostic_sections_complete"], "FAIL")

    def test_detects_digital_assets_cdn_injection(self):
        auditor = ap.PipelineAuditor()
        real_open = builtins.open
        with real_open(os.path.join(PROJECT_ROOT, "digital_assets", "web3_saas_calculator", "index.html")) as f:
            orig = f.read()

        corrupted = orig + '\n<script src="https://cdnjs.cloudflare.com/ajax/libs/chart.js"></script>'
        def mock_open_fn(file, *args, **kwargs):
            if "index.html" in str(file) and "calculator" in str(file):
                return mock.mock_open(read_data=corrupted)()
            return real_open(file, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=mock_open_fn):
            auditor.audit_digital_assets()

        checks = {c["name"]: c["status"] for c in auditor.results["digital_assets"]["checks"]}
        self.assertEqual(checks["calculator_zero_external_cdn"], "FAIL")

    def test_detects_wallet_removal_from_readme(self):
        auditor = ap.PipelineAuditor()
        real_open = builtins.open
        with real_open(os.path.join(PROJECT_ROOT, "README.md")) as f:
            orig = f.read()

        corrupted = orig.replace(ap.CANONICAL_WALLETS["stellar"], "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2XX")
        def mock_open_fn(file, *args, **kwargs):
            if "README.md" in str(file):
                return mock.mock_open(read_data=corrupted)()
            return real_open(file, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=mock_open_fn):
            auditor.audit_beneficiary_wallets()

        checks = {c["name"]: c["status"] for c in auditor.results["wallets"]["checks"]}
        self.assertEqual(checks["wallets_present_across_distribution_kit"], "FAIL")


class TestCLIFlagsAndPerformanceAdversarial(unittest.TestCase):
    """Verifies CLI flag behavior, exit codes, and execution performance."""

    def test_cli_help_flag(self):
        cmd = [sys.executable, os.path.join(PROJECT_ROOT, "audit_pipeline.py"), "--help"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--json", proc.stdout)
        self.assertIn("--fail-fast", proc.stdout)
        self.assertIn("-v", proc.stdout)

    def test_cli_json_flag_strict_parse(self):
        cmd = [sys.executable, os.path.join(PROJECT_ROOT, "audit_pipeline.py"), "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout.strip())
        self.assertEqual(data["overall_status"], "PASS")
        self.assertEqual(data["summary"]["failed"], 0)

    def test_cli_fail_fast_flag(self):
        cmd = [sys.executable, os.path.join(PROJECT_ROOT, "audit_pipeline.py"), "--fail-fast"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(proc.returncode, 0)

    def test_cli_verbose_and_json_flag_interaction(self):
        """
        Adversarial discovery: when -v and --json are combined,
        verbose check logs pollute stdout, corrupting JSON parsing.
        """
        cmd = [sys.executable, os.path.join(PROJECT_ROOT, "audit_pipeline.py"), "-v", "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        self.assertEqual(proc.returncode, 0)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(proc.stdout)

    def test_execution_performance(self):
        t0 = time.perf_counter()
        cmd = [sys.executable, os.path.join(PROJECT_ROOT, "audit_pipeline.py")]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        duration_ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(proc.returncode, 0)
        self.assertLess(duration_ms, 1000.0, f"Execution exceeded 1000ms: {duration_ms}ms")


if __name__ == "__main__":
    unittest.main()
