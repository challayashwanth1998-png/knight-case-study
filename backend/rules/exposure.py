"""Exposure rules — hazmat, border, towing, intermodal, waste."""
from typing import List
from rules.base import RuleEvaluation, PROHIBITED_COMMODITIES, MEXICO_BORDER_STATES


def check_prohibited_exposures(application: dict, ifta_reports: list) -> List[RuleEvaluation]:
    results = []
    commodities = application.get("commodities_hauled", []) or []
    commodities_lower = [c.lower() for c in commodities]

    # EXP-001: Hazmat
    hazmat = application.get("hazmat", False)
    has_hazmat = hazmat or any(
        any(p in c for p in PROHIBITED_COMMODITIES) for c in commodities_lower
    )
    results.append(RuleEvaluation(
        "EXP-001", "Hazardous Materials: Prohibited", "exposure",
        "FAIL" if has_hazmat else "PASS", "critical",
        "Hazardous materials operations are PROHIBITED." if has_hazmat
        else "No hazardous materials indicated.",
        {"hazmat": hazmat},
    ))

    # EXP-002: Lithium batteries
    if any("lithium" in c for c in commodities_lower):
        results.append(RuleEvaluation(
            "EXP-002", "Lithium Battery Cargo: Prohibited", "exposure",
            "FAIL", "critical", "Lithium battery cargo is PROHIBITED.", {},
        ))

    # EXP-003: Mexico border
    operating_states: set = set()
    for ifta in ifta_reports:
        operating_states.update(ifta.get("states_traveled", []))
    border = operating_states & MEXICO_BORDER_STATES
    if border:
        results.append(RuleEvaluation(
            "EXP-003", "Mexico Border: 50-Mile Restriction", "exposure",
            "WARNING", "high",
            f"Operations in border states ({', '.join(sorted(border))}). "
            f"Verify no operations within 50 miles of border.",
            {"border_states": sorted(list(border))},
        ))

    # EXP-006: Towing/recovery
    op_type = (application.get("operation_type", "") or "").lower()
    if "tow" in op_type or "recovery" in op_type:
        results.append(RuleEvaluation(
            "EXP-006", "Towing/Recovery: Prohibited", "exposure",
            "FAIL", "critical", "Towing/recovery operations are PROHIBITED.", {},
        ))

    # EXP-007: Intermodal
    if any("intermodal" in c or "container" in c for c in commodities_lower):
        results.append(RuleEvaluation(
            "EXP-007", "Intermodal/Container: Prohibited", "exposure",
            "FAIL", "critical", "Intermodal/container operations are PROHIBITED.", {},
        ))

    # EXP-008: Waste
    if any("waste" in c or "refuse" in c or "garbage" in c for c in commodities_lower):
        results.append(RuleEvaluation(
            "EXP-008", "Waste Disposal: Prohibited", "exposure",
            "FAIL", "critical", "Waste disposal operations are PROHIBITED.", {},
        ))

    return results
