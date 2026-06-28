"""Submission completeness rules — required documents, FEIN, MC/DOT."""
from typing import List
from rules.base import RuleEvaluation


def check_submission_completeness(
    application: dict, document_types: list,
    loss_runs: list, ifta_reports: list,
) -> List[RuleEvaluation]:
    results = []

    # SUB-001: FEIN/SSN
    fein = application.get("fein_ssn")
    results.append(RuleEvaluation(
        "SUB-001", "Application: FEIN/SSN Present", "submission",
        "PASS" if fein else "WARNING", "high",
        "FEIN/SSN found." if fein else "FEIN/SSN not found. Required for complete submission.",
        {"fein_present": bool(fein)},
    ))

    # SUB-002: MC/DOT number
    mc, dot = application.get("mc_number"), application.get("dot_number")
    if mc or dot:
        results.append(RuleEvaluation(
            "SUB-002", "Application: MC/DOT Number Present", "submission",
            "PASS", "high", f"MC#{mc or 'N/A'} / DOT#{dot or 'N/A'} found.",
            {"mc_number": mc, "dot_number": dot},
        ))
    else:
        results.append(RuleEvaluation(
            "SUB-002", "Application: MC/DOT Number Present", "submission",
            "WARNING", "high", "MC and DOT numbers not found.", {},
        ))

    # SUB-003/004: Loss runs
    has_loss = "loss_run" in document_types
    results.append(RuleEvaluation(
        "SUB-003", "Loss Runs: Current (Within 60 Days)", "submission",
        "INFO" if has_loss else "FAIL", "high",
        "Loss runs provided. Verify valuation within 60 days." if has_loss
        else "No loss runs provided. Required: current + 3 prior years.",
        {"loss_run_present": has_loss},
    ))
    if not has_loss:
        results.append(RuleEvaluation(
            "SUB-004", "Loss Runs: 3 Prior Years", "submission",
            "FAIL", "high", "No loss runs. Requires 3+ prior years.", {},
        ))

    # SUB-005: 4 quarters IFTA
    ifta_count = len(ifta_reports)
    quarters = [ifta.get("quarter", "?") for ifta in ifta_reports]
    results.append(RuleEvaluation(
        "SUB-005", "IFTA: Most Recent 4 Quarters", "submission",
        "PASS" if ifta_count >= 4 else "FAIL", "high",
        f"{ifta_count} IFTA reports provided." if ifta_count >= 4
        else f"Only {ifta_count}/4 IFTA reports. Found: {', '.join(quarters)}.",
        {"ifta_quarters_provided": ifta_count, "quarters": quarters},
    ))

    # SUB-006/007: Driver list, equipment list
    if "driver_list" not in document_types:
        results.append(RuleEvaluation(
            "SUB-006", "Driver List Provided", "submission",
            "FAIL", "high", "No driver list found.", {},
        ))
    if "equipment_list" not in document_types:
        results.append(RuleEvaluation(
            "SUB-007", "Equipment Schedule Provided", "submission",
            "FAIL", "high", "No equipment schedule found.", {},
        ))

    # SUB-008: Driver license documents for CDL verification
    if "drivers_license" not in document_types:
        results.append(RuleEvaluation(
            "SUB-008", "Driver License Documents Provided", "submission",
            "FAIL", "high",
            "No driver license (CDL) documents found. Required for driver eligibility verification.",
            {"cdl_docs_present": False},
        ))
    else:
        results.append(RuleEvaluation(
            "SUB-008", "Driver License Documents Provided", "submission",
            "PASS", "low", "Driver license documents provided for CDL verification.",
            {"cdl_docs_present": True},
        ))

    return results
