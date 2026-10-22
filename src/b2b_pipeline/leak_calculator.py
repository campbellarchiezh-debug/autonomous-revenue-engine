"""
Algorithmic conversion leak loss calculator for B2B commercial pipelines.
Pure Python 3.9 standard library implementation with zero external dependencies.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class LeakCalculationResult:
    """Detailed results from conversion leak modeling."""
    monthly_visitors: int
    mobile_share: float
    mobile_visitors: float
    benchmark_conversion_rate: float
    impaired_conversion_rate: float
    baseline_monthly_leads: float
    impaired_monthly_leads: float
    monthly_lost_leads: float
    closing_ratio: float
    monthly_lost_deals: float
    estimated_aov_usd: float
    estimated_monthly_lost_pipeline_usd: float
    estimated_annual_recoverable_usd: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "monthly_visitors": self.monthly_visitors,
            "mobile_share": round(self.mobile_share, 4),
            "mobile_visitors": round(self.mobile_visitors, 2),
            "benchmark_conversion_rate": round(self.benchmark_conversion_rate, 4),
            "impaired_conversion_rate": round(self.impaired_conversion_rate, 4),
            "baseline_monthly_leads": round(self.baseline_monthly_leads, 2),
            "impaired_monthly_leads": round(self.impaired_monthly_leads, 2),
            "monthly_lost_leads": round(self.monthly_lost_leads, 2),
            "closing_ratio": round(self.closing_ratio, 4),
            "monthly_lost_deals": round(self.monthly_lost_deals, 2),
            "estimated_aov_usd": round(self.estimated_aov_usd, 2),
            "estimated_monthly_lost_pipeline_usd": round(self.estimated_monthly_lost_pipeline_usd, 2),
            "estimated_annual_recoverable_usd": round(self.estimated_annual_recoverable_usd, 2),
        }


class ConversionLeakCalculator:
    """
    Calculates quantifiable top-line pipeline loss resulting from mobile conversion friction,
    sub-optimal Core Web Vitals (LCP, CLS), form drop-offs, and delayed speed-to-lead response.
    """

    DEFAULT_MOBILE_SHARE: float = 0.65  # 65% mobile traffic standard in commercial services
    DEFAULT_BENCHMARK_CONVERSION_RATE: float = 0.035  # 3.5% benchmark mobile lead form conversion
    DEFAULT_IMPAIRED_CONVERSION_RATE: float = 0.012  # 1.2% average impaired mobile conversion rate
    DEFAULT_CLOSING_RATIO: float = 0.25  # 25% qualified lead-to-deal close rate

    @classmethod
    def calculate_leak(
        cls,
        monthly_visitors: int,
        estimated_aov: float,
        mobile_share: float = DEFAULT_MOBILE_SHARE,
        benchmark_conversion_rate: float = DEFAULT_BENCHMARK_CONVERSION_RATE,
        impaired_conversion_rate: float = DEFAULT_IMPAIRED_CONVERSION_RATE,
        closing_ratio: float = DEFAULT_CLOSING_RATIO,
    ) -> LeakCalculationResult:
        """
        Executes standard pipeline revenue leakage calculation.

        Formulas:
          mobile_visitors = monthly_visitors * mobile_share
          baseline_leads = mobile_visitors * benchmark_conversion_rate
          impaired_leads = mobile_visitors * impaired_conversion_rate
          lost_leads = max(0.0, baseline_leads - impaired_leads)
          lost_deals = lost_leads * closing_ratio
          monthly_lost_pipeline = lost_deals * estimated_aov
          annual_recoverable = monthly_lost_pipeline * 12
        """
        if monthly_visitors < 0:
            raise ValueError(f"monthly_visitors must be non-negative, got {monthly_visitors}")
        if estimated_aov < 0:
            raise ValueError(f"estimated_aov must be non-negative, got {estimated_aov}")
        if not (0.0 <= mobile_share <= 1.0):
            raise ValueError(f"mobile_share must be between 0.0 and 1.0, got {mobile_share}")
        if not (0.0 <= benchmark_conversion_rate <= 1.0):
            raise ValueError(f"benchmark_conversion_rate must be between 0.0 and 1.0, got {benchmark_conversion_rate}")
        if not (0.0 <= impaired_conversion_rate <= 1.0):
            raise ValueError(f"impaired_conversion_rate must be between 0.0 and 1.0, got {impaired_conversion_rate}")
        if not (0.0 <= closing_ratio <= 1.0):
            raise ValueError(f"closing_ratio must be between 0.0 and 1.0, got {closing_ratio}")

        mobile_visitors = float(monthly_visitors) * mobile_share
        baseline_leads = mobile_visitors * benchmark_conversion_rate
        impaired_leads = mobile_visitors * impaired_conversion_rate
        lost_leads = max(0.0, baseline_leads - impaired_leads)
        lost_deals = lost_leads * closing_ratio
        monthly_lost_pipeline = lost_deals * float(estimated_aov)
        annual_recoverable = monthly_lost_pipeline * 12.0

        return LeakCalculationResult(
            monthly_visitors=monthly_visitors,
            mobile_share=mobile_share,
            mobile_visitors=mobile_visitors,
            benchmark_conversion_rate=benchmark_conversion_rate,
            impaired_conversion_rate=impaired_conversion_rate,
            baseline_monthly_leads=baseline_leads,
            impaired_monthly_leads=impaired_leads,
            monthly_lost_leads=lost_leads,
            closing_ratio=closing_ratio,
            monthly_lost_deals=lost_deals,
            estimated_aov_usd=float(estimated_aov),
            estimated_monthly_lost_pipeline_usd=round(monthly_lost_pipeline, 2),
            estimated_annual_recoverable_usd=round(annual_recoverable, 2),
        )

    @classmethod
    def estimate_impaired_conversion_rate(
        cls,
        mobile_lcp_seconds: float,
        mobile_cls_score: float,
        speed_to_lead_sla_hours: float,
        base_benchmark: float = DEFAULT_BENCHMARK_CONVERSION_RATE,
    ) -> float:
        """
        Dynamically derives the impaired conversion rate based on Core Web Vitals and SLA delays.
        - LCP > 2.5s: 10% penalty per second over 2.5s (capped at 70% reduction)
        - CLS > 0.1: 20% penalty per 0.1 CLS (capped at 50% reduction)
        - Speed to lead SLA > 1 hour: 5% decay per hour (capped at 60% reduction)
        """
        penalty_multiplier = 1.0

        # LCP penalty (Google Core Web Vitals benchmark: <2.5s Good, >4.0s Poor)
        if mobile_lcp_seconds > 2.5:
            lcp_excess = mobile_lcp_seconds - 2.5
            lcp_penalty = min(0.70, lcp_excess * 0.12)
            penalty_multiplier *= (1.0 - lcp_penalty)

        # CLS penalty (Google Core Web Vitals benchmark: <0.1 Good, >0.25 Poor)
        if mobile_cls_score > 0.10:
            cls_excess = (mobile_cls_score - 0.10) / 0.10
            cls_penalty = min(0.50, cls_excess * 0.15)
            penalty_multiplier *= (1.0 - cls_penalty)

        # Speed-to-lead response penalty
        if speed_to_lead_sla_hours > 1.0:
            sla_penalty = min(0.60, (speed_to_lead_sla_hours - 1.0) * 0.03)
            penalty_multiplier *= (1.0 - sla_penalty)

        # Floor conversion rate at 0.005 (0.5%)
        impaired_rate = max(0.005, base_benchmark * penalty_multiplier)
        return round(impaired_rate, 4)

    @classmethod
    def calculate_from_diagnostics(
        cls,
        monthly_visitors: int,
        estimated_aov: float,
        mobile_lcp_seconds: float,
        mobile_cls_score: float,
        speed_to_lead_sla_hours: float,
        mobile_share: float = DEFAULT_MOBILE_SHARE,
        benchmark_conversion_rate: float = DEFAULT_BENCHMARK_CONVERSION_RATE,
        closing_ratio: float = DEFAULT_CLOSING_RATIO,
    ) -> LeakCalculationResult:
        """Calculates revenue leak using empirical diagnostic metrics."""
        impaired_rate = cls.estimate_impaired_conversion_rate(
            mobile_lcp_seconds=mobile_lcp_seconds,
            mobile_cls_score=mobile_cls_score,
            speed_to_lead_sla_hours=speed_to_lead_sla_hours,
            base_benchmark=benchmark_conversion_rate,
        )
        return cls.calculate_leak(
            monthly_visitors=monthly_visitors,
            estimated_aov=estimated_aov,
            mobile_share=mobile_share,
            benchmark_conversion_rate=benchmark_conversion_rate,
            impaired_conversion_rate=impaired_rate,
            closing_ratio=closing_ratio,
        )
