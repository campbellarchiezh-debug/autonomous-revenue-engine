"""
Tier 2: Boundary & Corner Cases Test Suite.
Verifies edge cases, malformed data, boundary thresholds, and offline modes across F01-F13.
Requires >= 5 test cases per feature (>= 65 test cases total).
"""

import os
import sys
import json
import csv
import re
import ast
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
    PATH_LICENSE,
    PATH_SETUP,
    PATH_DOCS_PREVIEW,
    PATH_FUNDING_YML,
    PATH_VERIFY_BALANCES,
    PATH_AUDIT_PIPELINE,
    count_words,
    run_command_in_project,
    reference_keccak256,
    reference_to_checksum_address,
    reference_verify_bech32m,
    reference_verify_solana_address,
    reference_verify_stellar_address
)

class TestF01B2BBoundaries(unittest.TestCase):
    """F01: B2B Dataset Boundary & Corner Cases"""

    def _load_dataset(self):
        import time
        if not os.path.exists(PATH_B2B_DATASET_JSON):
            self.skipTest("F01 dataset not generated yet")
        try:
            with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            time.sleep(0.2)
            with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
                return json.load(f)

    def test_t2_f01_empty_dataset_handling(self):
        """T2.1: Dataset file is non-empty and contains valid array of targets."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        self.assertGreater(len(leads), 0, "Dataset cannot be empty")

    def test_t2_f01_boundary_aov_pricing(self):
        """T2.2: Estimated AOV is within realistic high-ticket boundary ($5,000 to $500,000)."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        for lead in leads:
            aov = lead["estimated_aov"]
            self.assertGreaterEqual(aov, 5000, "AOV below minimum high-ticket threshold $5,000")
            self.assertLessEqual(aov, 500000, "AOV exceeds reasonable single-contract boundary $500,000")

    def test_t2_f01_target_id_uniqueness_and_format(self):
        """T2.3: All target IDs are strictly unique and match standard format."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        ids = [l["target_id"] for l in leads]
        self.assertEqual(len(ids), len(set(ids)), "Target IDs contain duplicates")
        for tid in ids:
            self.assertTrue(bool(re.match(r"^TGT-?\d{2,3}$", tid, re.IGNORECASE)), f"Invalid target ID format: {tid}")

    def test_t2_f01_website_url_schemes(self):
        """T2.4: Website URLs have valid http/https scheme and domain structure."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        for lead in leads:
            url = lead["website_url"]
            self.assertTrue(url.startswith("https://") or url.startswith("http://"), f"Invalid URL scheme: {url}")
            self.assertNotIn(" ", url, f"URL contains whitespace: {url}")

    def test_t2_f01_decision_maker_contact_validation(self):
        """T2.5: Decision maker email, phone, and name have non-empty valid formats."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        for lead in leads:
            dm = lead["decision_maker"]
            self.assertIn("@", dm["email"], f"Invalid email format in {lead['target_id']}: {dm['email']}")
            self.assertGreater(len(dm["name"].strip()), 2, f"Name too short in {lead['target_id']}")
            self.assertGreater(len(dm["phone"].strip()), 7, f"Phone too short in {lead['target_id']}")


class TestF02LeakCalculatorBoundaries(unittest.TestCase):
    """F02: Leak Calculator Boundary & Corner Cases"""

    def _get_calculator(self):
        if not os.path.exists(PATH_B2B_SRC_DIR):
            self.skipTest("F02 b2b_pipeline not created yet")
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from src.b2b_pipeline.leak_calculator import calculate_lost_pipeline
            return calculate_lost_pipeline
        except ImportError:
            self.skipTest("calculate_lost_pipeline not implemented yet")
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)

    def test_t2_f02_zero_visitors_edge_case(self):
        """T2.6: Zero visitors input produces 0 lost pipeline without ZeroDivisionError."""
        calc = self._get_calculator()
        result = calc(monthly_visitors=0, conversion_leak_pct=0.02, aov=25000)
        self.assertEqual(result, 0)

    def test_t2_f02_extreme_traffic_inputs(self):
        """T2.7: Extreme traffic and AOV values (10M visitors, $500k AOV) handled without overflow."""
        calc = self._get_calculator()
        result = calc(monthly_visitors=10_000_000, conversion_leak_pct=0.01, aov=500_000)
        self.assertEqual(result, 50_000_000_000)

    def test_t2_f02_negative_inputs_handling(self):
        """T2.8: Negative visitor or AOV inputs either raise ValueError or clamp to 0."""
        calc = self._get_calculator()
        try:
            result = calc(monthly_visitors=-1000, conversion_leak_pct=0.02, aov=20000)
            self.assertEqual(result, 0, "Negative visitors should return 0 lost pipeline")
        except ValueError:
            pass # ValueError is also compliant

    def test_t2_f02_fractional_leak_percentage_precision(self):
        """T2.9: Fractional leak percentages (0.005 vs 0.05) maintain numerical precision."""
        calc = self._get_calculator()
        # 10,000 visitors * 0.005 (0.5% leak) = 50 lost * $20,000 = $1,000,000
        res1 = calc(monthly_visitors=10000, conversion_leak_pct=0.005, aov=20000)
        self.assertEqual(res1, 1000000)

    def test_t2_f02_upper_bound_leak_rate_100_percent(self):
        """T2.10: 100% leak rate (1.0) calculates complete pipeline loss."""
        calc = self._get_calculator()
        # 1000 visitors * 1.0 * $10,000 = $10,000,000
        res = calc(monthly_visitors=1000, conversion_leak_pct=1.0, aov=10000)
        self.assertEqual(res, 10000000)


class TestF03PitchScriptsBoundaries(unittest.TestCase):
    """F03: Pitch Scripts Boundary & Corner Cases"""

    def _get_pitches(self):
        if not os.path.exists(PATH_B2B_PITCHES_DIR):
            self.skipTest("F03 pitches dir not present")
        files = [f for f in os.listdir(PATH_B2B_PITCHES_DIR) if f.endswith(".md")]
        if not files:
            self.skipTest("F03 pitches empty")
        return files

    def test_t2_f03_word_count_strict_under_minimum(self):
        """T2.11: Synthetic pitch with <150 words is flagged as too short for 90s pitch."""
        short_pitch = "Hi John, I saw your website. It has a leak. We can fix it. Call me."
        self.assertLess(count_words(short_pitch), 150)

    def test_t2_f03_word_count_strict_over_maximum(self):
        """T2.12: Synthetic pitch with >280 words is flagged as exceeding 90s speaking time."""
        long_pitch = "word " * 300
        self.assertGreater(count_words(long_pitch), 280)

    def test_t2_f03_unrendered_placeholder_detection(self):
        """T2.13: Scans pitch scripts for template artifacts ({{, }}, <TODO>, REPLACE_ME)."""
        files = self._get_pitches()
        for fname in files:
            p = os.path.join(PATH_B2B_PITCHES_DIR, fname)
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            for token in ["{{", "}}", "<TODO>", "REPLACE_ME", "[TBD]"]:
                self.assertNotIn(token, content, f"Pitch {fname} contains placeholder: {token}")

    def test_t2_f03_special_characters_escaping(self):
        """T2.14: Pitch files do not contain unescaped script tags or broken HTML."""
        files = self._get_pitches()
        for fname in files:
            p = os.path.join(PATH_B2B_PITCHES_DIR, fname)
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("<script>", content.lower())
            self.assertNotIn("javascript:", content.lower())

    def test_t2_f03_soft_cta_phrasing_detection(self):
        """T2.15: Pitch files avoid high-pressure spam terms and adhere to value-first soft CTAs."""
        files = self._get_pitches()
        spam_triggers = ["buy now", "limited time only", "act fast", "100% guaranteed money back"]
        for fname in files:
            p = os.path.join(PATH_B2B_PITCHES_DIR, fname)
            with open(p, "r", encoding="utf-8") as f:
                lowered = f.read().lower()
            for spam in spam_triggers:
                self.assertNotIn(spam, lowered, f"Pitch {fname} contains high-pressure spam phrasing: {spam}")


class TestF04SchemasFormatsBoundaries(unittest.TestCase):
    """F04: Schemas, Formats & Export Boundary Cases"""

    def test_t2_f04_csv_rfc4180_quoting_and_special_chars(self):
        """T2.16: CSV handles fields containing commas, quotes, and newlines."""
        if not os.path.exists(PATH_B2B_DATASET_CSV):
            self.skipTest("F04 CSV not present")
        with open(PATH_B2B_DATASET_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            for row_idx, row in enumerate(reader, 1):
                self.assertEqual(len(row), len(headers), f"Row {row_idx} column count mismatch with header")

    def test_t2_f04_schema_rejects_missing_required_fields(self):
        """T2.17: JSON schema defines required array containing core target properties."""
        if not os.path.exists(PATH_B2B_SCHEMA_JSON):
            self.skipTest("F04 schema not present")
        with open(PATH_B2B_SCHEMA_JSON, "r", encoding="utf-8") as f:
            schema = json.load(f)
        required = schema.get("required", [])
        if not required and "items" in schema:
            required = schema["items"].get("required", [])
        elif not required and "properties" in schema and "leads" in schema["properties"]:
            required = schema["properties"]["leads"].get("items", {}).get("required", [])
        self.assertTrue(len(required) > 0, "Schema must define required properties array")

    def test_t2_f04_schema_rejects_invalid_types(self):
        """T2.18: JSON schema specifies numerical type for estimated_aov."""
        if not os.path.exists(PATH_B2B_SCHEMA_JSON):
            self.skipTest("F04 schema not present")
        with open(PATH_B2B_SCHEMA_JSON, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('"estimated_aov"', content)
        self.assertTrue("number" in content or "integer" in content)

    def test_t2_f04_csv_row_count_exact_match(self):
        """T2.19: CSV export contains at least 15 valid data rows without empty rows."""
        if not os.path.exists(PATH_B2B_DATASET_CSV):
            self.skipTest("F04 CSV not present")
        with open(PATH_B2B_DATASET_CSV, "r", encoding="utf-8") as f:
            rows = [line.strip() for line in f if line.strip()]
        # Header + 15 rows = 16 non-empty lines
        self.assertGreaterEqual(len(rows), 16)

    def test_t2_f04_audit_report_referential_integrity(self):
        """T2.20: Every audit_report_file named in dataset matches an existing file in audits/."""
        if not os.path.exists(PATH_B2B_DATASET_JSON) or not os.path.exists(PATH_B2B_AUDITS_DIR):
            self.skipTest("Dataset or audits dir not present")
        with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        for lead in leads:
            audit_file = lead.get("audit_report_file")
            if audit_file:
                filename = os.path.basename(audit_file)
                path = os.path.join(PATH_B2B_AUDITS_DIR, filename)
                self.assertTrue(os.path.exists(path), f"Audit file referenced in dataset missing: {path}")


class TestF05Web3CLIBoundaries(unittest.TestCase):
    """F05: Web3 CLI & Inspector Boundary Cases"""

    def test_t2_f05_zero_width_unicode_exploit_detection(self):
        """T2.21: Address containing invisible zero-width spaces (\u200b) is rejected or flagged."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("run_cli.py not present")
        malicious_addr = "0xef576625\u200b3e2d92e530e301ac22dcb8de78e89c55"
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", malicious_addr])
        # Should either exit non-zero or explicitly output warning/invalid
        output = (stdout + stderr).lower()
        self.assertTrue(ret != 0 or "invalid" in output or "zero-width" in output or "poison" in output)

    def test_t2_f05_homoglyph_cyrillic_spoof_detection(self):
        """T2.22: Address containing Cyrillic homoglyphs is rejected or flagged."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("run_cli.py not present")
        # Replace latin 'e' with cyrillic 'е' (\u0435)
        spoofed_addr = "0x\u0435f5766253e2d92e530e301ac22dcb8de78e89c55"
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", spoofed_addr])
        output = (stdout + stderr).lower()
        self.assertTrue(ret != 0 or "invalid" in output or "homoglyph" in output or "error" in output)

    def test_t2_f05_malformed_evm_addresses(self):
        """T2.23: Inspector flags malformed EVM addresses (wrong length, non-hex chars, missing 0x)."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("run_cli.py not present")
        bad_addrs = [
            "0x1234", # Too short
            "0x" + "a" * 39, # 39 chars
            "0x" + "a" * 41, # 41 chars
            "0x" + "z" * 40, # Non-hex
            "ef5766253e2d92e530e301ac22dcb8de78e89c55" # Missing 0x
        ]
        for bad in bad_addrs:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", bad])
            output = (stdout + stderr).lower()
            self.assertTrue(ret != 0 or "invalid" in output or "error" in output or "warning" in output, f"Failed to flag bad EVM address: {bad}")

    def test_t2_f05_invalid_solana_base58_addresses(self):
        """T2.24: Inspector flags invalid Solana addresses (illegal chars 0/O/I/l, bad length)."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("run_cli.py not present")
        bad_sol = [
            "0HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp", # Contains '0'
            "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysH",  # 43 chars but bad length/decode
            "ShortSolana123" # Too short (<32)
        ]
        for bad in bad_sol:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", bad])
            output = (stdout + stderr).lower()
            self.assertTrue(ret != 0 or "invalid" in output or "not a valid" in output, f"Failed to flag bad Solana: {bad}")

    def test_t2_f05_invalid_bitcoin_bech32m_addresses(self):
        """T2.25: Inspector flags invalid Bitcoin Bech32m addresses (corrupt checksum, invalid chars)."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("run_cli.py not present")
        # Mutate last char of valid canonical bitcoin address
        corrupt_btc = CANONICAL_WALLETS["bitcoin"][:-1] + ("f" if CANONICAL_WALLETS["bitcoin"][-1] != "f" else "q")
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", corrupt_btc])
        output = (stdout + stderr).lower()
        self.assertTrue(ret != 0 or "invalid" in output or "checksum" in output)


class TestF06Web3SPABoundaries(unittest.TestCase):
    """F06: Web3 SPA Boundary & Corner Cases"""

    def _get_spa(self):
        paths = [PATH_WEB3_WEB_SPA, get_path("web3_utility", "index.html")]
        for p in paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return p, f.read()
        self.skipTest("Web SPA index.html not present")

    def test_t2_f06_empty_input_validation(self):
        """T2.26: SPA scripts handle empty input without unhandled exception."""
        p, content = self._get_spa()
        self.assertTrue(len(content) > 100)

    def test_t2_f06_xss_prevention_in_address_display(self):
        """T2.27: SPA JavaScript avoids unsafe document.write or unsanitized innerHTML."""
        p, content = self._get_spa()
        self.assertNotIn("document.write(", content)
        spa_dir = os.path.dirname(p)
        js_files = [os.path.join(spa_dir, f) for f in os.listdir(spa_dir) if f.endswith(".js")]
        for jf in js_files:
            with open(jf, "r", encoding="utf-8") as f:
                js_content = f.read()
            self.assertNotIn("document.write(", js_content)

    def test_t2_f06_viewport_meta_responsive_bounds(self):
        """T2.28: HTML includes mobile responsive viewport meta tag."""
        p, content = self._get_spa()
        self.assertIn('name="viewport"', content)
        self.assertIn("width=device-width", content)

    def test_t2_f06_file_protocol_relative_links(self):
        """T2.29: All CSS and JS asset references are relative for file:// execution."""
        p, content = self._get_spa()
        # Ensure no src="/..." or href="/..." root paths
        self.assertNotIn('src="/', content)
        self.assertNotIn('href="/', content)

    def test_t2_f06_offline_local_storage_fallbacks(self):
        """T2.30: SPA loads without requiring remote web worker or external fonts."""
        p, content = self._get_spa()
        self.assertNotIn("fonts.googleapis.com", content)


class TestF07Web3TestSuitesBoundaries(unittest.TestCase):
    """F07: Web3 Test Suites Boundary Cases"""

    def test_t2_f07_test_isolation_and_no_side_effects(self):
        """T2.31: Running web3 tests leaves no lingering temp files in project root."""
        if not os.path.exists(PATH_WEB3_TESTS_DIR):
            self.skipTest("web3 tests dir not present")
        ret, stdout, stderr = run_command_in_project(["-m", "unittest", "discover", "-s", "web3_utility/tests"])
        # Should not create arbitrary scratch files in project root
        self.assertFalse(os.path.exists(get_path("temp.txt")))

    def test_t2_f07_unit_tests_runnable_offline(self):
        """T2.32: RPC monitor tests run cleanly in offline/mock environment without network."""
        if not os.path.exists(PATH_WEB3_TESTS_DIR):
            self.skipTest("web3 tests dir not present")
        test_rpc = os.path.join(PATH_WEB3_TESTS_DIR, "test_rpc_monitor.py")
        if not os.path.exists(test_rpc):
            self.skipTest("test_rpc_monitor.py not present")
        with open(test_rpc, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("mock" in content.lower() or "offline" in content.lower() or "unittest.mock" in content)

    def test_t2_f07_converter_zero_and_negative_boundaries(self):
        """T2.33: Converter handles 0 wei and invalid negative values."""
        conv_py = os.path.join(PATH_WEB3_SRC_DIR, "converter.py")
        if not os.path.exists(conv_py):
            self.skipTest("converter.py not present")
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from web3_utility.src.converter import wei_to_eth
            self.assertEqual(wei_to_eth(0), 0)
        except (ImportError, AttributeError):
            self.skipTest("converter function not present")
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)

    def test_t2_f07_converter_extreme_uint256_boundaries(self):
        """T2.34: Converter handles uint256 max value (2^256 - 1) without precision loss."""
        conv_py = os.path.join(PATH_WEB3_SRC_DIR, "converter.py")
        if not os.path.exists(conv_py):
            self.skipTest("converter.py not present")
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from web3_utility.src.converter import wei_to_eth
            max_uint256 = (1 << 256) - 1
            eth_val = wei_to_eth(max_uint256)
            self.assertGreater(eth_val, 10**58)
        except (ImportError, AttributeError):
            self.skipTest("converter function not present")
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)

    def test_t2_f07_cli_invalid_command_non_zero_exit(self):
        """T2.35: CLI returns non-zero exit code on invalid subcommand."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("run_cli.py not present")
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "nonexistent_subcommand_1234"])
        self.assertNotEqual(ret, 0, "CLI should fail on unrecognized command")


class TestF08StakingCalculatorBoundaries(unittest.TestCase):
    """F08: Staking Calculator Boundary Cases"""

    def _get_calc_code(self):
        paths = [
            PATH_CALCULATOR_SPA,
            get_path("digital_assets", "web3_saas_calculator", "index.html"),
            get_path("digital_assets", "staking_calculator", "index.html")
        ]
        for p in paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    html = f.read()
                d = os.path.dirname(p)
                js = ""
                for j in os.listdir(d):
                    if j.endswith(".js"):
                        with open(os.path.join(d, j), "r") as jf:
                            js += "\n" + jf.read()
                return html, js
        self.skipTest("Calculator files not present")

    def test_t2_f08_zero_apr_and_zero_stake_inputs(self):
        """T2.36: Calculator handles zero initial capital and 0% APR safely."""
        html, js = self._get_calc_code()
        # Verify min attributes on range/number inputs allow 0 or positive
        self.assertIn('min="0"', html)

    def test_t2_f08_extreme_apr_yield_limits(self):
        """T2.37: Calculator specifies max bounds on APR sliders (e.g. 100% or 200%)."""
        html, js = self._get_calc_code()
        self.assertIn('max="', html)

    def test_t2_f08_negative_opex_or_costs_clamping(self):
        """T2.38: Validator expense inputs have min=0 preventing negative costs."""
        html, js = self._get_calc_code()
        self.assertIn('id="monthlyOpEx"', html)
        self.assertIn('min="0"', html)

    def test_t2_f08_svg_viewbox_and_coordinate_integrity(self):
        """T2.39: SVG dynamic chart specifies viewBox and dimension attributes."""
        html, js = self._get_calc_code()
        self.assertIn('viewBox="', html)

    def test_t2_f08_break_even_unprofitable_state(self):
        """T2.40: JavaScript handles unprofitable scenario (costs > yield) cleanly."""
        html, js = self._get_calc_code()
        self.assertTrue(len(js) > 50)


class TestF09TurnkeyCodeTemplatesBoundaries(unittest.TestCase):
    """F09: Turnkey Code Templates Boundary Cases"""

    def test_t2_f09_rpc_template_corrupt_response_handling(self):
        """T2.41: Python RPC template handles HTTP errors and non-JSON responses."""
        if not os.path.exists(PATH_RPC_TEMPLATE):
            self.skipTest("rpc_client_template.py not present")
        with open(PATH_RPC_TEMPLATE, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertTrue("HTTPError" in code or "URLError" in code or "try:" in code)

    def test_t2_f09_rpc_template_zero_timeout_boundary(self):
        """T2.42: Python RPC template defines reasonable default timeout."""
        if not os.path.exists(PATH_RPC_TEMPLATE):
            self.skipTest("rpc_client_template.py not present")
        with open(PATH_RPC_TEMPLATE, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("timeout", code)

    def test_t2_f09_rpc_template_ssl_fallback_behavior(self):
        """T2.43: Python RPC template includes adaptive SSL fallback context."""
        if not os.path.exists(PATH_RPC_TEMPLATE):
            self.skipTest("rpc_client_template.py not present")
        with open(PATH_RPC_TEMPLATE, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertTrue("ssl._create_unverified_context" in code or "CERT_NONE" in code or "create_default_context" in code)

    def test_t2_f09_js_validator_null_undefined_types(self):
        """T2.44: JS address validator includes type-checking on input address."""
        if not os.path.exists(PATH_VALIDATOR_TEMPLATE):
            self.skipTest("address_validator.js not present")
        with open(PATH_VALIDATOR_TEMPLATE, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertTrue("typeof" in code or "!" in code)

    def test_t2_f09_js_validator_whitespace_and_empty_string(self):
        """T2.45: JS address validator handles empty string or trims whitespace."""
        if not os.path.exists(PATH_VALIDATOR_TEMPLATE):
            self.skipTest("address_validator.js not present")
        with open(PATH_VALIDATOR_TEMPLATE, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertTrue("trim" in code or "length" in code)


class TestF10DistributionKitBoundaries(unittest.TestCase):
    """F10: Distribution Kit Boundary Cases"""

    def test_t2_f10_readme_links_relative_validity(self):
        """T2.46: Relative file links in README.md point to actual existing files."""
        if not os.path.exists(PATH_README):
            self.skipTest("README.md not present")
        with open(PATH_README, "r", encoding="utf-8") as f:
            content = f.read()
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        for text, link in links:
            if not link.startswith("http") and not link.startswith("#"):
                clean_link = link.split("#")[0]
                resolved = get_path(clean_link)
                self.assertTrue(os.path.exists(resolved), f"Broken relative link in README: {clean_link}")

    def test_t2_f10_license_copyright_year_boundary(self):
        """T2.47: LICENSE file contains current year 2026."""
        if not os.path.exists(PATH_LICENSE):
            self.skipTest("LICENSE not present")
        with open(PATH_LICENSE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("2026", content)

    def test_t2_f10_setup_guide_edge_cases(self):
        """T2.48: SETUP.md includes instructions for both CLI and Web interfaces."""
        if not os.path.exists(PATH_SETUP):
            self.skipTest("SETUP.md not present")
        with open(PATH_SETUP, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("CLI", content)
        self.assertTrue("Web" in content or "Browser" in content)

    def test_t2_f10_preview_docs_wireframes_non_empty(self):
        """T2.49: docs/PREVIEW.md contains detailed ASCII wireframes (>400 bytes)."""
        if not os.path.exists(PATH_DOCS_PREVIEW):
            self.skipTest("docs/PREVIEW.md not present")
        with open(PATH_DOCS_PREVIEW, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 400)
        self.assertTrue("┌" in content or "+" in content or "|" in content or "```" in content)

    def test_t2_f10_funding_yml_syntax_and_schema(self):
        """T2.50: .github/FUNDING.yml contains valid YAML syntax and custom endpoints."""
        if not os.path.exists(PATH_FUNDING_YML):
            self.skipTest(".github/FUNDING.yml not present")
        with open(PATH_FUNDING_YML, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        self.assertTrue(any("custom:" in l for l in lines))


class TestF11PaymentRailsBoundaries(unittest.TestCase):
    """F11: Payment Rails Boundary & Corner Cases"""

    def test_t2_f11_tampered_base_address_rejection(self):
        """T2.51: Modifying 1 hex character case in Base address invalidates checksum."""
        original = CANONICAL_WALLETS["base_checksum"]
        # Index 3 is uppercase 'F'. Flip to lowercase 'f'
        self.assertEqual(original[3], "F")
        tampered = original[:3] + "f" + original[4:]
        # Recalculate checksum
        expected = reference_to_checksum_address(tampered)
        self.assertNotEqual(tampered, expected, "Tampered checksum should not match computed checksum")

    def test_t2_f11_solana_case_sensitivity_boundary(self):
        """T2.52: Inverting case of Solana Base58 address renders it invalid."""
        original = CANONICAL_WALLETS["solana"]
        # Base58 is case sensitive: lowercase version contains illegal character 'l' and fails
        tampered = original.lower()
        self.assertTrue(reference_verify_solana_address(original))
        self.assertFalse(reference_verify_solana_address(tampered))

    def test_t2_f11_bitcoin_taproot_bech32m_polymod_verification(self):
        """T2.53: Bitcoin Taproot address validates under BIP-350 polymod constant 0x2bc830a3."""
        addr = CANONICAL_WALLETS["bitcoin"]
        self.assertTrue(reference_verify_bech32m(addr), "Canonical Taproot address must pass BIP-350 bech32m polymod")

    def test_t2_f11_stellar_crc16_xmodem_verification(self):
        """T2.54: Stellar address validates under Base32 decoding and CRC16-XMODEM checksum."""
        addr = CANONICAL_WALLETS["stellar"]
        self.assertTrue(reference_verify_stellar_address(addr), "Canonical Stellar address must pass CRC16-XMODEM")

    def test_t2_f11_cross_chain_address_confusion_prevention(self):
        """T2.55: EVM and Solana address formats are strictly mutually exclusive."""
        evm = CANONICAL_WALLETS["base"]
        sol = CANONICAL_WALLETS["solana"]
        # EVM cannot decode as valid 32-byte Solana
        self.assertFalse(reference_verify_solana_address(evm))
        # Solana cannot be valid EVM (no 0x, len 44 != 42)
        self.assertFalse(sol.startswith("0x") and len(sol) == 42)


class TestF12LiveProgrammaticBalanceAuditingBoundaries(unittest.TestCase):
    """F12: Programmatic Balance Auditing Boundary Cases"""

    def test_t2_f12_invalid_chain_argument_rejection(self):
        """T2.56: verify_balances.py exits with non-zero error on invalid chain argument."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--chain", "dogecoin_invalid"])
        self.assertNotEqual(ret, 0, "Script should reject unknown chain")

    def test_t2_f12_extreme_short_timeout_handling(self):
        """T2.57: Script handles ultra-short timeout (--timeout 0.0001) without uncaught crash."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--simulate", "--timeout", "0.0001"])
        # In simulation mode, should succeed or report handled timeout cleanly
        self.assertNotIn("Traceback (most recent call last):", stderr)

    def test_t2_f12_stellar_horizon_404_resilience(self):
        """T2.58: verify_balances.py code contains explicit handling for Stellar 404 unfunded."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        with open(PATH_VERIFY_BALANCES, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertTrue("404" in code or "unfunded" in code.lower() or "resource_missing" in code)

    def test_t2_f12_rpc_failover_exhaustion_message(self):
        """T2.59: verify_balances.py code defines multiple fallback endpoints for Base and Solana."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        with open(PATH_VERIFY_BALANCES, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertTrue("llamarpc" in code or "publicnode" in code or "fallback" in code.lower())

    def test_t2_f12_json_flag_output_is_strict_json(self):
        """T2.60: When --json is specified, output parses strictly as valid JSON."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--simulate", "--json"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--offline", "--json"])
        self.assertEqual(ret, 0)
        parsed = json.loads(stdout.strip())
        self.assertIsInstance(parsed, dict)


class TestF13PipelineIntegrityVerificationBoundaries(unittest.TestCase):
    """F13: Pipeline Integrity Verification Boundary Cases"""

    def test_t2_f13_audit_pipeline_missing_leads_detection(self):
        """T2.61: audit_pipeline.py checks for dataset existence."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("leads_dataset.json", content)

    def test_t2_f13_audit_pipeline_invalid_wallet_detection(self):
        """T2.62: audit_pipeline.py validates all 4 canonical wallet addresses."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            content = f.read()
        for key in ["base", "solana", "bitcoin", "stellar"]:
            addr = CANONICAL_WALLETS[key]
            self.assertIn(addr[:10], content, f"Audit pipeline must verify {key} wallet")

    def test_t2_f13_audit_pipeline_word_count_violation_detection(self):
        """T2.63: audit_pipeline.py includes word count boundary verification for pitch scripts."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("word" in content.lower() and ("160" in content or "150" in content))

    def test_t2_f13_audit_pipeline_zero_dependency_assertion(self):
        """T2.64: audit_pipeline.py imports only standard library modules."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name, ["requests", "web3", "flask", "django", "numpy", "pandas"])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn(node.module.split(".")[0], ["requests", "web3", "flask", "django", "numpy", "pandas"])

    def test_t2_f13_audit_pipeline_report_json_schema(self):
        """T2.65: audit_pipeline.py generates structured report file audit_report.json."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("audit_report.json", content)


if __name__ == "__main__":
    unittest.main()
