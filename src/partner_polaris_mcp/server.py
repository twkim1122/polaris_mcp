"""Partner Polaris MCP Server.

Exposes 5 tools via FastMCP for partner Polaris level analysis:
1. get_polaris_status - Query partner Polaris levels by country
2. calculate_polaris_level - Calculate level from input data
3. get_l3_gap_analysis - L3 gap analysis with action guide
4. get_polaris_benchmark - Cross-country benchmark comparison
5. get_polaris_criteria - Official Polaris framework criteria
"""

import json
from dataclasses import asdict
from mcp.server.fastmcp import FastMCP

from .polaris_engine import (
    analyze_partner, calculate_l2_points, calculate_l3_points,
    determine_level, estimate_active_certs, CRITERIA
)
from .gap_analyzer import analyze_gap
from .benchmark import generate_benchmark
from .data_loader import (
    load_partners_by_country, find_partner, get_available_countries,
    get_data_info, clear_cache
)
from .models import PartnerData

# Initialize FastMCP server
mcp = FastMCP(
    "partner-polaris",
    description="Partner Polaris Level Analysis - Query, calculate, and benchmark AWS partner training depth using the Polaris framework."
)


@mcp.tool()
def get_polaris_status(
    country: str,
    partner_name: str = "",
    tier: str = "",
    include_active_cert: bool = True
) -> str:
    """Get current Polaris level status for partners in a country.
    
    Returns partner list with Polaris level, TTM certifications, Int+ ratio,
    L3 Engagement Points, Active Cert (3Y), and priority classification.
    
    Args:
        country: Country name (e.g., "Korea", "Japan", "India")
        partner_name: Optional specific partner name filter
        tier: Optional tier filter ("Premier", "Advanced", "Select")
        include_active_cert: Include 3Y Active Cert supplemental metric
    """
    partners = load_partners_by_country(country)
    
    if not partners:
        available = get_available_countries()
        return json.dumps({
            "error": f"No data found for country '{country}'",
            "available_countries": available
        }, indent=2)
    
    # Apply filters
    if partner_name:
        partners = [p for p in partners if partner_name.lower() in p.partner_name.lower()]
    if tier:
        partners = [p for p in partners if p.tier.lower() == tier.lower()]
    
    # Analyze each partner
    results = [analyze_partner(p) for p in partners]
    results.sort(key=lambda r: r.ttm_certs, reverse=True)
    
    # Summary
    total_certs = sum(r.ttm_certs for r in results)
    total_int = sum(r.int_plus_certs for r in results)
    
    output = {
        "country": country,
        "period": "TTM (Trailing 12 Months)",
        "summary": {
            "total_partners": len(results),
            "l3_count": sum(1 for r in results if r.polaris_level == "L3"),
            "l2_count": sum(1 for r in results if r.polaris_level == "L2"),
            "l1_count": sum(1 for r in results if r.polaris_level == "L1"),
            "l0_count": sum(1 for r in results if r.polaris_level == "L0"),
            "total_certs_ttm": total_certs,
            "int_plus_ratio": round(total_int / total_certs * 100, 1) if total_certs > 0 else 0,
            "quick_win_partners": sum(1 for r in results if r.priority == "quick-win"),
        },
        "partners": []
    }
    
    for r in results:
        partner_dict = {
            "name": r.partner_name,
            "tier": r.tier,
            "polaris_level": r.polaris_level,
            "ttm_certs": r.ttm_certs,
            "int_plus_certs": r.int_plus_certs,
            "int_plus_ratio": r.int_plus_ratio,
            "l3_pts": r.l3_pts,
            "cert_progress_pct": r.cert_progress_pct,
            "pts_progress_pct": r.pts_progress_pct,
            "cert_gap": r.cert_gap,
            "pts_gap": r.pts_gap,
            "priority": r.priority,
        }
        if include_active_cert:
            partner_dict["active_cert_3y"] = r.active_cert_3y
            partner_dict["active_cert_l3_ready"] = r.active_cert_l3_ready
        
        output["partners"].append(partner_dict)
    
    return json.dumps(output, indent=2, ensure_ascii=False)


@mcp.tool()
def calculate_polaris_level(
    tier: str,
    total_certs_ttm: int,
    int_plus_certs: int,
    ilt_sessions: int = 0,
    sb_hands_on: int = 0,
    partner_name: str = ""
) -> str:
    """Calculate Polaris level from input data (for simulation/what-if scenarios).
    
    Applies the official dual-condition criteria:
    - Condition 1: Total certifications >= tier threshold
    - Condition 2: L3 Engagement Points >= tier threshold
    
    Args:
        tier: Partner tier - "Premier", "Advanced", or "Select"
        total_certs_ttm: Total certifications obtained in TTM period
        int_plus_certs: Int+ (Associate+Professional+Specialty) certifications
        ilt_sessions: Int+ ILT sessions attended (default: 0)
        sb_hands_on: SB Hands-on (Labs/Games/JAMs) completions (default: 0)
        partner_name: Optional partner name for context
    """
    # Validate tier
    valid_tiers = ["Premier", "Advanced", "Select", "Registered"]
    if tier not in valid_tiers:
        return json.dumps({"error": f"Invalid tier '{tier}'. Must be one of: {valid_tiers}"})
    
    # Calculate points
    l2_pts = calculate_l2_points(total_certs_ttm, ilt_sessions, 0)
    l3_pts = calculate_l3_points(int_plus_certs, ilt_sessions, sb_hands_on)
    
    # Determine level
    level = determine_level(tier, total_certs_ttm, l2_pts, l3_pts)
    
    # Get thresholds
    tiers_config = CRITERIA.get("tiers", {})
    tier_config = tiers_config.get(tier, tiers_config.get("Select"))
    l3_cert_req = tier_config["l3"]["min_certs"]
    l3_pts_req = tier_config["l3"]["min_l3_pts"]
    
    cert_gap = max(0, l3_cert_req - total_certs_ttm)
    pts_gap = max(0, l3_pts_req - l3_pts)
    cert_progress = min(100, round(total_certs_ttm / l3_cert_req * 100, 1))
    pts_progress = min(100, round(l3_pts / l3_pts_req * 100, 1))
    
    # Active cert estimate
    active_est = estimate_active_certs(total_certs_ttm)
    
    output = {
        "partner_name": partner_name or "Unnamed",
        "tier": tier,
        "polaris_level": level,
        "details": {
            "total_certs": total_certs_ttm,
            "int_plus_certs": int_plus_certs,
            "l2_pts_calculated": l2_pts,
            "l3_pts_calculated": l3_pts,
            "l3_cert_threshold": l3_cert_req,
            "l3_pts_threshold": l3_pts_req,
            "cert_progress_pct": cert_progress,
            "pts_progress_pct": pts_progress,
            "cert_gap": cert_gap,
            "pts_gap": pts_gap,
            "active_cert_estimate": active_est,
        },
        "explanation": (
            f"{'L3 ACHIEVED! Both conditions met.' if level == 'L3' else ''}"
            f"{'L2: Meets L2 threshold but not L3.' if level == 'L2' else ''}"
            f"{'L1: Has engagement but does not meet L2 thresholds.' if level == 'L1' else ''}"
            f" For {tier} tier, L3 requires {l3_cert_req} certs AND {l3_pts_req} L3 pts."
            f" Current: {total_certs_ttm} certs ({cert_progress}%) and {l3_pts} L3 pts ({pts_progress}%)."
            f"{f' Gap: {cert_gap} certs + {pts_gap} pts needed.' if level != 'L3' else ''}"
        ).strip()
    }
    
    return json.dumps(output, indent=2, ensure_ascii=False)


@mcp.tool()
def get_l3_gap_analysis(
    country: str,
    partner_name: str,
    include_recommendations: bool = True,
    include_timeline: bool = True
) -> str:
    """Analyze the gap to L3 achievement for a specific partner.
    
    Provides current position, gap analysis, bottleneck identification,
    prioritized action recommendations, and estimated timeline.
    
    Args:
        country: Country name
        partner_name: Partner name to analyze
        include_recommendations: Include action guide (default: true)
        include_timeline: Include estimated timeline (default: true)
    """
    partner = find_partner(country, partner_name)
    
    if not partner:
        available = [p.partner_name for p in load_partners_by_country(country)]
        return json.dumps({
            "error": f"Partner '{partner_name}' not found in {country}",
            "available_partners": available[:20]
        }, indent=2, ensure_ascii=False)
    
    # Analyze
    result = analyze_partner(partner)
    gap = analyze_gap(result)
    
    output = {
        "partner": gap.partner_name,
        "country": gap.country,
        "tier": gap.tier,
        "current_level": gap.current_level,
        "gap": {
            "cert_gap": gap.cert_gap,
            "pts_gap": gap.pts_gap,
            "cert_progress_pct": gap.cert_progress_pct,
            "pts_progress_pct": gap.pts_progress_pct,
            "bottleneck": gap.bottleneck,
        },
        "active_cert_context": gap.active_cert_context,
    }
    
    if include_recommendations:
        output["recommendations"] = gap.recommendations
    if include_timeline:
        output["timeline"] = {
            "estimated_achievement": gap.timeline,
            "priority_classification": gap.priority,
        }
    
    return json.dumps(output, indent=2, ensure_ascii=False)


@mcp.tool()
def get_polaris_benchmark(
    countries: list[str] = None,
    metric: str = "all",
    tier_filter: str = ""
) -> str:
    """Compare Polaris metrics across countries.
    
    Supports country-level benchmarking with comparative insights.
    
    Args:
        countries: List of countries to compare (default: all available)
        metric: Focus metric - "certs", "int_plus_ratio", "l3_distribution", "all"
        tier_filter: Optional tier filter (e.g., "Premier")
    """
    result = generate_benchmark(
        countries=countries,
        tier_filter=tier_filter if tier_filter else None
    )
    
    # If specific metric requested, filter output
    if metric != "all" and result.get("countries"):
        for country_data in result["countries"]:
            if metric == "certs":
                keys_to_keep = ["country", "total_certs_ttm", "total_partners"]
            elif metric == "int_plus_ratio":
                keys_to_keep = ["country", "int_plus_ratio", "total_partners"]
            elif metric == "l3_distribution":
                keys_to_keep = ["country", "l3_count", "l2_count", "l1_count", "l3_rate_pct", "total_partners"]
            else:
                keys_to_keep = list(country_data.keys())
            
            for key in list(country_data.keys()):
                if key not in keys_to_keep:
                    del country_data[key]
    
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def get_polaris_criteria(
    tier: str = "",
    level: str = "",
    include_active_cert_policy: bool = True
) -> str:
    """Return the official Polaris level criteria from the framework document.
    
    Provides level definitions, tier-specific thresholds, engagement point
    calculation formulas, and Active Cert supplemental policy.
    
    Args:
        tier: Specific tier to query (default: all tiers)
        level: Specific level "L1", "L2", "L3" (default: all)
        include_active_cert_policy: Include 3Y validity rationale
    """
    output = {
        "framework_version": CRITERIA.get("version", "2025-10"),
        "measurement_periods": ["TTM (Trailing 12 Months)", "13-24 months ago"],
        "dual_condition_rule": "Both Certification count AND Engagement Points must be met simultaneously for level assignment.",
        "level_definitions": {
            "L0": "No training engagement recorded",
            "L1 (Awareness Trained)": "PartnerCast, Accreditation, or Free Digital content consumed but not meeting L2/L3 criteria",
            "L2 (Moderately Trained)": "Engagement with paid offerings (ILT, Certifications, SB Subscription) meeting tier-specific L2 thresholds",
            "L3 (Deeply Trained)": "Deep engagement with intermediate+ offerings (Int+ ILT, Int+ Certifications, Hands-on SB) meeting tier-specific L3 thresholds"
        },
        "point_formulas": {
            "l2_points": "1 ILT seat = 1pt, 1 certification = 1pt, 5 SB Subscription engagements = 1pt",
            "l3_points": "1 Int+ ILT seat = 1pt, 1 Int+ certification = 1pt, 5 Hands-on SB completions = 1pt",
            "int_plus_definition": "Associate + Professional + Specialty level (NOT Foundational)"
        },
    }
    
    # Tier thresholds
    tiers_data = CRITERIA.get("tiers", {})
    if tier and tier in tiers_data:
        output["thresholds"] = {tier: tiers_data[tier]}
    else:
        output["thresholds"] = tiers_data
    
    # Active cert policy
    if include_active_cert_policy:
        output["active_cert_policy"] = {
            "status": "Supplemental metric only - NOT used in official Polaris Level calculation",
            "validity_period": "3 years from certification date",
            "rationale": [
                "Polaris is a Flow metric (TTM training engagement velocity)",
                "Active Cert is a Stock metric (current org capability holdings)",
                "3Y cumulative would invalidate model calibration (thresholds based on TTM)",
                "Document explicitly limits lookback to TTM or 13-24 months (max 24M, not 36M)",
            ],
            "supplemental_value": [
                "Reflects project-deployable headcount",
                "Better PAR (Partner Attributed Revenue) correlation predictor",
                "Identifies recertification expiry risk",
                "Actionable for sales/business conversations"
            ],
            "estimation_formula": "Active_Cert_3Y ≈ TTM_certs × 2.4 (assumes ~20% YoY growth)"
        }
    
    return json.dumps(output, indent=2, ensure_ascii=False)


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
