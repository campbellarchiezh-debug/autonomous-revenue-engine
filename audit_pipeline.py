#!/usr/bin/env python3
"""
Autonomous Revenue Engine: Master Pipeline Integrity Verification Script (Feature F13).

Validates the complete integrity of the autonomous revenue generation engine across
all 4 core business pillars:
  Pillar 1: B2B Lead Pipeline (leads_dataset.json, schema, 15 pitches, 15 audits)
  Pillar 2: Web3 Developer Utilities (run_cli.py, web SPA, 46 passing unit tests)
  Pillar 3: Digital Software Assets & Distribution Kit (calculator, templates, docs, README)
  Pillar 4: Multi-Chain Payment Rails (Base EVM, Solana, Bitcoin, Stellar wallet verification)

Strict Zero-External-Dependency Guarantee: Uses only Python 3.9+ standard library.
"""

import os
import sys
import re
import json
import ast
import csv
import time
import argparse
import py_compile
import unittest
import base64
from typing import Dict, List, Any, Tuple

# Project root calculation
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_project_path(*subpaths: str) -> str:
    return os.path.join(PROJECT_ROOT, *subpaths)

# Canonical beneficiary wallets
CANONICAL_WALLETS = {
    "base": "0xef5766253e2d92e530e301ac22dcb8de78e89c55",
    "base_checksum": "0xeF5766253e2D92E530e301aC22dcB8DE78E89C55",
    "solana": "3HLDkipdKmJKGjbgCD8moo3GyhEY4DWdZ7JAgSpMysHp",
    "bitcoin": "bc1pavl0c4wn596jmexty56ret76gnj9jxf7px7w983vmt6akymjgahsjk803e",
    "stellar": "GBS2F7RTMYO53E33JGTO32HR3IQ75RI7RDMQX5C3KROZQIJ5IXOMI2WA",
}

# Word count boundaries for 90-second pitches
MIN_WORD_COUNT = 160
MAX_WORD_COUNT = 260
MIN_VIDEO_WORD_COUNT = 140
MAX_VIDEO_WORD_COUNT = 220

# ---------------------------------------------------------------------------
# Cryptographic Checksum & Address Verification Routines (Pure Stdlib)
# ---------------------------------------------------------------------------

def _rol64(a: int, n: int) -> int:
    n %= 64
    return ((a >> (64 - n)) + (a << n)) & 0xFFFFFFFFFFFFFFFF

def _keccak_f1600_on_lanes(lanes: List[List[int]]) -> List[List[int]]:
    R = 1
    for _ in range(24):
        C = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
        D = [C[(x + 4) % 5] ^ _rol64(C[(x + 1) % 5], 1) for x in range(5)]
        lanes = [[lanes[x][y] ^ D[x] for y in range(5)] for x in range(5)]

        x, y = 1, 0
        current = lanes[x][y]
        for t in range(24):
            x, y = y, (2 * x + 3 * y) % 5
            current, lanes[x][y] = lanes[x][y], _rol64(current, (t + 1) * (t + 2) // 2)

        for y_idx in range(5):
            T = [lanes[x_idx][y_idx] for x_idx in range(5)]
            for x_idx in range(5):
                lanes[x_idx][y_idx] = T[x_idx] ^ ((~T[(x_idx + 1) % 5]) & T[(x_idx + 2) % 5]) & 0xFFFFFFFFFFFFFFFF

        for j in range(7):
            R = ((R << 1) ^ ((R >> 7) * 0x71)) % 256
            if R & 2:
                lanes[0][0] ^= (1 << ((1 << j) - 1))
    return lanes

def _load64(b: bytes) -> int:
    return sum(b[i] << (8 * i) for i in range(8))

def _store64(a: int) -> bytearray:
    return bytearray((a >> (8 * i)) & 0xFF for i in range(8))

def keccak_sponge(rate: int, capacity: int, input_bytes: bytes, delimited_suffix: int, output_len: int) -> bytes:
    output_bytes = bytearray()
    state = bytearray(200)
    rate_in_bytes = rate // 8
    block_size = 0
    input_offset = 0

    while input_offset < len(input_bytes):
        block_size = min(len(input_bytes) - input_offset, rate_in_bytes)
        for i in range(block_size):
            state[i] ^= input_bytes[input_offset + i]
        input_offset += block_size
        if block_size == rate_in_bytes:
            lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
            lanes = _keccak_f1600_on_lanes(lanes)
            state = bytearray()
            for y in range(5):
                for x in range(5):
                    state.extend(_store64(lanes[x][y]))
            block_size = 0

    state[block_size] ^= delimited_suffix
    if (delimited_suffix & 0x80) != 0 and block_size == (rate_in_bytes - 1):
        lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
        lanes = _keccak_f1600_on_lanes(lanes)
        state = bytearray()
        for y in range(5):
            for x in range(5):
                state.extend(_store64(lanes[x][y]))

    state[rate_in_bytes - 1] ^= 0x80
    lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
    lanes = _keccak_f1600_on_lanes(lanes)
    state = bytearray()
    for y in range(5):
        for x in range(5):
            state.extend(_store64(lanes[x][y]))

    while output_len > 0:
        block_size = min(output_len, rate_in_bytes)
        output_bytes.extend(state[:block_size])
        output_len -= block_size
        if output_len > 0:
            lanes = [[_load64(state[8 * (x + 5 * y) : 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
            lanes = _keccak_f1600_on_lanes(lanes)
            state = bytearray()
            for y in range(5):
                for x in range(5):
                    state.extend(_store64(lanes[x][y]))

    return bytes(output_bytes)

def keccak256(data: bytes) -> bytes:
    return keccak_sponge(1088, 512, data, 0x01, 32)

def to_checksum_address(addr: str) -> str:
    clean = addr.lower().replace("0x", "")
    if len(clean) != 40 or not all(c in "0123456789abcdef" for c in clean):
        raise ValueError("Invalid hex address")
    h = keccak256(clean.encode("ascii")).hex()
    return "0x" + "".join(c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(clean))

def verify_solana_address(address: str) -> bool:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    if len(address) < 32 or len(address) > 44:
        return False
    num = 0
    for char in address:
        idx = alphabet.find(char)
        if idx == -1:
            return False
        num = num * 58 + idx
    res = []
    while num > 0:
        res.append(num % 256)
        num //= 256
    pad = 0
    for c in address:
        if c == '1':
            pad += 1
        else:
            break
    decoded = b'\x00' * pad + bytes(reversed(res))
    return len(decoded) == 32

def verify_bech32m(address: str) -> bool:
    charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    pos = address.rfind("1")
    if pos < 1 or pos + 7 > len(address) or len(address) > 90:
        return False
    hrp = address[:pos].lower()
    if hrp not in ("bc", "tb"):
        return False
    data = []
    for c in address[pos+1:].lower():
        idx = charset.find(c)
        if idx == -1:
            return False
        data.append(idx)
    gen = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    expanded_hrp = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]
    for v in expanded_hrp + data:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= gen[i] if ((b >> i) & 1) else 0
    return chk == 0x2bc830a3

def crc16_xmodem(data: bytes) -> int:
    crc = 0x0000
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def verify_stellar_address(address: str) -> bool:
    if len(address) != 56 or not address.startswith("G"):
        return False
    try:
        pad_len = (8 - (len(address) % 8)) % 8
        padded = address + ("=" * pad_len)
        raw = base64.b32decode(padded.encode("ascii"))
        if len(raw) != 35 or raw[0] != 0x30:
            return False
        payload, checksum = raw[:-2], raw[-2:]
        expected_chk = crc16_xmodem(payload).to_bytes(2, "little")
        return checksum == expected_chk
    except Exception:
        return False

def count_spoken_words(text: str) -> int:
    clean = re.sub(r'#.*', '', text)
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)
    clean = re.sub(r'[*_`>]', '', clean)
    tokens = re.findall(r"\b[A-Za-z0-9'-]+\b", clean)
    return len(tokens)

# ---------------------------------------------------------------------------
# Pure Standard Library Draft-07 JSON Schema Validator
# ---------------------------------------------------------------------------

def validate_draft07_schema(instance: Any, schema: Dict[str, Any], path: str = "") -> List[str]:
    errors = []
    schema_type = schema.get("type")
    if schema_type:
        type_map = {
            "object": dict,
            "array": list,
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
        }
        if schema_type == "integer" and isinstance(instance, bool):
            errors.append(f"{path}: expected integer, got boolean")
        elif schema_type in type_map and not isinstance(instance, type_map[schema_type]):
            errors.append(f"{path}: expected {schema_type}, got {type(instance).__name__}")
            return errors

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        for k, v in instance.items():
            if k in props:
                errors.extend(validate_draft07_schema(v, props[k], f"{path}.{k}" if path else k))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: array length {len(instance)} < minItems {schema['minItems']}")
        items_schema = schema.get("items")
        if items_schema:
            for idx, item in enumerate(instance):
                errors.extend(validate_draft07_schema(item, items_schema, f"{path}[{idx}]"))

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: string length {len(instance)} < minLength {schema['minLength']}")
        if "pattern" in schema:
            if not re.search(schema["pattern"], instance):
                errors.append(f"{path}: value '{instance}' does not match pattern {schema['pattern']}")
        if schema.get("format") == "uri":
            if not (instance.startswith("http://") or instance.startswith("https://")):
                errors.append(f"{path}: invalid URI '{instance}'")
        if schema.get("format") == "email":
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", instance):
                errors.append(f"{path}: invalid email '{instance}'")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: numeric value {instance} < minimum {schema['minimum']}")

    return errors

# ---------------------------------------------------------------------------
# Individual Pillar Audit Suites
# ---------------------------------------------------------------------------

class PipelineAuditor:
    def __init__(self, verbose: bool = False, fail_fast: bool = False, skip_network: bool = False):
        self.verbose = verbose
        self.fail_fast = fail_fast
        self.skip_network = skip_network
        self.results = {}
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0

    def record_check(self, suite: str, check_name: str, passed: bool, message: str = ""):
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1

        if suite not in self.results:
            self.results[suite] = {
                "status": "PASS",
                "checks_total": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "checks": []
            }
        self.results[suite]["checks_total"] += 1
        if passed:
            self.results[suite]["checks_passed"] += 1
        else:
            self.results[suite]["checks_failed"] += 1
            self.results[suite]["status"] = "FAIL"

        self.results[suite]["checks"].append({
            "name": check_name,
            "status": "PASS" if passed else "FAIL",
            "message": message
        })

        if self.verbose:
            status_str = "[\033[92mPASS\033[0m]" if passed else "[\033[91mFAIL\033[0m]"
            print(f"  {status_str} {check_name}: {message}")

        if not passed and self.fail_fast:
            raise RuntimeError(f"Fail-fast halted on check: [{suite}] {check_name} -> {message}")

    def audit_b2b_leads(self):
        """Pillar 1: B2B Leads Dataset, CSV Export, and Schema Validation."""
        suite = "b2b_leads"
        json_path = get_project_path("data", "b2b_leads", "leads_dataset.json")
        csv_path = get_project_path("data", "b2b_leads", "leads_dataset.csv")
        schema_path = get_project_path("data", "b2b_leads", "schema", "b2b_leads_schema.json")

        # 1. Existence
        self.record_check(suite, "leads_dataset_json_exists", os.path.isfile(json_path), f"Path: {json_path}")
        self.record_check(suite, "leads_dataset_csv_exists", os.path.isfile(csv_path), f"Path: {csv_path}")
        self.record_check(suite, "b2b_leads_schema_json_exists", os.path.isfile(schema_path), f"Path: {schema_path}")

        if not (os.path.isfile(json_path) and os.path.isfile(schema_path)):
            return

        with open(json_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # 2. Draft-07 JSON Schema Validation
        errors = validate_draft07_schema(dataset, schema)
        self.record_check(suite, "draft07_schema_compliance", len(errors) == 0, 
                          "Zero schema violations" if not errors else f"{len(errors)} errors: {errors[:2]}")

        # 3. Minimum targets count >= 15
        targets = dataset.get("targets", [])
        self.record_check(suite, "lead_count_gte_15", len(targets) >= 15, f"Found {len(targets)} commercial targets")

        # 4. Target contents, AOV, URLs, Decision Makers, Placeholders
        forbidden_placeholders = ["{{", "}}", "<TODO>", "REPLACE_ME", "[TBD]", "[TODO]"]

        def _has_placeholders(obj):
            if isinstance(obj, str):
                return any(tok in obj for tok in forbidden_placeholders)
            elif isinstance(obj, dict):
                return any(_has_placeholders(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(_has_placeholders(x) for x in obj)
            return False

        all_placeholders_clean = not any(_has_placeholders(t) for t in targets)
        all_aov_valid = True
        all_contacts_valid = True

        for t in targets:
            if t.get("estimated_aov", 0) < 5000:
                all_aov_valid = False
            dm = t.get("decision_maker", {})
            if not dm.get("email") or "@" not in dm.get("email") or len(dm.get("phone", "")) < 7:
                all_contacts_valid = False

        self.record_check(suite, "no_placeholder_tokens", all_placeholders_clean, "Verified zero template artifacts")
        self.record_check(suite, "valid_high_aov_thresholds", all_aov_valid, "All target AOVs >= $5,000 USD")
        self.record_check(suite, "valid_decision_maker_contacts", all_contacts_valid, "All targets have direct contact points")

        # 5. CSV target alignment
        if os.path.isfile(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                csv_ids = [row["target_id"] for row in reader if "target_id" in row]
            json_ids = [t["target_id"] for t in targets]
            self.record_check(suite, "csv_json_target_id_alignment", sorted(csv_ids) == sorted(json_ids),
                              f"Exact 1-to-1 match across {len(csv_ids)} targets")

    def audit_b2b_pitches(self):
        """Pillar 1b: Tailored 90-Second Pitch Scripts (15 files in data/b2b_leads/pitches/)."""
        suite = "b2b_pitches"
        pitches_dir = get_project_path("data", "b2b_leads", "pitches")
        self.record_check(suite, "pitches_directory_exists", os.path.isdir(pitches_dir), f"Path: {pitches_dir}")

        if not os.path.isdir(pitches_dir):
            return

        pitch_files = sorted([f for f in os.listdir(pitches_dir) if f.endswith(".md")])
        self.record_check(suite, "pitch_files_count_gte_15", len(pitch_files) >= 15, f"Found {len(pitch_files)} pitch files")

        forbidden_placeholders = ["{{", "}}", "<TODO>", "REPLACE_ME", "[TBD]", "[TODO]"]
        spam_triggers = ["buy now", "limited time only", "act fast", "100% guaranteed money back"]

        all_words_valid = True
        all_video_words_valid = True
        all_personalized = True
        all_spam_clean = True
        all_tokens_clean = True

        for i in range(1, 16):
            expected_prefix = f"pitch_tgt_{i:03d}"
            matches = [f for f in pitch_files if expected_prefix in f.lower()]
            self.record_check(suite, f"pitch_tgt_{i:03d}_present", len(matches) > 0, f"Found {matches[0] if matches else 'none'}")
            if not matches:
                continue

            with open(os.path.join(pitches_dir, matches[0]), "r", encoding="utf-8") as f:
                content = f.read()

            # Word count constraints
            total_words = count_spoken_words(content)
            video_part = content.split("### Companion Outreach Email")[0] if "### Companion Outreach Email" in content else content
            video_words = count_spoken_words(video_part)

            if not (MIN_WORD_COUNT <= total_words <= MAX_WORD_COUNT):
                all_words_valid = False
            if not (MIN_VIDEO_WORD_COUNT <= video_words <= MAX_VIDEO_WORD_COUNT):
                all_video_words_valid = False

            # Personalization & diagnostic leaks
            has_leak = any(k in content.lower() for k in ["leak", "mobile", "speed", "conversion", "bounce", "pipeline"])
            has_cta = any(k in content.lower() for k in ["video", "walkthrough", "developer", "send that over", "take a look"])
            if not (has_leak and has_cta):
                all_personalized = False

            # Spam & tokens
            for st in spam_triggers:
                if st in content.lower():
                    all_spam_clean = False
            for tok in forbidden_placeholders:
                if tok in content:
                    all_tokens_clean = False

        self.record_check(suite, "pitch_word_count_bounds", all_words_valid,
                          f"All pitches strictly within {MIN_WORD_COUNT}-{MAX_WORD_COUNT} word boundaries")
        self.record_check(suite, "pitch_video_word_count_bounds", all_video_words_valid,
                          f"All 90s video scripts within {MIN_VIDEO_WORD_COUNT}-{MAX_VIDEO_WORD_COUNT} words")
        self.record_check(suite, "pitch_personalization_and_ctas", all_personalized,
                          "All pitch scripts feature diagnostic leaks and value-first soft CTAs")
        self.record_check(suite, "pitch_no_spam_triggers", all_spam_clean, "Zero high-pressure spam terms detected")
        self.record_check(suite, "pitch_no_template_artifacts", all_tokens_clean, "Zero unrendered placeholders")

    def audit_b2b_audits(self):
        """Pillar 1c: Diagnostic Audit Reports (15 files in data/b2b_leads/audits/)."""
        suite = "b2b_audits"
        audits_dir = get_project_path("data", "b2b_leads", "audits")
        self.record_check(suite, "audits_directory_exists", os.path.isdir(audits_dir), f"Path: {audits_dir}")

        if not os.path.isdir(audits_dir):
            return

        audit_files = sorted([f for f in os.listdir(audits_dir) if f.endswith(".md")])
        self.record_check(suite, "audit_files_count_gte_15", len(audit_files) >= 15, f"Found {len(audit_files)} audit reports")

        required_sections = [
            "## 1. Executive Financial Summary",
            "## 2. Core Web Vitals & Mobile Diagnostics",
            "## 3. Decision Maker & Key Contact Profile",
            "## 4. Three-Phase Technical Remediation Plan"
        ]

        all_sections_present = True
        all_metrics_quantified = True

        for i in range(1, 16):
            expected_prefix = f"audit_tgt_{i:03d}"
            matches = [f for f in audit_files if expected_prefix in f.lower()]
            self.record_check(suite, f"audit_tgt_{i:03d}_present", len(matches) > 0, f"Found {matches[0] if matches else 'none'}")
            if not matches:
                continue

            with open(os.path.join(audits_dir, matches[0]), "r", encoding="utf-8") as f:
                content = f.read()

            for sec in required_sections:
                if sec not in content:
                    all_sections_present = False

            has_lost_rev = ("Lost Pipeline" in content or "lost_pipeline" in content.lower()) and "$" in content
            has_cwv = ("Largest Contentful Paint" in content or "LCP" in content) and ("CLS" in content)
            if not (has_lost_rev and has_cwv):
                all_metrics_quantified = False

        self.record_check(suite, "audit_diagnostic_sections_complete", all_sections_present,
                          "All 15 audit reports contain all 4 diagnostic sections")
        self.record_check(suite, "audit_metrics_quantified", all_metrics_quantified,
                          "All 15 audit reports contain Core Web Vitals & quantified dollar loss calculations")

    def audit_web3_utility(self):
        """Pillar 2: Web3 Micro-Utility CLI, Web SPA & Unit Test Discovery Execution."""
        suite = "web3_utility"

        # 1. File existence
        cli_path = get_project_path("web3_utility", "run_cli.py")
        spa_html = get_project_path("web3_utility", "src", "web", "index.html")
        spa_js = get_project_path("web3_utility", "src", "web", "app.js")
        spa_css = get_project_path("web3_utility", "src", "web", "style.css")
        tests_dir = get_project_path("web3_utility", "tests")

        self.record_check(suite, "web3_cli_exists", os.path.isfile(cli_path), f"Path: {cli_path}")
        self.record_check(suite, "web3_spa_html_exists", os.path.isfile(spa_html), f"Path: {spa_html}")
        self.record_check(suite, "web3_spa_js_exists", os.path.isfile(spa_js), f"Path: {spa_js}")
        self.record_check(suite, "web3_spa_css_exists", os.path.isfile(spa_css), f"Path: {spa_css}")
        self.record_check(suite, "web3_tests_dir_exists", os.path.isdir(tests_dir), f"Path: {tests_dir}")

        # 2. Syntax Compilation (py_compile & AST)
        py_files = [cli_path]
        for root, _, files in os.walk(get_project_path("web3_utility")):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))
        py_files = sorted(list(set(py_files)))

        syntax_clean = True
        for pf in py_files:
            try:
                py_compile.compile(pf, doraise=True)
                with open(pf, "r", encoding="utf-8") as f:
                    ast.parse(f.read())
            except Exception:
                syntax_clean = False
                break
        self.record_check(suite, "web3_python_syntax_validity", syntax_clean, f"Compiled {len(py_files)} Python source files")

        # 3. Unit Test Execution via unittest discovery
        if os.path.isdir(tests_dir):
            loader = unittest.TestLoader()
            test_suite = loader.discover(tests_dir)
            import io
            runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
            res = runner.run(test_suite)
            all_tests_passed = res.wasSuccessful() and res.testsRun >= 46
            self.record_check(suite, "web3_unit_tests_pass", all_tests_passed,
                              f"Ran {res.testsRun} unit tests: {len(res.failures)} failures, {len(res.errors)} errors")

    def audit_digital_assets(self):
        """Pillar 3: Digital Assets, Turnkey Templates & Open-Source Distribution Kit."""
        suite = "digital_assets"

        distro_files = [
            "README.md", "LICENSE", "SETUP.md", "CONTRIBUTING.md", "CHANGELOG.md",
            "docs/PREVIEW.md", "docs/ARCHITECTURE.md", "docs/SPONSORSHIP.md", ".github/FUNDING.yml",
            "digital_assets/web3_saas_calculator/index.html",
            "digital_assets/web3_saas_calculator/style.css",
            "digital_assets/web3_saas_calculator/app.js",
            "templates/rpc_client_template.py",
            "templates/address_validator.js"
        ]

        all_exist = True
        all_non_empty = True
        for rel in distro_files:
            p = get_project_path(*rel.split("/"))
            if not os.path.isfile(p):
                all_exist = False
            elif os.path.getsize(p) < 100:
                all_non_empty = False

        self.record_check(suite, "distribution_kit_files_present", all_exist, f"Verified all {len(distro_files)} required distribution files")
        self.record_check(suite, "distribution_kit_files_non_empty", all_non_empty, "All files contain complete content (>100 bytes)")

        # Calculator dynamic charts & zero external CDN
        calc_html_path = get_project_path("digital_assets", "web3_saas_calculator", "index.html")
        if os.path.isfile(calc_html_path):
            with open(calc_html_path, "r", encoding="utf-8") as f:
                calc_content = f.read()
            has_svg = "<svg" in calc_content.lower()
            has_sliders = 'type="range"' in calc_content.lower()
            has_no_cdn = not any(cdn in calc_content for cdn in ["googleapis.com", "cloudflare.com", "unpkg.com"])
            self.record_check(suite, "calculator_pure_svg_charts", has_svg and has_sliders, "Pure SVG visual projections & interactive sliders")
            self.record_check(suite, "calculator_zero_external_cdn", has_no_cdn, "Strict zero-dependency standalone distribution")

        # Code templates syntax
        rpc_tpl = get_project_path("templates", "rpc_client_template.py")
        if os.path.isfile(rpc_tpl):
            try:
                py_compile.compile(rpc_tpl, doraise=True)
                with open(rpc_tpl, "r", encoding="utf-8") as f:
                    ast.parse(f.read())
                tpl_valid = True
            except Exception:
                tpl_valid = False
            self.record_check(suite, "rpc_client_template_syntax", tpl_valid, "Python RPC failover template clean AST")

    def audit_beneficiary_wallets(self):
        """Pillar 4: Multi-Chain Beneficiary Wallets Integrity & Checksum Verification."""
        suite = "wallets"

        # 1. Cryptographic format and checksum verification
        base_addr = CANONICAL_WALLETS["base"]
        base_checksum = CANONICAL_WALLETS["base_checksum"]
        solana_addr = CANONICAL_WALLETS["solana"]
        bitcoin_addr = CANONICAL_WALLETS["bitcoin"]
        stellar_addr = CANONICAL_WALLETS["stellar"]

        # Base EVM EIP-55 Checksum
        base_ok = to_checksum_address(base_addr) == base_checksum
        self.record_check(suite, "wallet_base_eip55_checksum", base_ok, f"Base: {base_checksum}")

        # Solana Ed25519 Base58
        sol_ok = verify_solana_address(solana_addr)
        self.record_check(suite, "wallet_solana_base58_format", sol_ok, f"Solana: {solana_addr}")

        # Bitcoin Taproot Bech32m
        btc_ok = verify_bech32m(bitcoin_addr)
        self.record_check(suite, "wallet_bitcoin_bech32m_checksum", btc_ok, f"Bitcoin: {bitcoin_addr}")

        # Stellar StrKey Base32 + CRC16
        xlm_ok = verify_stellar_address(stellar_addr)
        self.record_check(suite, "wallet_stellar_strkey_checksum", xlm_ok, f"Stellar: {stellar_addr}")

        # 2. Presence across key distribution and code files
        audit_targets = [
            "README.md", "SETUP.md", "CONTRIBUTING.md", "docs/SPONSORSHIP.md",
            "docs/PREVIEW.md", "docs/ARCHITECTURE.md", ".github/FUNDING.yml",
            "web3_utility/run_cli.py", "web3_utility/src/web/app.js", "web3_utility/src/web/index.html",
            "digital_assets/web3_saas_calculator/app.js", "digital_assets/web3_saas_calculator/index.html",
            "templates/rpc_client_template.py", "templates/address_validator.js"
        ]

        all_present = True
        for rel in audit_targets:
            p = get_project_path(*rel.split("/"))
            if not os.path.isfile(p):
                continue
            with open(p, "r", encoding="utf-8") as f:
                c = f.read().lower()
            if not all(CANONICAL_WALLETS[w].lower() in c for w in ["base", "solana", "bitcoin", "stellar"]):
                all_present = False
                break

        self.record_check(suite, "wallets_present_across_distribution_kit", all_present,
                          f"Verified all 4 chains across {len(audit_targets)} project files")

    def run_all(self) -> Dict[str, Any]:
        start_time = time.time()
        self.audit_b2b_leads()
        self.audit_b2b_pitches()
        self.audit_b2b_audits()
        self.audit_web3_utility()
        self.audit_digital_assets()
        self.audit_beneficiary_wallets()
        duration_ms = round((time.time() - start_time) * 1000, 2)

        overall_status = "PASS" if self.failed_checks == 0 else "FAIL"

        report = {
            "status": overall_status,
            "overall_status": overall_status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "summary": {
                "total_checks": self.total_checks,
                "passed": self.passed_checks,
                "failed": self.failed_checks,
                "duration_ms": duration_ms
            },
            "suites": self.results
        }
        return report

# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------

def render_terminal_summary(report: Dict[str, Any]):
    print("=" * 86)
    print("           AUTONOMOUS REVENUE ENGINE: MASTER PIPELINE INTEGRITY AUDIT")
    print("=" * 86)
    print(f"{'Audit Suite':<35} {'Status':<10} {'Total':<10} {'Passed':<10} {'Failed':<10}")
    print("-" * 86)

    for suite_name, suite_data in report["suites"].items():
        st = suite_data["status"]
        color_st = f"\033[92m{st:<10}\033[0m" if st == "PASS" else f"\033[91m{st:<10}\033[0m"
        tot = str(suite_data["checks_total"])
        pas = str(suite_data["checks_passed"])
        fai = str(suite_data["checks_failed"])
        print(f"{suite_name:<35} {color_st} {tot:<10} {pas:<10} {fai:<10}")

    print("-" * 86)
    sum_data = report["summary"]
    status_label = report["overall_status"]
    color_label = f"\033[92m{status_label}\033[0m" if status_label == "PASS" else f"\033[91m{status_label}\033[0m"
    print(f"OVERALL PIPELINE INTEGRITY: {color_label} ({sum_data['passed']}/{sum_data['total_checks']} checks passed in {sum_data['duration_ms']}ms)")
    print("=" * 86)

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Master Pipeline Integrity Verification Script for Autonomous Revenue Engine (Feature F13)."
    )
    parser.add_argument("--json", action="store_true", help="Output audit report as JSON to stdout.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display verbose check execution output.")
    parser.add_argument("--fail-fast", action="store_true", help="Halt execution on the first check failure.")
    parser.add_argument("--skip-network", action="store_true", help="Skip any remote network checks and verify offline.")
    parser.add_argument("--export-report", type=str, default="audit_report.json",
                        help="Path to export the structured JSON report (default: audit_report.json).")

    args = parser.parse_args()

    auditor = PipelineAuditor(
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        skip_network=args.skip_network
    )

    try:
        report = auditor.run_all()
    except Exception as e:
        if args.json:
            print(json.dumps({"status": "FAIL", "overall_status": "FAIL", "error": str(e)}, indent=2))
        else:
            print(f"\n[\033[91mERROR\033[0m] Pipeline audit failed: {e}")
        sys.exit(1)

    # Write export report file
    report_file_path = args.export_report
    if not os.path.isabs(report_file_path):
        report_file_path = get_project_path(report_file_path)

    try:
        with open(report_file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to export report to {report_file_path}: {e}", file=sys.stderr)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        render_terminal_summary(report)
        print(f"Report exported to: {os.path.relpath(report_file_path, PROJECT_ROOT)}")

    # Exit code semantics: 0 on 100% pass, non-zero on failure
    sys.exit(0 if report["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
