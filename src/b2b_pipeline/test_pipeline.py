"""
Unit test suite for B2B pipeline models, leak calculator, generator, and data assets.
Pure Python 3.9 standard library unittest with zero external dependencies.
"""

import csv
import json
import os
import unittest
from pathlib import Path

from src.b2b_pipeline.models import (
    DecisionMaker,
    Diagnostics,
    FinancialImpact,
    OutreachAssets,
    LeadTarget,
    LeadDataset,
)
from src.b2b_pipeline.leak_calculator import (
    ConversionLeakCalculator,
    LeakCalculationResult,
)
from src.b2b_pipeline.generator import (
    B2BPipelineGenerator,
    CANONICAL_TARGETS_RAW,
)


class TestB2BModels(unittest.TestCase):
    """Tests for dataclass models, validation rules, and serialization."""

    def test_decision_maker_valid(self):
        dm = DecisionMaker(
            name="John Smith",
            title="CEO",
            email="john@example.com",
            phone="(555) 123-4567",
            linkedin_url="https://linkedin.com/in/johnsmith",
        )
        errors = dm.validate()
        self.assertEqual(len(errors), 0)
        d = dm.to_dict()
        self.assertEqual(d["name"], "John Smith")
        reconstructed = DecisionMaker.from_dict(d)
        self.assertEqual(reconstructed.email, "john@example.com")

    def test_decision_maker_invalid_email(self):
        dm = DecisionMaker(
            name="John Smith",
            title="CEO",
            email="invalid-email",
            phone="(555) 123-4567",
            linkedin_url="https://linkedin.com/in/johnsmith",
        )
        errors = dm.validate()
        self.assertTrue(any("Invalid email" in e for e in errors))

    def test_diagnostics_validation(self):
        diag = Diagnostics(
            primary_leak_summary="High LCP",
            primary_leak_technical_detail="38MB video",
            secondary_leak_summary="Unclickable phone",
            mobile_lcp_seconds=6.8,
            mobile_cls_score=0.05,
            speed_to_lead_sla_hours=18.0,
        )
        self.assertEqual(len(diag.validate()), 0)

        bad_diag = Diagnostics(
            primary_leak_summary="",
            primary_leak_technical_detail="",
            secondary_leak_summary="",
            mobile_lcp_seconds=-1.0,
            mobile_cls_score=-0.5,
            speed_to_lead_sla_hours=-2.0,
        )
        errors = bad_diag.validate()
        self.assertGreaterEqual(len(errors), 4)

    def test_financial_impact_validation(self):
        fin = FinancialImpact(
            estimated_monthly_lost_pipeline_usd=100000.0,
            estimated_annual_recoverable_usd=1200000.0,
        )
        self.assertEqual(len(fin.validate()), 0)

        mismatched_fin = FinancialImpact(
            estimated_monthly_lost_pipeline_usd=100000.0,
            estimated_annual_recoverable_usd=500000.0,
        )
        errors = mismatched_fin.validate()
        self.assertTrue(any("must equal 12x" in e for e in errors))

    def test_lead_target_validation(self):
        raw = CANONICAL_TARGETS_RAW[0]
        target = LeadTarget.from_dict(raw)
        errors = target.validate()
        self.assertEqual(len(errors), 0)
        self.assertEqual(target.target_id, "TGT-001")
        self.assertGreaterEqual(target.estimated_aov, 5000.0)

    def test_lead_target_invalid_id(self):
        raw = dict(CANONICAL_TARGETS_RAW[0])
        raw["target_id"] = "INVALID-ID"
        target = LeadTarget.from_dict(raw)
        errors = target.validate()
        self.assertTrue(any("expected pattern 'TGT-###'" in e for e in errors))


class TestConversionLeakCalculator(unittest.TestCase):
    """Tests for mathematical leak calculation formulas and boundary cases."""

    def test_standard_leak_calculation(self):
        result = ConversionLeakCalculator.calculate_leak(
            monthly_visitors=3200,
            estimated_aov=28500.0,
            mobile_share=0.65,
            benchmark_conversion_rate=0.035,
            impaired_conversion_rate=0.012,
            closing_ratio=0.25,
        )
        self.assertIsInstance(result, LeakCalculationResult)
        self.assertEqual(result.monthly_visitors, 3200)
        self.assertAlmostEqual(result.mobile_visitors, 2080.0, places=1)
        self.assertAlmostEqual(result.baseline_monthly_leads, 72.8, places=1)
        self.assertAlmostEqual(result.impaired_monthly_leads, 24.96, places=2)
        self.assertGreater(result.estimated_monthly_lost_pipeline_usd, 0.0)
        self.assertAlmostEqual(
            result.estimated_annual_recoverable_usd,
            result.estimated_monthly_lost_pipeline_usd * 12.0,
            places=1,
        )

    def test_boundary_zero_visitors(self):
        result = ConversionLeakCalculator.calculate_leak(
            monthly_visitors=0,
            estimated_aov=25000.0,
        )
        self.assertEqual(result.estimated_monthly_lost_pipeline_usd, 0.0)
        self.assertEqual(result.estimated_annual_recoverable_usd, 0.0)

    def test_negative_inputs_raise_value_error(self):
        with self.assertRaises(ValueError):
            ConversionLeakCalculator.calculate_leak(monthly_visitors=-100, estimated_aov=20000.0)
        with self.assertRaises(ValueError):
            ConversionLeakCalculator.calculate_leak(monthly_visitors=1000, estimated_aov=-500.0)

    def test_estimate_impaired_conversion_rate(self):
        good_rate = ConversionLeakCalculator.estimate_impaired_conversion_rate(
            mobile_lcp_seconds=1.8,
            mobile_cls_score=0.04,
            speed_to_lead_sla_hours=0.2,
        )
        self.assertEqual(good_rate, 0.035)

        poor_rate = ConversionLeakCalculator.estimate_impaired_conversion_rate(
            mobile_lcp_seconds=6.8,
            mobile_cls_score=0.25,
            speed_to_lead_sla_hours=18.0,
        )
        self.assertLess(poor_rate, 0.02)
        self.assertGreaterEqual(poor_rate, 0.005)


class TestB2BGeneratorAndAssets(unittest.TestCase):
    """Tests for generated datasets, CSV integrity, schema compliance, and pitch scripts."""

    @classmethod
    def setUpClass(cls):
        cls.generator = B2BPipelineGenerator()
        cls.dataset, cls.errors = cls.generator.write_all()

    def test_generation_clean(self):
        self.assertEqual(len(self.errors), 0, f"Generator reported errors: {self.errors}")
        self.assertEqual(len(self.dataset.targets), 15)

    def test_target_verticals_coverage(self):
        verticals = {t.vertical for t in self.dataset.targets}
        self.assertEqual(len(verticals), 5, f"Expected 5 distinct verticals, found {len(verticals)}")

    def test_json_dataset_matches_models(self):
        with open(self.generator.dataset_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["total_targets"], 15)
        self.assertEqual(len(data["targets"]), 15)
        for t in data["targets"]:
            self.assertIn("target_id", t)
            self.assertIn("company_name", t)
            self.assertIn("website_url", t)
            self.assertIn("decision_maker", t)
            self.assertIn("estimated_monthly_lost_pipeline", t)
            self.assertIn("tailored_pitch_file", t)
            self.assertIn("audit_report_file", t)

    def test_csv_export_format(self):
        with open(self.generator.csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 15)
        for row in rows:
            self.assertTrue(row["target_id"].startswith("TGT-"))
            self.assertTrue(row["dm_email"].find("@") > 0)
            self.assertGreater(float(row["estimated_aov_usd"]), 5000)

    def test_pitch_scripts_word_count(self):
        """Verifies all 15 pitch scripts fall strictly within 160-260 words."""
        pitches = list(self.generator.pitches_dir.glob("*.md"))
        self.assertEqual(len(pitches), 15)
        for pf in pitches:
            words = len(pf.read_text().split())
            self.assertGreaterEqual(words, 160, f"{pf.name} word count {words} < 160")
            self.assertLessEqual(words, 260, f"{pf.name} word count {words} > 260")

    def test_audit_reports_completeness(self):
        """Verifies all 15 audit reports contain required sections and technical details."""
        audits = list(self.generator.audits_dir.glob("*.md"))
        self.assertEqual(len(audits), 15)
        for af in audits:
            text = af.read_text()
            self.assertIn("Executive Financial Summary", text)
            self.assertIn("Core Web Vitals & Mobile Diagnostics", text)
            self.assertIn("Three-Phase Technical Remediation Plan", text)
            self.assertGreaterEqual(len(text.split()), 350)


if __name__ == "__main__":
    unittest.main()
