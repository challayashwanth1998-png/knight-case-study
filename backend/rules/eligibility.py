"""Eligibility rules — vehicle types, states, coverage checks."""
from typing import List
from rules.base import (
    RuleEvaluation, ALLOWED_STATES, INELIGIBLE_VEHICLE_TYPES, is_semi_truck,
)


def check_eligibility(application: dict, vehicles: list, ifta_reports: list) -> List[RuleEvaluation]:
    results = []

    # ELIG-001: Semi-trucks only — check power units only, not trailers
    if vehicles:
        from rules.base import is_power_unit
        power_units = [v for v in vehicles if is_power_unit(v)]
        semi_count = sum(1 for v in power_units if is_semi_truck(v))
        total_pu = len(power_units)
        non_semi = total_pu - semi_count
        non_semi_types = [v.get("vehicle_type", "unknown") for v in power_units if not is_semi_truck(v)]

        if non_semi == 0:
            results.append(RuleEvaluation(
                "ELIG-001", "Target Risk: Semi-Trucks Only", "eligibility",
                "PASS", "critical",
                f"All {total_pu} power units are semi-trucks ({len(vehicles)} total incl. trailers).",
                {"semi_count": semi_count, "total_power_units": total_pu, "total_vehicles": len(vehicles)},
            ))
        else:
            results.append(RuleEvaluation(
                "ELIG-001", "Target Risk: Semi-Trucks Only", "eligibility",
                "FAIL", "critical",
                f"{non_semi} of {total_pu} power units are NOT semi-trucks. "
                f"Ineligible types: {', '.join(set(non_semi_types))}.",
                {"semi_count": semi_count, "non_semi_count": non_semi, "total_power_units": total_pu},
            ))

    # ELIG-002: Prohibited vehicle types
    if vehicles:
        prohibited = []
        for v in vehicles:
            vtype = (v.get("vehicle_type", "") or "").lower()
            for inelig in INELIGIBLE_VEHICLE_TYPES:
                if inelig in vtype:
                    prohibited.append(v.get("vehicle_type", "unknown"))
                    break
        if prohibited:
            results.append(RuleEvaluation(
                "ELIG-002", "Ineligible Vehicle Types", "eligibility",
                "FAIL", "critical",
                f"Found {len(prohibited)} ineligible vehicle types: {', '.join(set(prohibited))}.",
                {"prohibited_types": list(set(prohibited))},
            ))
        else:
            results.append(RuleEvaluation(
                "ELIG-002", "Ineligible Vehicle Types", "eligibility",
                "PASS", "critical", "No prohibited vehicle types found.", {},
            ))

    # ELIG-003: Available states
    operating_states: set = set()
    for ifta in ifta_reports:
        operating_states.update(ifta.get("states_traveled", []))

    if operating_states:
        disallowed = operating_states - ALLOWED_STATES
        if disallowed:
            results.append(RuleEvaluation(
                "ELIG-003", "Available States Check", "eligibility",
                "WARNING", "high",
                f"Operating in states not in Knight's program: {', '.join(sorted(disallowed))}.",
                {"disallowed": sorted(list(disallowed))},
            ))
        else:
            results.append(RuleEvaluation(
                "ELIG-003", "Available States Check", "eligibility",
                "PASS", "high",
                f"All {len(operating_states)} operating states are covered.",
                {"states": sorted(list(operating_states))},
            ))

    # ELIG-004: TX north of I-10
    if "TX" in operating_states:
        results.append(RuleEvaluation(
            "ELIG-004", "Texas: North of I-10 Requirement", "eligibility",
            "WARNING", "medium",
            "Must verify Texas operations are north of I-10.",
            {"state": "TX"},
        ))

    # ELIG-005: IL selective
    app_state = (application.get("mailing_address", {}) or {}).get("state", "")
    if app_state == "IL" or "IL" in operating_states:
        results.append(RuleEvaluation(
            "ELIG-005", "Illinois: Selective Basis", "eligibility",
            "WARNING", "medium",
            "Illinois accounts accepted on selective basis only.",
            {"is_il_based": app_state == "IL"},
        ))

    # ELIG-006: No liability deductibles
    coverage = application.get("coverage_requested", {}) or {}
    results.append(RuleEvaluation(
        "ELIG-006", "Auto Liability Deductibles Not Allowed", "eligibility",
        "INFO", "info", "Auto liability deductibles are not allowed.", {},
    ))

    # ELIG-007: Physical damage not available
    pd_val = str(coverage.get("physical_damage") or "").lower().strip()
    pd_requested = pd_val and pd_val not in ("", "no", "none", "n/a", "not requested",
                                               "not requested - not applicable", "not applicable",
                                               "false", "0")
    if pd_requested:
        results.append(RuleEvaluation(
            "ELIG-007", "Auto Physical Damage Not Available", "eligibility",
            "WARNING", "medium",
            "Physical damage coverage requested but not available under this program.",
            {"physical_damage_requested": True},
        ))

    return results
