"""Data models for Partner Polaris MCP Server."""

from dataclasses import dataclass, field
from typing import Optional, Literal


@dataclass
class PartnerData:
    """Raw partner training/certification data."""
    partner_name: str
    tier: str  # Premier, Advanced, Select, Registered
    country: str
    total_certs_ttm: int = 0
    foundational_certs: int = 0
    associate_certs: int = 0
    professional_certs: int = 0
    specialty_certs: int = 0
    ilt_sessions_total: int = 0
    ilt_sessions_int_plus: int = 0
    sb_subscription_engagements: int = 0
    sb_hands_on_completions: int = 0
    active_certs_3y: int = 0

    @property
    def int_plus_certs(self) -> int:
        return self.associate_certs + self.professional_certs + self.specialty_certs

    @property
    def int_plus_ratio(self) -> float:
        if self.total_certs_ttm == 0:
            return 0.0
        return round(self.int_plus_certs / self.total_certs_ttm * 100, 1)


@dataclass
class PolarisResult:
    """Result of Polaris level calculation."""
    partner_name: str
    tier: str
    country: str
    polaris_level: str  # L0, L1, L2, L3
    ttm_certs: int
    int_plus_certs: int
    int_plus_ratio: float
    l2_pts: int
    l3_pts: int
    l3_cert_threshold: int
    l3_pts_threshold: int
    cert_progress_pct: float
    pts_progress_pct: float
    cert_gap: int
    pts_gap: int
    active_cert_3y: int
    active_cert_l3_ready: bool
    priority: str  # quick-win, high, medium, maintain, low


@dataclass
class GapAnalysisResult:
    """L3 gap analysis with recommendations."""
    partner_name: str
    country: str
    tier: str
    current_level: str
    cert_gap: int
    pts_gap: int
    cert_progress_pct: float
    pts_progress_pct: float
    bottleneck: str  # certifications, points, both, none
    active_cert_context: dict = field(default_factory=dict)
    recommendations: list = field(default_factory=list)
    timeline: str = ""
    priority: str = ""


@dataclass
class BenchmarkEntry:
    """Country-level benchmark data."""
    country: str
    total_partners: int = 0
    total_certs_ttm: int = 0
    training_engagements: int = 0
    int_plus_ratio: float = 0.0
    l3_count: int = 0
    l2_count: int = 0
    l1_count: int = 0
    l0_count: int = 0
    active_cert_total: int = 0
