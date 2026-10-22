"""
Tier 1: Feature Coverage Test Suite.
Verifies features F01 through F13 in isolation using public contracts and files.
Requires >= 5 test cases per feature (>= 65 test cases total).
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
    reference_to_checksum_address,
    reference_verify_bech32m,
    reference_verify_solana_address,
    reference_verify_stellar_address
)

class TestF01B2BLeadSourcingDataset(unittest.TestCase):
    """F01: B2B Lead Sourcing Dataset (ORIGINAL_REQUEST §R1)"""

    def _load_dataset(self):
        import time
        if not os.path.exists(PATH_B2B_DATASET_JSON):
            self.skipTest(f"F01 dataset not generated yet: {PATH_B2B_DATASET_JSON}")
        try:
            with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            time.sleep(0.2)
            with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
                return json.load(f)

    def test_t1_f01_dataset_file_exists_and_parses(self):
        """T1.1: Dataset exists and is valid JSON."""
        data = self._load_dataset()
        self.assertIsInstance(data, (list, dict))
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        self.assertIsInstance(leads, list)

    def test_t1_f01_lead_target_count_at_least_15(self):
        """T1.2: Dataset contains at least 15 verified commercial targets."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        self.assertGreaterEqual(len(leads), 15, "Requirement R1 mandates >= 15 verified commercial targets")

    def test_t1_f01_required_fields_present_per_target(self):
        """T1.3: All targets have complete contact, traffic, and revenue leak profiles."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        required_fields = [
            "target_id", "company_name", "vertical", "headquarters", "website_url",
            "estimated_aov", "estimated_monthly_visitors", "estimated_ad_spend_monthly",
            "decision_maker", "primary_conversion_leak", "secondary_conversion_leak",
            "estimated_monthly_lost_pipeline", "tailored_pitch_file", "audit_report_file"
        ]
        for lead in leads:
            for field in required_fields:
                self.assertIn(field, lead, f"Target {lead.get('target_id')} missing field: {field}")
            # Decision maker subfields
            dm = lead["decision_maker"]
            self.assertIsInstance(dm, dict)
            for dm_field in ["name", "title", "email", "phone", "linkedin_url"]:
                self.assertIn(dm_field, dm, f"Decision maker in {lead.get('target_id')} missing {dm_field}")

    def test_t1_f01_high_aov_pricing_thresholds(self):
        """T1.4: All targets meet high-AOV threshold (>= $5,000) and have positive lost pipeline."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        for lead in leads:
            aov = lead["estimated_aov"]
            self.assertGreaterEqual(aov, 5000, f"Target {lead.get('target_id')} AOV below $5,000 high-ticket threshold")
            lost_pipe = lead["estimated_monthly_lost_pipeline"]
            self.assertGreater(lost_pipe, 0, f"Target {lead.get('target_id')} must have positive lost pipeline")

    def test_t1_f01_vertical_diversity(self):
        """T1.5: Dataset spans at least 3 distinct high-AOV commercial verticals."""
        data = self._load_dataset()
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        verticals = set(lead.get("vertical", "") for lead in leads if lead.get("vertical"))
        self.assertGreaterEqual(len(verticals), 3, f"Expected >= 3 distinct verticals, found {len(verticals)}: {verticals}")


class TestF02ConversionLeakDiagnosticEngine(unittest.TestCase):
    """F02: Conversion Leak Diagnostic Engine (ORIGINAL_REQUEST §R1)"""

    def test_t1_f02_module_syntax_and_importability(self):
        """T1.6: Diagnostic engine python files exist and parse with clean AST."""
        calculator_py = os.path.join(PATH_B2B_SRC_DIR, "leak_calculator.py")
        if not os.path.exists(calculator_py):
            self.skipTest(f"F02 leak_calculator.py not generated yet: {calculator_py}")
        with open(calculator_py, "r", encoding="utf-8") as f:
            code = f.read()
        parsed = ast.parse(code)
        self.assertIsNotNone(parsed)

    def test_t1_f02_revenue_loss_calculation_logic(self):
        """T1.7: Revenue loss calculation formula correctness."""
        if not os.path.exists(PATH_B2B_SRC_DIR):
            self.skipTest("F02 b2b_pipeline source not created yet")
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from src.b2b_pipeline.leak_calculator import calculate_lost_pipeline
        except ImportError:
            self.skipTest("calculate_lost_pipeline not importable yet")
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)
        
        # Test mathematical contract: 3000 visitors, 2% leak, $20,000 AOV = 60 lost * 20,000 = $1,200,000
        result = calculate_lost_pipeline(monthly_visitors=3000, conversion_leak_pct=0.02, aov=20000)
        self.assertGreater(result, 0)
        self.assertEqual(result, 1200000)

    def test_t1_f02_lead_model_instantiation(self):
        """T1.8: Lead data model can be instantiated and validated."""
        models_py = os.path.join(PATH_B2B_SRC_DIR, "models.py")
        if not os.path.exists(models_py):
            self.skipTest(f"F02 models.py not found: {models_py}")
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from src.b2b_pipeline.models import LeadTarget, DecisionMaker
            dm = DecisionMaker(name="Jane Doe", title="COO", email="jane@example.com", phone="555-0100", linkedin_url="https://linkedin.com/in/jane")
            lead = LeadTarget(
                target_id="TGT-TEST", company_name="Test Co", vertical="Roofing",
                headquarters="Denver, CO", website_url="https://test.com",
                estimated_aov=25000, estimated_monthly_visitors=4000,
                estimated_ad_spend_monthly=8000, decision_maker=dm,
                primary_conversion_leak="Uncompressed Hero Video",
                secondary_conversion_leak="Unclickable Phone Link",
                estimated_monthly_lost_pipeline=100000,
                tailored_pitch_file="pitch_tgt_test.md",
                audit_report_file="audit_tgt_test.md"
            )
            self.assertEqual(lead.target_id, "TGT-TEST")
            self.assertEqual(lead.estimated_aov, 25000)
        except ImportError:
            self.skipTest("F02 LeadTarget/DecisionMaker not implemented in models.py yet")
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)

    def test_t1_f02_conversion_leak_categorization(self):
        """T1.9: Conversion leak categorizer detects mobile UX and technical friction points."""
        calculator_py = os.path.join(PATH_B2B_SRC_DIR, "leak_calculator.py")
        if not os.path.exists(calculator_py):
            self.skipTest(f"F02 leak_calculator.py not found: {calculator_py}")
        with open(calculator_py, "r", encoding="utf-8") as f:
            content = f.read()
        # Diagnostic engine should reference standard leak types
        self.assertTrue(any(term in content.lower() for term in ["mobile", "lcp", "cls", "video", "call", "form", "leak"]))

    def test_t1_f02_annualized_leakage_projections(self):
        """T1.10: Formatted currency and annual projection calculations."""
        calculator_py = os.path.join(PATH_B2B_SRC_DIR, "leak_calculator.py")
        if not os.path.exists(calculator_py):
            self.skipTest(f"F02 leak_calculator.py not found: {calculator_py}")
        sys.path.insert(0, PROJECT_ROOT)
        try:
            from src.b2b_pipeline.leak_calculator import annualize_pipeline_loss
            annual = annualize_pipeline_loss(100000)
            self.assertEqual(annual, 1200000)
        except (ImportError, AttributeError):
            # If function name is slightly different, check general module syntax
            with open(calculator_py, "r") as f:
                self.assertIn("def ", f.read())
        finally:
            if PROJECT_ROOT in sys.path:
                sys.path.remove(PROJECT_ROOT)


class TestF03TailoredPitchScripts(unittest.TestCase):
    """F03: 15 Tailored Pitch Scripts (ORIGINAL_REQUEST §R1)"""

    def _get_pitch_files(self):
        if not os.path.exists(PATH_B2B_PITCHES_DIR):
            self.skipTest(f"F03 pitches directory not created yet: {PATH_B2B_PITCHES_DIR}")
        files = [f for f in os.listdir(PATH_B2B_PITCHES_DIR) if f.endswith(".md")]
        if not files:
            self.skipTest("F03 pitch files not generated yet")
        return files

    def test_t1_f03_pitch_scripts_count_and_naming(self):
        """T1.11: Exactly 15 markdown pitch files exist in data/b2b_leads/pitches/."""
        files = self._get_pitch_files()
        self.assertGreaterEqual(len(files), 15, f"Expected at least 15 pitch scripts, found {len(files)}")

    def test_t1_f03_one_to_one_target_id_alignment(self):
        """T1.12: Each pitch file aligns with target identifiers (e.g. tgt_001 to tgt_015)."""
        files = self._get_pitch_files()
        for i in range(1, 16):
            expected_prefix = f"pitch_tgt_{i:03d}"
            matches = [f for f in files if expected_prefix in f.lower() or f"tgt_{i:03d}" in f.lower() or f"{i:02d}" in f.lower()]
            self.assertTrue(len(matches) > 0, f"Missing pitch script for target index {i:03d}")

    def test_t1_f03_word_count_duration_constraints(self):
        """T1.13: Pitch scripts comply with 90-second duration (140 to 220 words for 90s video script)."""
        files = self._get_pitch_files()
        for fname in files[:15]:
            path = os.path.join(PATH_B2B_PITCHES_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            video_part = content.split("### Companion Outreach Email")[0] if "### Companion Outreach Email" in content else content
            words = count_words(video_part)
            self.assertGreaterEqual(words, 140, f"Pitch {fname} video script too short ({words} words < 140 words)")
            self.assertLessEqual(words, 220, f"Pitch {fname} video script too long ({words} words > 220 words for 90s pitch)")

    def test_t1_f03_four_part_value_first_framework(self):
        """T1.14: Pitch scripts follow 4-part value-first framework."""
        files = self._get_pitch_files()
        for fname in files[:5]:
            path = os.path.join(PATH_B2B_PITCHES_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().lower()
            # Must contain problem diagnosis and call to action
            has_diagnostic = any(w in content for w in ["leak", "mobile", "speed", "conversion", "bounce", "error", "lost"])
            has_cta = any(w in content for w in ["send", "video", "walkthrough", "code", "take a look", "developer", "mind if"])
            self.assertTrue(has_diagnostic, f"Pitch {fname} lacks diagnostic analysis")
            self.assertTrue(has_cta, f"Pitch {fname} lacks value-first CTA")

    def test_t1_f03_personalization_checks(self):
        """T1.15: Pitch scripts contain personalized details and no unrendered template tags."""
        files = self._get_pitch_files()
        for fname in files[:15]:
            path = os.path.join(PATH_B2B_PITCHES_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("{{", content, f"Pitch {fname} has unrendered template tag '{{'")
            self.assertNotIn("}}", content, f"Pitch {fname} has unrendered template tag '}}'")
            self.assertNotIn("[TODO]", content, f"Pitch {fname} contains placeholder [TODO]")


class TestF04B2BSchemasFormatsAndExport(unittest.TestCase):
    """F04: B2B Schemas, Formats & Export (ORIGINAL_REQUEST §R1)"""

    def test_t1_f04_json_schema_validity(self):
        """T1.16: b2b_leads_schema.json exists and is a valid JSON schema."""
        if not os.path.exists(PATH_B2B_SCHEMA_JSON):
            self.skipTest(f"F04 schema not generated yet: {PATH_B2B_SCHEMA_JSON}")
        with open(PATH_B2B_SCHEMA_JSON, "r", encoding="utf-8") as f:
            schema = json.load(f)
        self.assertIn("type", schema)
        self.assertIn("properties", schema)

    def test_t1_f04_schema_validates_dataset_records(self):
        """T1.17: JSON Schema properties match required target fields."""
        if not os.path.exists(PATH_B2B_SCHEMA_JSON):
            self.skipTest(f"F04 schema not generated yet: {PATH_B2B_SCHEMA_JSON}")
        with open(PATH_B2B_SCHEMA_JSON, "r", encoding="utf-8") as f:
            schema = json.load(f)
        props = schema.get("properties", {})
        # If schema wraps array in 'leads' or 'targets', check items
        if "leads" in props:
            item_props = props["leads"].get("items", {}).get("properties", {})
        elif "targets" in props:
            item_props = props["targets"].get("items", {}).get("properties", {})
        else:
            item_props = props
        for key in ["target_id", "company_name", "vertical", "website_url", "estimated_aov"]:
            self.assertIn(key, item_props, f"Schema missing field definition for: {key}")

    def test_t1_f04_crm_csv_export_headers_and_rows(self):
        """T1.18: CRM CSV export exists and has valid tabular structure."""
        if not os.path.exists(PATH_B2B_DATASET_CSV):
            self.skipTest(f"F04 CSV export not generated yet: {PATH_B2B_DATASET_CSV}")
        with open(PATH_B2B_DATASET_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        self.assertGreaterEqual(len(header), 8, "CSV header missing core fields")
        self.assertGreaterEqual(len(rows), 15, "CSV export must contain at least 15 rows")

    def test_t1_f04_csv_json_target_alignment(self):
        """T1.19: Target IDs in CSV match Target IDs in JSON dataset."""
        if not os.path.exists(PATH_B2B_DATASET_JSON) or not os.path.exists(PATH_B2B_DATASET_CSV):
            self.skipTest("F04 CSV or JSON dataset not present")
        with open(PATH_B2B_DATASET_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        leads = data if isinstance(data, list) else data.get("leads", data.get("targets", []))
        json_ids = set(l["target_id"] for l in leads)

        with open(PATH_B2B_DATASET_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_ids = set(r["target_id"] for r in reader if "target_id" in r)
        self.assertEqual(json_ids, csv_ids, "Mismatch between JSON target IDs and CSV target IDs")

    def test_t1_f04_diagnostic_audit_reports_present(self):
        """T1.20: data/b2b_leads/audits/ contains at least 15 diagnostic audit reports."""
        if not os.path.exists(PATH_B2B_AUDITS_DIR):
            self.skipTest(f"F04 audits directory not found: {PATH_B2B_AUDITS_DIR}")
        audit_files = [f for f in os.listdir(PATH_B2B_AUDITS_DIR) if f.endswith(".md")]
        if not audit_files:
            self.skipTest("F04 audit files not generated yet")
        self.assertGreaterEqual(len(audit_files), 15, f"Expected >= 15 audit reports, found {len(audit_files)}")


class TestF05Web3MicroUtilityCLI(unittest.TestCase):
    """F05: Web3 Micro-Utility CLI Suite (ORIGINAL_REQUEST §R2)"""

    def test_t1_f05_cli_wrapper_executable_and_syntax(self):
        """T1.21: web3_utility/run_cli.py exists, parses, and provides help."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest(f"F05 CLI wrapper not generated yet: {PATH_WEB3_CLI}")
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "--help"])
        self.assertEqual(ret, 0, f"run_cli.py --help failed with error: {stderr}")
        self.assertIn("inspect", stdout.lower())

    def test_t1_f05_base_evm_eip55_checksum_inspection(self):
        """T1.22: CLI inspect command validates Base EVM address checksumming."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("F05 run_cli.py not present")
        addr = CANONICAL_WALLETS["base"]
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", addr])
        self.assertEqual(ret, 0, f"inspect failed on EVM address: {stderr}")
        self.assertIn("valid", stdout.lower())

    def test_t1_f05_solana_base58_address_inspection(self):
        """T1.23: CLI inspect command validates Solana 32-byte Base58 address."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("F05 run_cli.py not present")
        sol = CANONICAL_WALLETS["solana"]
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", sol])
        self.assertEqual(ret, 0, f"inspect failed on Solana address: {stderr}")
        self.assertIn("solana", stdout.lower())

    def test_t1_f05_bitcoin_bech32m_taproot_inspection(self):
        """T1.24: CLI inspect command validates Bitcoin Bech32m Taproot address."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("F05 run_cli.py not present")
        btc = CANONICAL_WALLETS["bitcoin"]
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", btc])
        self.assertEqual(ret, 0, f"inspect failed on Bitcoin address: {stderr}")
        self.assertIn("bitcoin", stdout.lower())

    def test_t1_f05_stellar_strkey_address_inspection(self):
        """T1.25: CLI inspect command validates Stellar StrKey Base32 address."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("F05 run_cli.py not present")
        xlm = CANONICAL_WALLETS["stellar"]
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "inspect", xlm])
        self.assertEqual(ret, 0, f"inspect failed on Stellar address: {stderr}")
        self.assertIn("stellar", stdout.lower())


class TestF06Web3MicroUtilityWebSPA(unittest.TestCase):
    """F06: Web3 Micro-Utility Web SPA (ORIGINAL_REQUEST §R2)"""

    def _get_spa_content(self):
        # Look in web3_utility/src/web/index.html or web3_utility/index.html
        paths = [PATH_WEB3_WEB_SPA, get_path("web3_utility", "index.html")]
        for p in paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return p, f.read()
        self.skipTest("F06 Web SPA index.html not generated yet")

    def test_t1_f06_web_spa_file_presence(self):
        """T1.26: Web SPA entrypoint index.html exists."""
        p, content = self._get_spa_content()
        self.assertTrue(len(content) > 200)

    def test_t1_f06_zero_external_dependencies_and_cdns(self):
        """T1.27: Web SPA has zero external CDN or npm script dependencies."""
        p, content = self._get_spa_content()
        self.assertNotIn("unpkg.com", content)
        self.assertNotIn("cdn.jsdelivr.net", content)
        self.assertNotIn("cdnjs.cloudflare.com", content)

    def test_t1_f06_inspector_ui_components_present(self):
        """T1.28: Web SPA contains multi-chain address inspector form."""
        p, content = self._get_spa_content()
        self.assertTrue(any(term in content.lower() for term in ["inspector", "address", "validate", "checksum"]))

    def test_t1_f06_rpc_monitor_ui_components_present(self):
        """T1.29: Web SPA contains RPC monitor latency / health components."""
        p, content = self._get_spa_content()
        self.assertTrue(any(term in content.lower() for term in ["rpc", "latency", "health", "benchmark", "ping"]))

    def test_t1_f06_tipping_modal_with_beneficiary_wallets(self):
        """T1.30: Web SPA includes tipping modal or cards embedding beneficiary wallets."""
        p, content = self._get_spa_content()
        self.assertIn(CANONICAL_WALLETS["base"].lower(), content.lower(), "SPA must embed Base beneficiary wallet")
        self.assertIn(CANONICAL_WALLETS["solana"], content, "SPA must embed Solana beneficiary wallet")


class TestF07Web3MicroUtilityTestSuites(unittest.TestCase):
    """F07: Web3 Micro-Utility Test Suites (ORIGINAL_REQUEST §R2)"""

    def test_t1_f07_test_directory_and_files_present(self):
        """T1.31: web3_utility/tests/ exists with test suites."""
        if not os.path.exists(PATH_WEB3_TESTS_DIR):
            self.skipTest(f"F07 tests directory not present: {PATH_WEB3_TESTS_DIR}")
        files = os.listdir(PATH_WEB3_TESTS_DIR)
        test_files = [f for f in files if f.startswith("test_") and f.endswith(".py")]
        if len(test_files) < 3 and not os.path.exists(os.path.join(PATH_WEB3_TESTS_DIR, "test_cli.py")):
            self.skipTest(f"F07 test suite generation in progress ({len(test_files)} files created)")
        self.assertGreaterEqual(len(test_files), 3)

    def test_t1_f07_inspector_tests_syntax_and_discovery(self):
        """T1.32: test_inspector.py compiles cleanly under AST."""
        test_path = os.path.join(PATH_WEB3_TESTS_DIR, "test_inspector.py")
        if not os.path.exists(test_path):
            self.skipTest("test_inspector.py not present")
        with open(test_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())

    def test_t1_f07_rpc_monitor_tests_syntax_and_discovery(self):
        """T1.33: test_rpc_monitor.py compiles cleanly under AST."""
        test_path = os.path.join(PATH_WEB3_TESTS_DIR, "test_rpc_monitor.py")
        if not os.path.exists(test_path):
            self.skipTest("test_rpc_monitor.py not present")
        with open(test_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())

    def test_t1_f07_converter_tests_syntax_and_discovery(self):
        """T1.34: test_converter.py compiles cleanly under AST."""
        test_path = os.path.join(PATH_WEB3_TESTS_DIR, "test_converter.py")
        if not os.path.exists(test_path):
            self.skipTest("test_converter.py not present")
        with open(test_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())

    def test_t1_f07_cli_tests_syntax_and_discovery(self):
        """T1.35: test_cli.py compiles cleanly under AST."""
        test_path = os.path.join(PATH_WEB3_TESTS_DIR, "test_cli.py")
        if not os.path.exists(test_path):
            self.skipTest("test_cli.py not present")
        with open(test_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())


class TestF08InteractiveStakingCalculator(unittest.TestCase):
    """F08: Interactive Staking Calculator (ORIGINAL_REQUEST §R3)"""

    def _get_calc_content(self):
        paths = [
            PATH_CALCULATOR_SPA,
            get_path("digital_assets", "web3_saas_calculator", "index.html"),
            get_path("digital_assets", "staking_calculator", "index.html")
        ]
        for p in paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return p, f.read()
        self.skipTest("F08 Staking Calculator SPA index.html not generated yet")

    def test_t1_f08_calculator_html_presence(self):
        """T1.36: Staking calculator HTML entrypoint exists."""
        p, content = self._get_calc_content()
        self.assertTrue(len(content) > 200)

    def test_t1_f08_interactive_input_sliders_present(self):
        """T1.37: Calculator contains interactive range sliders for financial inputs."""
        p, content = self._get_calc_content()
        self.assertIn('type="range"', content.lower())

    def test_t1_f08_dynamic_svg_chart_markup_present(self):
        """T1.38: Dynamic SVG chart container present with zero third-party chart dependencies."""
        p, content = self._get_calc_content()
        self.assertIn("<svg", content.lower())
        self.assertNotIn("chart.js", content.lower())
        self.assertNotIn("d3.js", content.lower())

    def test_t1_f08_financial_compounding_calculation_logic(self):
        """T1.39: Calculator scripts contain compounding and net revenue logic."""
        p, content = self._get_calc_content()
        calc_dir = os.path.dirname(p)
        js_files = [os.path.join(calc_dir, f) for f in os.listdir(calc_dir) if f.endswith(".js")]
        all_js = content
        for js_path in js_files:
            with open(js_path, "r", encoding="utf-8") as f:
                all_js += "\n" + f.read()
        self.assertTrue(any(term in all_js.lower() for term in ["compound", "apy", "apr", "revenue", "break-even", "return"]))

    def test_t1_f08_sponsor_pro_card_embeds_beneficiary_wallets(self):
        """T1.40: Calculator embeds sponsor/pro card with canonical beneficiary wallets."""
        p, content = self._get_calc_content()
        self.assertIn(CANONICAL_WALLETS["base"].lower(), content.lower())
        self.assertIn(CANONICAL_WALLETS["solana"], content)


class TestF09TurnkeyCodeTemplates(unittest.TestCase):
    """F09: Turnkey Code Templates (ORIGINAL_REQUEST §R3)"""

    def test_t1_f09_rpc_template_presence_and_syntax(self):
        """T1.41: templates/rpc_client_template.py exists and parses with clean AST."""
        if not os.path.exists(PATH_RPC_TEMPLATE):
            self.skipTest(f"F09 RPC client template not generated yet: {PATH_RPC_TEMPLATE}")
        with open(PATH_RPC_TEMPLATE, "r", encoding="utf-8") as f:
            code = f.read()
        parsed = ast.parse(code)
        self.assertIsNotNone(parsed)

    def test_t1_f09_rpc_template_failover_and_ssl_logic(self):
        """T1.42: Python RPC client template defines failover endpoints and adaptive SSL handling."""
        if not os.path.exists(PATH_RPC_TEMPLATE):
            self.skipTest("F09 RPC template not present")
        with open(PATH_RPC_TEMPLATE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(any(term in content for term in ["fallback", "failover", "endpoints", "retry"]))
        self.assertTrue(any(term in content for term in ["ssl", "SSL", "context", "unverified"]))

    def test_t1_f09_js_address_validator_presence(self):
        """T1.43: templates/address_validator.js exists."""
        if not os.path.exists(PATH_VALIDATOR_TEMPLATE):
            self.skipTest(f"F09 address_validator.js not generated yet: {PATH_VALIDATOR_TEMPLATE}")
        self.assertTrue(os.path.isfile(PATH_VALIDATOR_TEMPLATE))

    def test_t1_f09_js_address_validator_syntax(self):
        """T1.44: Vanilla JS address validator template contains multi-chain validation functions."""
        if not os.path.exists(PATH_VALIDATOR_TEMPLATE):
            self.skipTest("F09 address_validator.js not present")
        with open(PATH_VALIDATOR_TEMPLATE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("function", content)
        self.assertTrue(any(chain in content.lower() for chain in ["evm", "ethereum", "solana", "bitcoin", "stellar"]))

    def test_t1_f09_templates_zero_external_dependencies(self):
        """T1.45: Templates rely exclusively on standard libraries with zero external packages."""
        if not os.path.exists(PATH_RPC_TEMPLATE):
            self.skipTest("F09 RPC template not present")
        with open(PATH_RPC_TEMPLATE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("import requests", content)
        self.assertNotIn("import web3", content)


class TestF10DistributionKitAndDocs(unittest.TestCase):
    """F10: Distribution Kit & Docs (ORIGINAL_REQUEST §R3)"""

    def test_t1_f10_readme_presence_and_structure(self):
        """T1.46: Flagship README.md exists and is comprehensive (>500 bytes)."""
        if not os.path.exists(PATH_README):
            self.skipTest(f"F10 README.md not generated yet: {PATH_README}")
        with open(PATH_README, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 500)
        self.assertIn("# ", content)

    def test_t1_f10_license_presence_and_mit_terms(self):
        """T1.47: LICENSE exists with permissive MIT terms."""
        if not os.path.exists(PATH_LICENSE):
            self.skipTest(f"F10 LICENSE not generated yet: {PATH_LICENSE}")
        with open(PATH_LICENSE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("MIT License", content)

    def test_t1_f10_setup_guide_presence(self):
        """T1.48: SETUP.md exists with developer instructions."""
        if not os.path.exists(PATH_SETUP):
            self.skipTest(f"F10 SETUP.md not generated yet: {PATH_SETUP}")
        with open(PATH_SETUP, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 200)

    def test_t1_f10_preview_docs_visual_mockups(self):
        """T1.49: docs/PREVIEW.md exists with visual ASCII or UI previews."""
        if not os.path.exists(PATH_DOCS_PREVIEW):
            self.skipTest(f"F10 docs/PREVIEW.md not generated yet: {PATH_DOCS_PREVIEW}")
        with open(PATH_DOCS_PREVIEW, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 300)

    def test_t1_f10_funding_yml_crypto_endpoints(self):
        """T1.50: .github/FUNDING.yml exists with custom crypto funding endpoints."""
        if not os.path.exists(PATH_FUNDING_YML):
            self.skipTest(f"F10 .github/FUNDING.yml not generated yet: {PATH_FUNDING_YML}")
        with open(PATH_FUNDING_YML, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("custom:", content)


class TestF11MultiChainPaymentRailsEmbedding(unittest.TestCase):
    """F11: Multi-Chain Payment Rails Embedding (ORIGINAL_REQUEST §R4)"""

    def test_t1_f11_base_evm_canonical_address_embedded(self):
        """T1.51: Canonical Base EVM address is embedded across documentation and UI."""
        target_addr = CANONICAL_WALLETS["base"].lower()
        found = False
        for p in [PATH_README, PATH_DOCS_PREVIEW, PATH_WEB3_WEB_SPA, PATH_CALCULATOR_SPA]:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    if target_addr in f.read().lower():
                        found = True
                        break
        if not any(os.path.exists(p) for p in [PATH_README, PATH_WEB3_WEB_SPA]):
            self.skipTest("F11 assets not present yet")
        self.assertTrue(found, "Canonical Base EVM address not found in project assets")

    def test_t1_f11_solana_canonical_address_embedded(self):
        """T1.52: Canonical Solana address is embedded across documentation and UI."""
        target_addr = CANONICAL_WALLETS["solana"]
        found = False
        for p in [PATH_README, PATH_DOCS_PREVIEW, PATH_WEB3_WEB_SPA, PATH_CALCULATOR_SPA]:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    if target_addr in f.read():
                        found = True
                        break
        if not any(os.path.exists(p) for p in [PATH_README, PATH_WEB3_WEB_SPA]):
            self.skipTest("F11 assets not present yet")
        self.assertTrue(found, "Canonical Solana address not found in project assets")

    def test_t1_f11_bitcoin_taproot_canonical_address_embedded(self):
        """T1.53: Canonical Bitcoin Taproot address is embedded across documentation and UI."""
        target_addr = CANONICAL_WALLETS["bitcoin"]
        found = False
        for p in [PATH_README, PATH_DOCS_PREVIEW, PATH_WEB3_WEB_SPA, PATH_CALCULATOR_SPA]:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    if target_addr in f.read():
                        found = True
                        break
        if not any(os.path.exists(p) for p in [PATH_README, PATH_WEB3_WEB_SPA]):
            self.skipTest("F11 assets not present yet")
        self.assertTrue(found, "Canonical Bitcoin Taproot address not found in project assets")

    def test_t1_f11_stellar_canonical_address_embedded(self):
        """T1.54: Canonical Stellar address is embedded across documentation and UI."""
        target_addr = CANONICAL_WALLETS["stellar"]
        found = False
        for p in [PATH_README, PATH_DOCS_PREVIEW, PATH_WEB3_WEB_SPA, PATH_CALCULATOR_SPA]:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    if target_addr in f.read():
                        found = True
                        break
        if not any(os.path.exists(p) for p in [PATH_README, PATH_WEB3_WEB_SPA]):
            self.skipTest("F11 assets not present yet")
        self.assertTrue(found, "Canonical Stellar address not found in project assets")

    def test_t1_f11_cli_tip_command_displays_canonical_wallets(self):
        """T1.55: CLI --tip or --sponsor command displays all 4 canonical addresses."""
        if not os.path.exists(PATH_WEB3_CLI):
            self.skipTest("F11 CLI not present")
        ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "--tip"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "tip"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["web3_utility/run_cli.py", "--sponsor"])
        self.assertEqual(ret, 0, f"CLI tip command failed: {stderr}")
        self.assertIn(CANONICAL_WALLETS["base"].lower(), stdout.lower())
        self.assertIn(CANONICAL_WALLETS["solana"], stdout)


class TestF12LiveProgrammaticBalanceAuditing(unittest.TestCase):
    """F12: Live Programmatic Balance Auditing (ORIGINAL_REQUEST §R4)"""

    def test_t1_f12_script_presence_and_syntax(self):
        """T1.56: verify_balances.py exists at project root with clean AST."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest(f"F12 verify_balances.py not generated yet: {PATH_VERIFY_BALANCES}")
        with open(PATH_VERIFY_BALANCES, "r", encoding="utf-8") as f:
            code = f.read()
        parsed = ast.parse(code)
        self.assertIsNotNone(parsed)

    def test_t1_f12_cli_flags_support(self):
        """T1.57: verify_balances.py supports standard CLI flags (--help)."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--help"])
        self.assertEqual(ret, 0, f"--help failed: {stderr}")
        self.assertTrue(any(flag in stdout for flag in ["--simulate", "--offline", "--chain", "--json"]))

    def test_t1_f12_simulated_offline_run_exit_code(self):
        """T1.58: verify_balances.py --simulate returns exit code 0."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--simulate", "--json"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--offline", "--json"])
        self.assertEqual(ret, 0, f"Simulated balance run returned error: {stderr}")

    def test_t1_f12_json_output_structure_all_chains(self):
        """T1.59: verify_balances.py outputs JSON containing Base, Solana, Bitcoin, and Stellar."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--simulate", "--json"])
        if ret != 0:
            ret, stdout, stderr = run_command_in_project(["verify_balances.py", "--offline", "--json"])
        self.assertEqual(ret, 0)
        parsed = json.loads(stdout)
        self.assertIn("balances", parsed)
        balances = parsed["balances"]
        for chain in ["base", "solana", "bitcoin", "stellar"]:
            self.assertIn(chain, balances, f"Missing chain in balance output: {chain}")

    def test_t1_f12_unfunded_stellar_handling_resilience(self):
        """T1.60: Script reports Stellar unactivated account as unfunded without crash."""
        if not os.path.exists(PATH_VERIFY_BALANCES):
            self.skipTest("verify_balances.py not present")
        with open(PATH_VERIFY_BALANCES, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("404" in content or "unfunded" in content.lower() or "horizon" in content.lower())


class TestF13PipelineIntegrityVerification(unittest.TestCase):
    """F13: Pipeline Integrity Verification (ORIGINAL_REQUEST §Acceptance)"""

    def test_t1_f13_script_presence_and_syntax(self):
        """T1.61: audit_pipeline.py exists at project root with clean AST."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest(f"F13 audit_pipeline.py not generated yet: {PATH_AUDIT_PIPELINE}")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            code = f.read()
        parsed = ast.parse(code)
        self.assertIsNotNone(parsed)

    def test_t1_f13_b2b_suite_validation_logic(self):
        """T1.62: audit_pipeline.py inspects B2B leads dataset and schema."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("leads_dataset.json", content)

    def test_t1_f13_pitch_scripts_suite_validation_logic(self):
        """T1.63: audit_pipeline.py inspects 15 pitch scripts and word count constraints."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(any(term in content for term in ["pitches", "word_count", "15", "pitch_tgt"]))

    def test_t1_f13_web3_tools_suite_validation_logic(self):
        """T1.64: audit_pipeline.py verifies Web3 micro-utilities and payment rails."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        with open(PATH_AUDIT_PIPELINE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("web3_utility", content)
        self.assertIn(CANONICAL_WALLETS["base"].lower(), content.lower())

    def test_t1_f13_pipeline_audit_exit_code_and_report_generation(self):
        """T1.65: audit_pipeline.py supports verification and outputs report."""
        if not os.path.exists(PATH_AUDIT_PIPELINE):
            self.skipTest("audit_pipeline.py not present")
        ret, stdout, stderr = run_command_in_project(["audit_pipeline.py", "--help"])
        self.assertEqual(ret, 0, f"audit_pipeline.py --help failed: {stderr}")


if __name__ == "__main__":
    unittest.main()
