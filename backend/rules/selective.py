"""Selective exposure rules — box trucks, power unit minimums, new venture."""
from typing import List
from rules.base import RuleEvaluation, is_power_unit


def check_selective_exposures(application: dict, vehicles: list) -> List[RuleEvaluation]:
    results = []
    if not vehicles:
        return results

    box_trucks = [v for v in vehicles if (v.get("vehicle_type", "").lower() in
                  ["box truck", "transit van", "cargo van"])]
    if box_trucks:
        results.append(RuleEvaluation(
            "SEL-002", "Box Trucks/Vans: Minimum Premium $250,000", "selective",
            "WARNING", "medium",
            f"Found {len(box_trucks)} box trucks/vans. Min premium $250K required.",
            {"count": len(box_trucks)},
        ))

    power_units = sum(1 for v in vehicles if is_power_unit(v))
    if 0 < power_units < 20:
        # Only warn if premium per unit is below $13K
        premium_str = application.get("annual_premium") or application.get("estimated_premium") or ""
        try:
            premium = float(str(premium_str).replace("$", "").replace(",", "").strip() or "0")
        except (ValueError, TypeError):
            premium = 0
        premium_per_unit = premium / power_units if power_units > 0 else 0
        if premium_per_unit < 13000:
            results.append(RuleEvaluation(
                "SEL-003", "Power Unit Minimum: 20 if <$13K/unit", "selective",
                "WARNING", "medium",
                f"Only {power_units} power units at ${premium_per_unit:,.0f}/unit. "
                f"Need 20+ if premium <$13K/unit.",
                {"power_unit_count": power_units, "premium_per_unit": premium_per_unit},
            ))

    return results


def check_new_venture(application: dict) -> List[RuleEvaluation]:
    results = []
    biz_type = (application.get("business_type", "") or "").lower()

    if biz_type in ["corporation", "corp"]:
        results.append(RuleEvaluation(
            "VENT-002", "Corporation: Underwriter Review Required", "eligibility",
            "WARNING", "medium", "Corporation ventures require underwriter review.",
            {"business_type": biz_type},
        ))
    elif biz_type in ["sole proprietor", "partnership", "llc", "individual"]:
        years_exp = application.get("years_experience_trucking")
        if years_exp is not None and years_exp < 2:
            results.append(RuleEvaluation(
                "VENT-001", "New Venture: CDL Experience Required", "eligibility",
                "FAIL", "high",
                f"Min 2 years CDL required. Found: {years_exp} years.",
                {"business_type": biz_type, "years_experience": years_exp},
            ))

    return results
