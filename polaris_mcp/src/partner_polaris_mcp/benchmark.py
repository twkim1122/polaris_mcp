"""Cross-country/region Polaris benchmarking.

Compares Polaris metrics across countries for leadership insights.
"""

from .models import BenchmarkEntry, PolarisResult
from .polaris_engine import analyze_partner
from .data_loader import load_partners_by_country


def generate_benchmark(countries: list[str] = None, tier_filter: str = None) -> dict:
    """Generate benchmark comparison across countries.
    
    Args:
        countries: List of country names to compare. None = all available.
        tier_filter: Optional tier to filter by (e.g., "Premier")
    
    Returns:
        Dict with countries data and comparative insights.
    """
    from .data_loader import get_available_countries, load_all_partners
    
    available = get_available_countries()
    if countries:
        target_countries = [c for c in countries if c in available]
    else:
        target_countries = available
    
    entries = []
    for country in target_countries:
        partners = load_partners_by_country(country)
        if tier_filter:
            partners = [p for p in partners if p.tier == tier_filter]
        
        if not partners:
            continue
        
        results = [analyze_partner(p) for p in partners]
        
        total_certs = sum(p.total_certs_ttm for p in partners)
        total_int = sum(p.int_plus_certs for p in partners)
        int_ratio = round(total_int / total_certs * 100, 1) if total_certs > 0 else 0.0
        
        entry = BenchmarkEntry(
            country=country,
            total_partners=len(results),
            total_certs_ttm=total_certs,
            training_engagements=sum(p.ilt_sessions_total + p.sb_subscription_engagements + p.sb_hands_on_completions for p in partners),
            int_plus_ratio=int_ratio,
            l3_count=sum(1 for r in results if r.polaris_level == "L3"),
            l2_count=sum(1 for r in results if r.polaris_level == "L2"),
            l1_count=sum(1 for r in results if r.polaris_level == "L1"),
            l0_count=sum(1 for r in results if r.polaris_level == "L0"),
            active_cert_total=sum(r.active_cert_3y for r in results),
        )
        entries.append(entry)
    
    # Generate insights
    insights = _generate_insights(entries)
    
    return {
        "benchmark_type": "country",
        "tier_filter": tier_filter or "All",
        "countries": [_entry_to_dict(e) for e in entries],
        "insights": insights
    }


def _entry_to_dict(entry: BenchmarkEntry) -> dict:
    return {
        "country": entry.country,
        "total_partners": entry.total_partners,
        "total_certs_ttm": entry.total_certs_ttm,
        "training_engagements": entry.training_engagements,
        "int_plus_ratio": entry.int_plus_ratio,
        "l3_count": entry.l3_count,
        "l2_count": entry.l2_count,
        "l1_count": entry.l1_count,
        "l0_count": entry.l0_count,
        "active_cert_total": entry.active_cert_total,
        "l3_rate_pct": round(entry.l3_count / entry.total_partners * 100, 1) if entry.total_partners > 0 else 0,
    }


def _generate_insights(entries: list[BenchmarkEntry]) -> list[str]:
    """Generate comparative insights from benchmark data."""
    if not entries:
        return ["No data available for comparison."]
    
    insights = []
    
    # Sort by total certs
    by_certs = sorted(entries, key=lambda e: e.total_certs_ttm, reverse=True)
    if len(by_certs) >= 2:
        top = by_certs[0]
        insights.append(
            f"{top.country} leads in certification volume ({top.total_certs_ttm:,} TTM certs), "
            f"{by_certs[0].total_certs_ttm / by_certs[-1].total_certs_ttm:.0f}x more than {by_certs[-1].country}."
        )
    
    # Highest Int+ ratio
    by_int = sorted(entries, key=lambda e: e.int_plus_ratio, reverse=True)
    if by_int:
        top_int = by_int[0]
        insights.append(
            f"{top_int.country} has the highest Int+ ratio ({top_int.int_plus_ratio}%), "
            f"indicating deep training focus (global avg: 46.8%)."
        )
    
    # L3 comparison
    by_l3 = sorted(entries, key=lambda e: e.l3_count, reverse=True)
    if by_l3 and by_l3[0].l3_count > 0:
        insights.append(
            f"{by_l3[0].country} has the most L3 partners ({by_l3[0].l3_count}). "
            f"Global L3 rate benchmark: 8%."
        )
    
    return insights
