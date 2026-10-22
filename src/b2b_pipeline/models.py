"""
Data models for B2B Lead Sourcing & Conversion Leak Audit Pipeline.
Pure Python 3.9 standard library implementation with zero external dependencies.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import re
from urllib.parse import urlparse

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
TARGET_ID_REGEX = re.compile(r"^TGT-\d{3}$")


@dataclass
class DecisionMaker:
    """Decision maker contact information."""
    name: str
    title: str
    email: str
    phone: str
    linkedin_url: str

    def validate(self) -> List[str]:
        errors = []
        if not self.name or not self.name.strip():
            errors.append("Decision maker name is required.")
        if not self.title or not self.title.strip():
            errors.append("Decision maker title is required.")
        if not self.email or not EMAIL_REGEX.match(self.email.strip()):
            errors.append(f"Invalid email address: '{self.email}'.")
        if not self.phone or not self.phone.strip():
            errors.append("Decision maker phone is required.")
        if not self.linkedin_url or not self.linkedin_url.strip():
            errors.append("LinkedIn URL is required.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionMaker":
        return cls(
            name=str(data.get("name", "")).strip(),
            title=str(data.get("title", "")).strip(),
            email=str(data.get("email", "")).strip(),
            phone=str(data.get("phone", "")).strip(),
            linkedin_url=str(data.get("linkedin_url", "")).strip(),
        )


@dataclass
class Diagnostics:
    """Technical and UX diagnostic metrics."""
    primary_leak_summary: str
    primary_leak_technical_detail: str
    secondary_leak_summary: str
    mobile_lcp_seconds: float
    mobile_cls_score: float
    speed_to_lead_sla_hours: float

    def validate(self) -> List[str]:
        errors = []
        if not self.primary_leak_summary:
            errors.append("Primary leak summary is required.")
        if not self.primary_leak_technical_detail:
            errors.append("Primary leak technical detail is required.")
        if not self.secondary_leak_summary:
            errors.append("Secondary leak summary is required.")
        if self.mobile_lcp_seconds < 0:
            errors.append("Mobile LCP seconds must be non-negative.")
        if self.mobile_cls_score < 0:
            errors.append("Mobile CLS score must be non-negative.")
        if self.speed_to_lead_sla_hours < 0:
            errors.append("Speed to lead SLA hours must be non-negative.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diagnostics":
        return cls(
            primary_leak_summary=str(data.get("primary_leak_summary", "")),
            primary_leak_technical_detail=str(data.get("primary_leak_technical_detail", "")),
            secondary_leak_summary=str(data.get("secondary_leak_summary", "")),
            mobile_lcp_seconds=float(data.get("mobile_lcp_seconds", 0.0)),
            mobile_cls_score=float(data.get("mobile_cls_score", 0.0)),
            speed_to_lead_sla_hours=float(data.get("speed_to_lead_sla_hours", 0.0)),
        )


@dataclass
class FinancialImpact:
    """Calculated financial impact of conversion leaks."""
    estimated_monthly_lost_pipeline_usd: float
    estimated_annual_recoverable_usd: float

    def validate(self) -> List[str]:
        errors = []
        if self.estimated_monthly_lost_pipeline_usd < 0:
            errors.append("Monthly lost pipeline must be non-negative.")
        if self.estimated_annual_recoverable_usd < 0:
            errors.append("Annual recoverable revenue must be non-negative.")
        expected_annual = round(self.estimated_monthly_lost_pipeline_usd * 12.0, 2)
        actual_annual = round(self.estimated_annual_recoverable_usd, 2)
        if abs(expected_annual - actual_annual) > 1.0:
            errors.append(
                f"Annual recoverable ({actual_annual}) must equal 12x monthly lost pipeline ({expected_annual})."
            )
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialImpact":
        return cls(
            estimated_monthly_lost_pipeline_usd=float(data.get("estimated_monthly_lost_pipeline_usd", 0.0)),
            estimated_annual_recoverable_usd=float(data.get("estimated_annual_recoverable_usd", 0.0)),
        )


@dataclass
class OutreachAssets:
    """Outreach campaign copy and pitch outlines."""
    email_subject: str
    email_body_template: str
    video_script_90sec: str

    def validate(self) -> List[str]:
        errors = []
        if not self.email_subject:
            errors.append("Email subject is required.")
        if not self.email_body_template:
            errors.append("Email body template is required.")
        if not self.video_script_90sec:
            errors.append("Video script is required.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutreachAssets":
        return cls(
            email_subject=str(data.get("email_subject", "")),
            email_body_template=str(data.get("email_body_template", "")),
            video_script_90sec=str(data.get("video_script_90sec", "")),
        )


@dataclass
class LeadTarget:
    """B2B commercial target entity."""
    target_id: str
    company_name: str
    vertical: str
    headquarters: str
    website_url: str
    estimated_aov: float
    estimated_monthly_visitors: int
    estimated_ad_spend_monthly: float
    decision_maker: DecisionMaker
    primary_conversion_leak: str
    secondary_conversion_leak: str
    estimated_monthly_lost_pipeline: float
    tailored_pitch_file: str
    audit_report_file: str
    specialization: Optional[str] = None
    # Supplementary fields for multi-spec alignment
    domain_url: Optional[str] = None
    estimated_aov_usd: Optional[float] = None
    monthly_visitors: Optional[int] = None
    estimated_monthly_ad_spend_usd: Optional[float] = None
    estimated_annual_recoverable: Optional[float] = None
    diagnostics: Optional[Diagnostics] = None
    financial_impact: Optional[FinancialImpact] = None
    outreach_assets: Optional[OutreachAssets] = None

    def __post_init__(self):
        if self.domain_url is None:
            self.domain_url = self.website_url
        if self.estimated_aov_usd is None:
            self.estimated_aov_usd = self.estimated_aov
        if self.monthly_visitors is None:
            self.monthly_visitors = self.estimated_monthly_visitors
        if self.estimated_monthly_ad_spend_usd is None:
            self.estimated_monthly_ad_spend_usd = self.estimated_ad_spend_monthly
        if self.estimated_annual_recoverable is None:
            self.estimated_annual_recoverable = round(self.estimated_monthly_lost_pipeline * 12.0, 2)

    def validate(self) -> List[str]:
        errors = []
        if not TARGET_ID_REGEX.match(self.target_id):
            errors.append(f"Invalid target_id '{self.target_id}', expected pattern 'TGT-###'.")
        if not self.company_name:
            errors.append("company_name is required.")
        if not self.vertical:
            errors.append("vertical is required.")
        if not self.headquarters:
            errors.append("headquarters is required.")

        parsed_url = urlparse(self.website_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            errors.append(f"Invalid website_url: '{self.website_url}'.")

        if self.estimated_aov < 5000:
            errors.append(f"estimated_aov ({self.estimated_aov}) must be >= 5000 for high-ticket B2B.")
        if self.estimated_monthly_visitors < 500:
            errors.append(f"estimated_monthly_visitors ({self.estimated_monthly_visitors}) must be >= 500.")
        if self.estimated_ad_spend_monthly < 0:
            errors.append("estimated_ad_spend_monthly must be non-negative.")
        if self.estimated_monthly_lost_pipeline < 0:
            errors.append("estimated_monthly_lost_pipeline must be non-negative.")

        errors.extend(self.decision_maker.validate())
        if self.diagnostics:
            errors.extend(self.diagnostics.validate())
        if self.financial_impact:
            errors.extend(self.financial_impact.validate())
        if self.outreach_assets:
            errors.extend(self.outreach_assets.validate())

        return errors

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "target_id": self.target_id,
            "company_name": self.company_name,
            "vertical": self.vertical,
            "headquarters": self.headquarters,
            "website_url": self.website_url,
            "domain_url": self.domain_url or self.website_url,
            "estimated_aov": float(self.estimated_aov),
            "estimated_aov_usd": float(self.estimated_aov_usd if self.estimated_aov_usd is not None else self.estimated_aov),
            "estimated_monthly_visitors": int(self.estimated_monthly_visitors),
            "monthly_visitors": int(self.monthly_visitors if self.monthly_visitors is not None else self.estimated_monthly_visitors),
            "estimated_ad_spend_monthly": float(self.estimated_ad_spend_monthly),
            "estimated_monthly_ad_spend_usd": float(
                self.estimated_monthly_ad_spend_usd if self.estimated_monthly_ad_spend_usd is not None else self.estimated_ad_spend_monthly
            ),
            "decision_maker": self.decision_maker.to_dict(),
            "primary_conversion_leak": self.primary_conversion_leak,
            "secondary_conversion_leak": self.secondary_conversion_leak,
            "estimated_monthly_lost_pipeline": float(self.estimated_monthly_lost_pipeline),
            "estimated_annual_recoverable": float(
                self.estimated_annual_recoverable if self.estimated_annual_recoverable is not None else self.estimated_monthly_lost_pipeline * 12.0
            ),
            "tailored_pitch_file": self.tailored_pitch_file,
            "audit_report_file": self.audit_report_file,
        }
        if self.diagnostics:
            data["diagnostics"] = self.diagnostics.to_dict()
        if self.financial_impact:
            data["financial_impact"] = self.financial_impact.to_dict()
        if self.outreach_assets:
            data["outreach_assets"] = self.outreach_assets.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeadTarget":
        dm_data = data.get("decision_maker", {})
        dm = DecisionMaker.from_dict(dm_data)

        diag = Diagnostics.from_dict(data["diagnostics"]) if "diagnostics" in data else None
        fin = FinancialImpact.from_dict(data["financial_impact"]) if "financial_impact" in data else None
        outreach = OutreachAssets.from_dict(data["outreach_assets"]) if "outreach_assets" in data else None

        aov = float(data.get("estimated_aov", data.get("estimated_aov_usd", 0.0)))
        visitors = int(data.get("estimated_monthly_visitors", data.get("monthly_visitors", 0)))
        ad_spend = float(data.get("estimated_ad_spend_monthly", data.get("estimated_monthly_ad_spend_usd", 0.0)))
        lost_pipeline = float(
            data.get(
                "estimated_monthly_lost_pipeline",
                fin.estimated_monthly_lost_pipeline_usd if fin else 0.0,
            )
        )

        return cls(
            target_id=str(data.get("target_id", "")),
            company_name=str(data.get("company_name", "")),
            vertical=str(data.get("vertical", "")),
            headquarters=str(data.get("headquarters", "")),
            website_url=str(data.get("website_url", data.get("domain_url", ""))),
            domain_url=str(data.get("domain_url", data.get("website_url", ""))),
            estimated_aov=aov,
            estimated_aov_usd=aov,
            estimated_monthly_visitors=visitors,
            monthly_visitors=visitors,
            estimated_ad_spend_monthly=ad_spend,
            estimated_monthly_ad_spend_usd=ad_spend,
            decision_maker=dm,
            primary_conversion_leak=str(data.get("primary_conversion_leak", "")),
            secondary_conversion_leak=str(data.get("secondary_conversion_leak", "")),
            estimated_monthly_lost_pipeline=lost_pipeline,
            estimated_annual_recoverable=float(
                data.get("estimated_annual_recoverable", round(lost_pipeline * 12.0, 2))
            ),
            tailored_pitch_file=str(data.get("tailored_pitch_file", "")),
            audit_report_file=str(data.get("audit_report_file", "")),
            diagnostics=diag,
            financial_impact=fin,
            outreach_assets=outreach,
        )


@dataclass
class LeadDataset:
    """Master container for the B2B lead generation dataset."""
    version: str
    generated_at: str
    total_targets: int
    targets: List[LeadTarget] = field(default_factory=list)

    def validate(self) -> List[str]:
        errors = []
        if not self.version:
            errors.append("Dataset version is required.")
        if not self.generated_at:
            errors.append("generated_at timestamp is required.")
        if len(self.targets) < 15:
            errors.append(f"Dataset must contain at least 15 targets, found {len(self.targets)}.")
        if self.total_targets != len(self.targets):
            errors.append(f"total_targets ({self.total_targets}) does not match targets count ({len(self.targets)}).")

        seen_ids = set()
        for idx, target in enumerate(self.targets):
            t_errors = target.validate()
            for err in t_errors:
                errors.append(f"Target [{target.target_id or idx}]: {err}")
            if target.target_id in seen_ids:
                errors.append(f"Duplicate target_id '{target.target_id}' found.")
            seen_ids.add(target.target_id)

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "total_targets": len(self.targets),
            "targets": [t.to_dict() for t in self.targets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeadDataset":
        targets = [LeadTarget.from_dict(t) for t in data.get("targets", [])]
        return cls(
            version=str(data.get("version", "1.0.0")),
            generated_at=str(data.get("generated_at", "")),
            total_targets=int(data.get("total_targets", len(targets))),
            targets=targets,
        )
