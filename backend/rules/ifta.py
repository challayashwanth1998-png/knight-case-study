"""IFTA validation rules — MPG, company name consistency, state coverage."""
from typing import List
from rules.base import RuleEvaluation, ALLOWED_STATES


def check_ifta_validation(ifta_reports: list, application: dict) -> List[RuleEvaluation]:
    results = []
    if not ifta_reports:
        return results

    # IFTA-001: Fleet MPG
    for ifta in ifta_reports:
        mpg = ifta.get("fleet_mpg")
        quarter = ifta.get("quarter", "?")
        if mpg is not None:
            ok = 4.0 <= mpg <= 9.0
            results.append(RuleEvaluation(
                "IFTA-001", f"Fleet MPG Reasonableness ({quarter})", "ifta",
                "PASS" if ok else "WARNING", "medium",
                f"Fleet MPG {mpg} {'within' if ok else 'OUTSIDE'} range (4.0-9.0).",
                {"mpg": mpg, "quarter": quarter},
            ))

    # IFTA-002: Name consistency
    names = {ifta.get("company_name", "").strip() for ifta in ifta_reports if ifta.get("company_name")}
    if len(names) > 1:
        results.append(RuleEvaluation(
            "IFTA-002", "IFTA Company Name Consistency", "ifta",
            "FAIL", "high",
            f"Different names across IFTA reports: {', '.join(names)}.",
            {"names_found": list(names)},
        ))

    # IFTA-003: Name matches application
    app_name = (application.get("business_name", "") or "").strip()
    if app_name and names:
        app_lower = app_name.lower()
        match = any(app_lower in n.lower() or n.lower() in app_lower for n in names)
        results.append(RuleEvaluation(
            "IFTA-003", "IFTA vs Application Company Name", "ifta",
            "PASS" if match else "FAIL", "high",
            "Company name consistent." if match
            else f"Application name '{app_name}' doesn't match IFTA: {', '.join(names)}.",
            {"application_name": app_name, "ifta_names": list(names)},
        ))

    # IFTA-004: Non-covered states
    all_states: set = set()
    for ifta in ifta_reports:
        all_states.update(ifta.get("states_traveled", []))
    non_covered = all_states - ALLOWED_STATES
    if non_covered:
        results.append(RuleEvaluation(
            "IFTA-004", "IFTA: Operations in Non-Covered States", "ifta",
            "WARNING", "high",
            f"Operations in {len(non_covered)} non-covered states: {', '.join(sorted(non_covered))}.",
            {"non_covered_states": sorted(list(non_covered))},
        ))

    return results
