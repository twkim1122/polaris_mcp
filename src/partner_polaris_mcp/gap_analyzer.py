"""L3 Gap Analysis and Action Guide Generator.

Provides detailed gap analysis for each partner, including:
- Bottleneck identification (certs vs points vs both)
- Prioritized action recommendations
- Estimated timeline to L3 achievement
- Active Cert context (stock vs flow gap)
"""

from .models import PolarisResult, GapAnalysisResult


def generate_recommendations(result: PolarisResult) -> list:
    """Generate prioritized action recommendations based on gap analysis."""
    recommendations = []
    
    if result.polaris_level == "L3":
        recommendations.append({
            "priority": 1,
            "action": "Maintain current L3 level through annual certification plan",
            "impact": "Sustains PAR correlation benefit and partner status",
            "effort": "Low (ongoing monitoring)"
        })
        return recommendations
    
    # Determine bottleneck
    cert_gap = result.cert_gap
    pts_gap = result.pts_gap
    
    # Quick-win: only certs needed
    if pts_gap <= 0 and cert_gap > 0:
        if cert_gap <= 5:
            recommendations.append({
                "priority": 1,
                "action": f"Take {cert_gap} more Associate or Professional certification exam(s)",
                "impact": "Immediately achieves L3 (L3 Pts already met)",
                "effort": "Low (1-4 weeks)"
            })
            recommendations.append({
                "priority": 2,
                "action": "Run a Cert Readiness session for target candidates",
                "impact": "Prepares team members for immediate exam success",
                "effort": "Low (1 day session)"
            })
        elif cert_gap <= 20:
            recommendations.append({
                "priority": 1,
                "action": f"Distribute {cert_gap} certification vouchers (Int+ level focus)",
                "impact": "Achieves L3 within 6 months",
                "effort": "Medium (6 months)"
            })
            recommendations.append({
                "priority": 2,
                "action": "Host 1-2 Cert Day events (target 10+ participants each)",
                "impact": "Batch certification drives efficiency",
                "effort": "Medium (1 day per event)"
            })
    
    # Both gaps exist
    elif cert_gap > 0 and pts_gap > 0:
        if result.tier == "Premier":
            recommendations.append({
                "priority": 1,
                "action": f"Deploy SCA lever: SBTS seats + {min(200, cert_gap // 2)} vouchers/year",
                "impact": f"Addresses cert gap ({cert_gap}) and builds Hands-on SB points",
                "effort": "High (requires SCA contract)"
            })
            recommendations.append({
                "priority": 2,
                "action": f"Schedule {max(5, pts_gap // 20)} Int+ Private ILT sessions per year",
                "impact": f"Builds L3 pts ({pts_gap} gap) through intermediate+ ILT credit",
                "effort": "Medium (quarterly scheduling)"
            })
            recommendations.append({
                "priority": 3,
                "action": "Run quarterly Cert Day / Elevate Days (20-30 participants)",
                "impact": "Scale program drives cert volume and engagement",
                "effort": "Medium (quarterly cadence)"
            })
        else:
            recommendations.append({
                "priority": 1,
                "action": f"Focus on Int+ certifications ({cert_gap} needed) - Associate and Professional level",
                "impact": "Simultaneously addresses both cert count and L3 pts",
                "effort": "Medium"
            })
            recommendations.append({
                "priority": 2,
                "action": f"Complete {pts_gap * 5} SB Hands-on Labs/Games/JAMs",
                "impact": f"Gains {pts_gap} L3 pts from hands-on activities",
                "effort": "Medium (self-paced)"
            })
            recommendations.append({
                "priority": 3,
                "action": "Attend 2-3 intermediate+ ILT sessions",
                "impact": "Each session = 1 L3 pt plus skill development",
                "effort": "Low-Medium (2-3 days total)"
            })
    
    # Int+ ratio improvement needed
    if result.int_plus_ratio < 60 and result.polaris_level != "L3":
        recommendations.append({
            "priority": len(recommendations) + 1,
            "action": f"Improve Int+ ratio from {result.int_plus_ratio}% to 70%+: take only Associate/Professional/Specialty exams",
            "impact": "Higher Int+ ratio means each cert contributes to L3 pts",
            "effort": "Behavioral change (exam selection guidance)"
        })
    
    # Recertification risk
    if result.active_cert_3y > 100:
        renewals_needed = round(result.active_cert_3y / 3)
        recommendations.append({
            "priority": len(recommendations) + 1,
            "action": f"Manage recertification schedule (~{renewals_needed} renewals/year needed)",
            "impact": "Prevents Active Cert stock erosion and potential Polaris level drop",
            "effort": "Low (scheduling and voucher allocation)"
        })
    
    return recommendations


def estimate_timeline(result: PolarisResult) -> str:
    """Estimate time to L3 achievement."""
    if result.polaris_level == "L3":
        return "Already achieved"
    
    cert_gap = result.cert_gap
    pts_gap = result.pts_gap
    
    # Quick-win
    if pts_gap <= 0 and cert_gap <= 5:
        return "Immediate (1-2 months)"
    
    if cert_gap <= 10 and pts_gap <= 10:
        return "6 months"
    
    if cert_gap <= 20:
        return "6-12 months"
    
    if cert_gap <= 50:
        return "12-18 months"
    
    if cert_gap <= 200:
        return "1.5-2 years"
    
    return "Long-term (3-5 years)"


def identify_bottleneck(result: PolarisResult) -> str:
    """Identify which condition is the bottleneck for L3."""
    if result.polaris_level == "L3":
        return "none"
    
    cert_met = result.cert_gap <= 0
    pts_met = result.pts_gap <= 0
    
    if cert_met and pts_met:
        return "none"
    elif cert_met and not pts_met:
        return "points"
    elif not cert_met and pts_met:
        return "certifications"
    else:
        return "both"


def analyze_gap(result: PolarisResult) -> GapAnalysisResult:
    """Full gap analysis for a partner."""
    bottleneck = identify_bottleneck(result)
    recommendations = generate_recommendations(result)
    timeline = estimate_timeline(result)
    
    active_context = {
        "active_cert_3y": result.active_cert_3y,
        "l3_cert_threshold": result.l3_cert_threshold,
        "stock_sufficient": result.active_cert_l3_ready,
        "recertification_risk": "Low" if result.active_cert_3y < 100 else f"Monitor (~{result.active_cert_3y // 3}/yr renewal)"
    }
    
    return GapAnalysisResult(
        partner_name=result.partner_name,
        country=result.country,
        tier=result.tier,
        current_level=result.polaris_level,
        cert_gap=result.cert_gap,
        pts_gap=result.pts_gap,
        cert_progress_pct=result.cert_progress_pct,
        pts_progress_pct=result.pts_progress_pct,
        bottleneck=bottleneck,
        active_cert_context=active_context,
        recommendations=recommendations,
        timeline=timeline,
        priority=result.priority
    )
