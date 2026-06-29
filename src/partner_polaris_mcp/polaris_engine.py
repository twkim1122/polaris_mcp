"""Core Polaris level calculation engine.

Implements the official dual-condition Polaris framework:
- Condition 1: Total certifications >= tier-specific threshold
- Condition 2: Engagement Points >= tier-specific threshold

Reference: Partner Polaris_Oct 2025.docx, Section 5 (Final Polaris Level Definitions)
"""

import json
import os
from pathlib import Path
from .models import PartnerData, PolarisResult

# Load criteria from JSON config
DATA_DIR = Path(os.environ.get("POLARIS_DATA_DIR", Path(__file__).parent.parent.parent / "data"))


def load_criteria() -> dict:
    """Load Polaris criteria from JSON configuration file."""
    criteria_path = DATA_DIR / "polaris_criteria.json"
    if criteria_path.exists():
        with open(criteria_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Fallback defaults if file not found
    return {
        "tiers": {
            "Select": {"l2": {"min_certs": 5, "min_l2_pts": 5}, "l3": {"min_certs": 20, "min_l3_pts": 20}},
            "Advanced": {"l2": {"min_certs": 10, "min_l2_pts": 10}, "l3": {"min_certs": 40, "min_l3_pts": 40}},
            "Premier": {"l2": {"min_certs": 100, "min_l2_pts": 100}, "l3": {"min_certs": 400, "min_l3_pts": 400}},
        }
    }


CRITERIA = load_criteria()


def calculate_l2_points(total_certs: int, ilt_total: int, sb_sub: int) -> int:
    """Calculate L2 engagement points.
    
    L2 pts = total_certs + ILT_seats + (SB_subscription / 5)
    """
    return total_certs + ilt_total + (sb_sub // 5)


def calculate_l3_points(int_plus_certs: int, int_plus_ilt: int, hands_on_sb: int) -> int:
    """Calculate L3 engagement points.
    
    L3 pts = Int+ certs + Int+ ILT seats + (hands_on_SB / 5)
    """
    return int_plus_certs + int_plus_ilt + (hands_on_sb // 5)


def determine_level(tier: str, total_certs: int, l2_pts: int, l3_pts: int) -> str:
    """Determine Polaris level based on dual-condition criteria.
    
    Both conditions must be met simultaneously for a given level.
    Checks L3 first (highest), then L2, then L1, then L0.
    """
    tiers = CRITERIA.get("tiers", {})
    tier_config = tiers.get(tier)
    
    if tier_config is None:
        # Registered partners: use Select thresholds as fallback (Customer Polaris)
        tier_config = tiers.get("Select", {"l2": {"min_certs": 5, "min_l2_pts": 5}, "l3": {"min_certs": 20, "min_l3_pts": 20}})
    
    # Check L3
    l3 = tier_config["l3"]
    if total_certs >= l3["min_certs"] and l3_pts >= l3["min_l3_pts"]:
        return "L3"
    
    # Check L2
    l2 = tier_config["l2"]
    if total_certs >= l2["min_certs"] and l2_pts >= l2["min_l2_pts"]:
        return "L2"
    
    # L1: any engagement
    if total_certs > 0:
        return "L1"
    
    return "L0"


def classify_priority(level: str, cert_gap: int, pts_gap: int, tier: str) -> str:
    """Classify partner into priority bucket for L3 uplevel."""
    if level == "L3":
        return "maintain"
    
    # Quick-win: L3 pts already met AND cert gap <= 5
    if pts_gap <= 0 and cert_gap <= 5:
        return "quick-win"
    
    # High: small gap (cert gap <= 20 or pts gap <= 10)
    if cert_gap <= 20 and pts_gap <= 10:
        return "high"
    
    # Premier with large gap is long-term
    if tier == "Premier" and cert_gap > 200:
        return "low"
    
    return "medium"


def estimate_active_certs(ttm_certs: int, growth_rate: float = 0.2) -> int:
    """Estimate 3-year cumulative active certifications.
    
    Assumes declining growth rate over prior years:
    Active = TTM + TTM*(1-growth) + TTM*(1-growth)^2
    ≈ TTM * 2.4 for 20% growth
    """
    if ttm_certs <= 0:
        return 0
    year_2 = ttm_certs * (1 - growth_rate)
    year_3 = ttm_certs * (1 - growth_rate) ** 2
    return round(ttm_certs + year_2 + year_3)


def analyze_partner(partner: PartnerData) -> PolarisResult:
    """Full Polaris analysis for a single partner.
    
    Returns PolarisResult with level, points, progress, gap, and priority.
    """
    # Calculate points
    l2_pts = calculate_l2_points(
        partner.total_certs_ttm,
        partner.ilt_sessions_total,
        partner.sb_subscription_engagements
    )
    l3_pts = calculate_l3_points(
        partner.int_plus_certs,
        partner.ilt_sessions_int_plus,
        partner.sb_hands_on_completions
    )
    
    # Determine level
    level = determine_level(partner.tier, partner.total_certs_ttm, l2_pts, l3_pts)
    
    # Get thresholds for gap calculation
    tiers = CRITERIA.get("tiers", {})
    tier_config = tiers.get(partner.tier, tiers.get("Select"))
    l3_cert_threshold = tier_config["l3"]["min_certs"]
    l3_pts_threshold = tier_config["l3"]["min_l3_pts"]
    
    # Calculate gaps and progress
    cert_gap = max(0, l3_cert_threshold - partner.total_certs_ttm)
    pts_gap = max(0, l3_pts_threshold - l3_pts)
    cert_progress = min(100.0, round(partner.total_certs_ttm / l3_cert_threshold * 100, 1))
    pts_progress = min(100.0, round(l3_pts / l3_pts_threshold * 100, 1))
    
    # Active cert
    active_3y = partner.active_certs_3y if partner.active_certs_3y > 0 else estimate_active_certs(partner.total_certs_ttm)
    active_l3_ready = active_3y >= l3_cert_threshold
    
    # Priority
    priority = classify_priority(level, cert_gap, pts_gap, partner.tier)
    
    return PolarisResult(
        partner_name=partner.partner_name,
        tier=partner.tier,
        country=partner.country,
        polaris_level=level,
        ttm_certs=partner.total_certs_ttm,
        int_plus_certs=partner.int_plus_certs,
        int_plus_ratio=partner.int_plus_ratio,
        l2_pts=l2_pts,
        l3_pts=l3_pts,
        l3_cert_threshold=l3_cert_threshold,
        l3_pts_threshold=l3_pts_threshold,
        cert_progress_pct=cert_progress,
        pts_progress_pct=pts_progress,
        cert_gap=cert_gap,
        pts_gap=pts_gap,
        active_cert_3y=active_3y,
        active_cert_l3_ready=active_l3_ready,
        priority=priority
    )
