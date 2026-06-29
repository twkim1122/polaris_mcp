"""Data loading and caching layer.

Loads partner data from CSV files in the data/ directory.
Supports multiple country CSVs for multi-country analysis.
"""

import csv
import os
from pathlib import Path
from typing import Optional
from .models import PartnerData

DATA_DIR = Path(os.environ.get("POLARIS_DATA_DIR", Path(__file__).parent.parent.parent / "data"))

# In-memory cache
_cache: dict[str, list[PartnerData]] = {}


def _parse_int(val: str) -> int:
    """Safely parse integer from CSV value."""
    try:
        return int(val.strip()) if val.strip() else 0
    except (ValueError, AttributeError):
        return 0


def load_csv(filepath: Path) -> list[PartnerData]:
    """Load partner data from a CSV file."""
    partners = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            partner = PartnerData(
                partner_name=row.get("partner_name", "").strip(),
                tier=row.get("tier", "").strip(),
                country=row.get("country", "").strip(),
                total_certs_ttm=_parse_int(row.get("total_certs_ttm", "0")),
                foundational_certs=_parse_int(row.get("foundational_certs", "0")),
                associate_certs=_parse_int(row.get("associate_certs", "0")),
                professional_certs=_parse_int(row.get("professional_certs", "0")),
                specialty_certs=_parse_int(row.get("specialty_certs", "0")),
                ilt_sessions_total=_parse_int(row.get("ilt_sessions_total", "0")),
                ilt_sessions_int_plus=_parse_int(row.get("ilt_sessions_int_plus", "0")),
                sb_subscription_engagements=_parse_int(row.get("sb_subscription_engagements", "0")),
                sb_hands_on_completions=_parse_int(row.get("sb_hands_on_completions", "0")),
                active_certs_3y=_parse_int(row.get("active_certs_3y", "0")),
            )
            if partner.partner_name:
                partners.append(partner)
    return partners


def load_all_partners() -> list[PartnerData]:
    """Load all partner data from all CSV files in data/ directory."""
    global _cache
    if "all" in _cache:
        return _cache["all"]
    
    all_partners = []
    for csv_file in DATA_DIR.glob("*.csv"):
        partners = load_csv(csv_file)
        all_partners.extend(partners)
    
    _cache["all"] = all_partners
    return all_partners


def load_partners_by_country(country: str) -> list[PartnerData]:
    """Load partners filtered by country name (case-insensitive)."""
    all_partners = load_all_partners()
    return [p for p in all_partners if p.country.lower() == country.lower()]


def get_available_countries() -> list[str]:
    """Get list of all available countries in the dataset."""
    all_partners = load_all_partners()
    countries = sorted(set(p.country for p in all_partners))
    return countries


def find_partner(country: str, partner_name: str) -> Optional[PartnerData]:
    """Find a specific partner by country and name (case-insensitive partial match)."""
    partners = load_partners_by_country(country)
    name_lower = partner_name.lower()
    
    # Exact match first
    for p in partners:
        if p.partner_name.lower() == name_lower:
            return p
    
    # Partial match
    for p in partners:
        if name_lower in p.partner_name.lower():
            return p
    
    return None


def clear_cache():
    """Clear the in-memory cache. Call after data file updates."""
    global _cache
    _cache.clear()


def get_data_info() -> dict:
    """Get information about loaded data."""
    all_partners = load_all_partners()
    countries = get_available_countries()
    return {
        "total_partners": len(all_partners),
        "countries": countries,
        "data_directory": str(DATA_DIR),
        "csv_files": [f.name for f in DATA_DIR.glob("*.csv")]
    }
