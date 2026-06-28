"""
Base types, constants, and shared definitions for the rules engine.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any


@dataclass
class RuleEvaluation:
    """Result of evaluating a single underwriting rule."""
    rule_id: str
    rule_name: str
    category: str       # eligibility, driver, exposure, submission, selective, ifta
    result: str         # PASS, FAIL, WARNING, INFO, SKIP
    severity: str       # critical, high, medium, low, info
    details: str
    data_used: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Constants from Knight Specialty Insurance Guidelines ─────

ALLOWED_STATES = {
    "AL", "AZ", "AR", "CA", "SC", "SD", "TN",
    "TX", "UT", "VA", "WV", "WI", "WY",
}

ELIGIBLE_VEHICLE_TYPES = {
    "semi-truck", "semi truck", "tractor", "semi", "sleeper", "day cab",
}

INELIGIBLE_VEHICLE_TYPES = {
    "straight truck", "tow truck", "dump truck", "concrete mixer",
    "concrete pumper", "crane", "mobile equipment", "box truck",
    "cargo van", "shuttle bus", "utility truck", "medium duty truck",
    "flatbed truck", "transit van",
}

PROHIBITED_COMMODITIES = {
    "hazardous materials", "hazmat", "lithium battery",
    "lithium batteries", "waste", "refuse", "garbage", "disposal",
}

UNACCEPTABLE_VIOLATIONS = [
    "dui", "dwi", "driving under the influence", "driving while intoxicated",
    "vehicular homicide", "vehicular assault", "vehicular manslaughter",
    "negligent driving", "reckless driving",
    "hit-and-run", "hit and run",
    "fleeing", "eluding", "evading",
    "felony", "passing a stopped school bus", "passing school bus",
]

MEXICO_BORDER_STATES = {"TX", "AZ", "CA", "NM"}


# ─── Shared Helpers ───────────────────────────────────────────

def is_semi_truck(vehicle: dict) -> bool:
    """Check if a vehicle is a semi-truck."""
    vtype = (vehicle.get("vehicle_type", "") or "").lower()
    is_semi = vehicle.get("is_semi_truck", None)
    if is_semi is not None:
        return is_semi
    return any(t in vtype for t in ELIGIBLE_VEHICLE_TYPES)


def is_power_unit(vehicle: dict) -> bool:
    """Check if a vehicle is a power unit (not a trailer)."""
    vtype = (vehicle.get("vehicle_type", "") or "").lower()
    trailer_keywords = [
        "trailer", "dolly", "reefer", "dry van", "flatbed",
        "tanker", "chassis", "container", "lowboy", "drop deck",
        "curtainside", "refrigerated", "van trailer",
    ]
    return not any(t in vtype for t in trailer_keywords)
