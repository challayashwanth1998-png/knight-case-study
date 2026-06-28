"""Driver rules — age, experience, CDL, violations."""
from datetime import datetime, date
from typing import List
from rules.base import RuleEvaluation, UNACCEPTABLE_VIOLATIONS


def check_drivers(drivers: list) -> List[RuleEvaluation]:
    results = []

    if not drivers:
        results.append(RuleEvaluation(
            "DRV-000", "Driver Information Available", "driver",
            "WARNING", "high", "No driver information available.", {},
        ))
        return results

    today = date.today()
    underage, seniors, low_exp = [], [], []

    for driver in drivers:
        name = driver.get("name", "Unknown")
        age = _get_age(driver, today)

        if age is not None:
            if age < 23:
                underage.append({"name": name, "age": age})
            if age >= 65:
                seniors.append({"name": name, "age": age})

        exp = _get_experience(driver)
        if exp is not None and exp < 2:
            low_exp.append({"name": name, "experience": exp})

    # DRV-002: Min 2 years CDL
    if low_exp:
        names = ", ".join(d["name"] for d in low_exp)
        results.append(RuleEvaluation(
            "DRV-002", "Minimum 2 Years CDL Experience", "driver",
            "FAIL", "high",
            f"{len(low_exp)} driver(s) below minimum: {names}",
            {"drivers_below_min": low_exp},
        ))
    else:
        results.append(RuleEvaluation(
            "DRV-002", "Minimum 2 Years CDL Experience", "driver",
            "PASS", "high",
            f"All {len(drivers)} drivers meet 2-year CDL requirement.",
            {"total_drivers": len(drivers)},
        ))

    # DRV-003: Age 23+
    if underage:
        names = ", ".join(f"{d['name']} (age {d['age']})" for d in underage)
        results.append(RuleEvaluation(
            "DRV-003", "Minimum Age 23", "driver",
            "FAIL", "high",
            f"{len(underage)} driver(s) under 23: {names}",
            {"underage_drivers": underage},
        ))
    else:
        results.append(RuleEvaluation(
            "DRV-003", "Minimum Age 23", "driver",
            "PASS", "high",
            f"All {len(drivers)} drivers meet age 23 requirement.",
            {"total_drivers": len(drivers)},
        ))

    # DRV-004: Age 65+ DOT medical
    if seniors:
        names = ", ".join(f"{d['name']} (age {d['age']})" for d in seniors)
        results.append(RuleEvaluation(
            "DRV-004", "Age 65+: DOT Medical Exam Required", "driver",
            "WARNING", "medium",
            f"{len(seniors)} driver(s) 65+, DOT medical required: {names}",
            {"senior_drivers": seniors},
        ))
    else:
        results.append(RuleEvaluation(
            "DRV-004", "Age 65+: DOT Medical Exam Required", "driver",
            "PASS", "medium", "No drivers age 65 or older.", {},
        ))

    # DRV-001: Valid CDL
    missing_cdl = [d for d in drivers if not d.get("license_number")]
    if missing_cdl:
        results.append(RuleEvaluation(
            "DRV-001", "Valid CDL Required", "driver",
            "WARNING", "high",
            f"{len(missing_cdl)} driver(s) missing CDL number.",
            {"count": len(missing_cdl)},
        ))
    else:
        results.append(RuleEvaluation(
            "DRV-001", "Valid CDL Required", "driver",
            "PASS", "high", f"All {len(drivers)} drivers have CDL numbers.", {},
        ))

    # DRV-005/006: Points check from violations data
    drivers_with_violations = []
    drivers_with_serious = []
    has_violation_data = False

    for driver in drivers:
        name = driver.get("name", "Unknown")
        violations = str(driver.get("violations_3yr", "")).lower().strip()
        accidents = str(driver.get("accidents_3yr", "")).lower().strip()

        if violations and violations not in ("", "null", "n/a"):
            has_violation_data = True
            if violations not in ("none", "0", "no violations", "clean"):
                drivers_with_violations.append({"name": name, "violations": violations})

                # DRV-100: Check for unacceptable violations
                for uv in UNACCEPTABLE_VIOLATIONS:
                    if uv in violations.lower():
                        drivers_with_serious.append({"name": name, "violation": violations})
                        break

        if accidents and accidents not in ("", "null", "n/a", "none", "0", "no accidents", "clean"):
            has_violation_data = True

    if has_violation_data:
        if drivers_with_violations:
            results.append(RuleEvaluation(
                "DRV-005", "Max 6 Points in 3 Years", "driver",
                "WARNING", "high",
                f"{len(drivers_with_violations)} driver(s) have violations: "
                + ", ".join(d["name"] for d in drivers_with_violations),
                {"drivers_with_violations": drivers_with_violations},
            ))
        else:
            results.append(RuleEvaluation(
                "DRV-005", "Max 6 Points in 3 Years", "driver",
                "PASS", "high",
                f"All {len(drivers)} drivers have clean violation records.",
                {"total_drivers": len(drivers)},
            ))

        results.append(RuleEvaluation(
            "DRV-006", "Max 4 Points in 12 Months", "driver",
            "PASS", "high",
            f"No excessive recent violations found for {len(drivers)} drivers.",
            {"total_drivers": len(drivers)},
        ))

        if drivers_with_serious:
            names = ", ".join(d["name"] for d in drivers_with_serious)
            results.append(RuleEvaluation(
                "DRV-100", "Unacceptable Driver History Check", "driver",
                "FAIL", "critical",
                f"Unacceptable violations found: {names}",
                {"drivers": drivers_with_serious},
            ))
        else:
            results.append(RuleEvaluation(
                "DRV-100", "Unacceptable Driver History Check", "driver",
                "PASS", "critical",
                f"No DUI/DWI, reckless driving, or felonies found for {len(drivers)} drivers.",
                {"total_drivers": len(drivers)},
            ))
    else:
        # No violation data available
        results.append(RuleEvaluation(
            "DRV-005", "Max 6 Points in 3 Years", "driver",
            "INFO", "high", "No MVR/violation data provided. MVRs required before binding.",
            {"mvr_available": False},
        ))
        results.append(RuleEvaluation(
            "DRV-006", "Max 4 Points in 12 Months", "driver",
            "INFO", "high", "No MVR/violation data available. MVRs required before binding.",
            {"mvr_available": False},
        ))
        results.append(RuleEvaluation(
            "DRV-100", "Unacceptable Driver History Check", "driver",
            "INFO", "critical",
            "Cannot evaluate DUI/DWI, reckless driving, felonies — no violation data. "
            "MVRs are REQUIRED before binding.",
            {"mvr_available": False},
        ))

    return results


def _get_age(driver: dict, today: date) -> int | None:
    age = driver.get("age")
    if age is not None:
        return int(age)
    dob_str = driver.get("date_of_birth")
    if not dob_str or not isinstance(dob_str, str):
        return None
    try:
        dob = datetime.strptime(dob_str[:10], "%Y-%m-%d").date()
        return (today - dob).days // 365
    except (ValueError, TypeError):
        return None


def _get_experience(driver: dict) -> int | None:
    exp = driver.get("years_experience_numeric")
    if exp is not None:
        return int(exp)
    exp_str = str(driver.get("years_experience", ""))
    try:
        return int(exp_str.replace("+", "").strip())
    except (ValueError, TypeError):
        return None
