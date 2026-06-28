"""
Rules Engine — Orchestrator.
Delegates to category-specific modules and collects results.
"""
import logging
from typing import List, Dict, Any

from rules.base import RuleEvaluation
from rules.eligibility import check_eligibility
from rules.driver import check_drivers
from rules.exposure import check_prohibited_exposures
from rules.selective import check_selective_exposures, check_new_venture
from rules.submission import check_submission_completeness
from rules.ifta import check_ifta_validation

logger = logging.getLogger(__name__)


class RulesEngine:
    """Evaluates all Knight Specialty Insurance underwriting rules."""

    def evaluate_all(self, extracted_data: Dict[str, Any]) -> List[RuleEvaluation]:
        application = extracted_data.get("application", {})
        drivers = extracted_data.get("drivers", [])
        vehicles = extracted_data.get("vehicles", [])
        ifta_reports = extracted_data.get("ifta_reports", [])
        loss_runs = extracted_data.get("loss_runs", [])
        document_types = extracted_data.get("document_types", [])

        results: List[RuleEvaluation] = []

        results.extend(check_eligibility(application, vehicles, ifta_reports))
        results.extend(check_new_venture(application))
        results.extend(check_drivers(drivers))
        results.extend(check_prohibited_exposures(application, ifta_reports))
        results.extend(check_selective_exposures(application, vehicles))
        results.extend(check_submission_completeness(
            application, document_types, loss_runs, ifta_reports
        ))
        results.extend(check_ifta_validation(ifta_reports, application))

        logger.info(
            f"Rules evaluation complete: "
            f"{sum(1 for r in results if r.result == 'PASS')} pass, "
            f"{sum(1 for r in results if r.result == 'FAIL')} fail, "
            f"{sum(1 for r in results if r.result == 'WARNING')} warnings"
        )
        return results

    @staticmethod
    def get_rule_definitions() -> list:
        """Return static definitions of all business rules for the UI rules viewer."""
        return [
            # Eligibility
            {"rule_id": "ELIG-001", "rule_name": "Target Risk: Semi-Trucks Only", "category": "eligibility", "severity": "critical", "description": "Only semi-trucks hauling general freight are eligible. Straight trucks, tow trucks, dump trucks, concrete mixers/pumpers, cranes, and mobile equipment are not eligible regardless of GVW."},
            {"rule_id": "ELIG-002", "rule_name": "Ineligible Vehicle Types", "category": "eligibility", "severity": "critical", "description": "Explicitly prohibited vehicle types include straight trucks, tow trucks, dump trucks, concrete mixers, pumpers, cranes, and mobile equipment."},
            {"rule_id": "ELIG-003", "rule_name": "Available States Check", "category": "eligibility", "severity": "critical", "description": "Operations must be in approved states: AL, AZ, AR, CA, SC, SD, TN, TX, UT, VA, WV, WI, WY. Operations in non-listed states are not eligible."},
            {"rule_id": "ELIG-004", "rule_name": "Texas: North of I-10 Requirement", "category": "eligibility", "severity": "medium", "description": "Texas-based accounts must operate north of Interstate 10 (I-10)."},
            {"rule_id": "ELIG-005", "rule_name": "Illinois: Selective Basis", "category": "eligibility", "severity": "medium", "description": "Illinois-based accounts are accepted on a selective basis only and require additional underwriter review."},
            {"rule_id": "ELIG-006", "rule_name": "Auto Liability Deductibles Not Allowed", "category": "eligibility", "severity": "high", "description": "Auto liability deductibles are not permitted under this program."},
            {"rule_id": "ELIG-007", "rule_name": "Auto Physical Damage Not Available", "category": "eligibility", "severity": "medium", "description": "Auto physical damage coverage is not available under this program."},
            # Driver
            {"rule_id": "DRV-001", "rule_name": "Valid CDL Required", "category": "driver", "severity": "critical", "description": "All drivers must hold a valid U.S. driver license with CDL endorsement."},
            {"rule_id": "DRV-002", "rule_name": "Minimum 2 Years CDL Experience", "category": "driver", "severity": "high", "description": "Drivers must have at least 2 years of CDL driving experience in the U.S. or Canada."},
            {"rule_id": "DRV-003", "rule_name": "Minimum Age 23", "category": "driver", "severity": "critical", "description": "All drivers must be at least 23 years of age."},
            {"rule_id": "DRV-004", "rule_name": "DOT Medical Exam (Age 65+)", "category": "driver", "severity": "high", "description": "Drivers age 65 and older must provide an acceptable DOT medical examination report."},
            {"rule_id": "DRV-005", "rule_name": "Max 6 Points in 3 Years", "category": "driver", "severity": "high", "description": "Drivers should have no more than 6 points on their MVR in the last 3 years."},
            {"rule_id": "DRV-006", "rule_name": "Max 4 Points in 12 Months", "category": "driver", "severity": "high", "description": "Drivers should have no more than 4 points on their MVR in the last 12 months."},
            {"rule_id": "DRV-100", "rule_name": "Unacceptable Driver History", "category": "driver", "severity": "critical", "description": "Automatic decline for: DUI/DWI (past 5 years), vehicular homicide/assault, negligent or reckless driving, speeding 30+ mph over limit, hit-and-run, fleeing/eluding, felony involving a motor vehicle, passing a stopped school bus."},
            # Exposure
            {"rule_id": "EXP-001", "rule_name": "No Hazardous Materials", "category": "exposure", "severity": "critical", "description": "Hauling hazardous materials is a prohibited exposure."},
            {"rule_id": "EXP-002", "rule_name": "No Lithium Battery Cargo", "category": "exposure", "severity": "critical", "description": "Hauling lithium battery cargo is a prohibited exposure."},
            {"rule_id": "EXP-003", "rule_name": "Mexico Border Restriction", "category": "exposure", "severity": "critical", "description": "Operations within 50 miles of the USA/Mexico border are prohibited."},
            {"rule_id": "EXP-004", "rule_name": "SAFER Violations", "category": "exposure", "severity": "critical", "description": "Serious SAFER violations are a prohibited exposure that triggers automatic decline."},
            {"rule_id": "EXP-005", "rule_name": "No Towing/Recovery", "category": "exposure", "severity": "critical", "description": "Towing and recovery operations are prohibited."},
            {"rule_id": "EXP-006", "rule_name": "No Intermodal/Container", "category": "exposure", "severity": "critical", "description": "Intermodal and container hauling operations are prohibited."},
            {"rule_id": "EXP-007", "rule_name": "No Waste Disposal", "category": "exposure", "severity": "critical", "description": "Waste disposal operations are prohibited."},
            # Submission
            {"rule_id": "SUB-001", "rule_name": "FEIN/SSN Required", "category": "submission", "severity": "high", "description": "Application must include a Federal Employer Identification Number (FEIN) or Social Security Number (SSN)."},
            {"rule_id": "SUB-002", "rule_name": "MC/DOT Number Required", "category": "submission", "severity": "high", "description": "Application must include an MC or DOT number for commercial auto operations."},
            {"rule_id": "SUB-003", "rule_name": "Current Loss Runs Required", "category": "submission", "severity": "high", "description": "Current loss runs valued within 60 days must be provided."},
            {"rule_id": "SUB-004", "rule_name": "3 Prior Years Loss Runs", "category": "submission", "severity": "high", "description": "At least 3 prior years of loss history must be provided."},
            {"rule_id": "SUB-005", "rule_name": "4 IFTA Quarters Required", "category": "submission", "severity": "high", "description": "The most recent 4 quarters of IFTA reports must be submitted."},
            {"rule_id": "SUB-008", "rule_name": "Driver License Documents Required", "category": "submission", "severity": "high", "description": "Driver license (CDL) images must be provided for driver eligibility verification."},
            # IFTA
            {"rule_id": "IFTA-001", "rule_name": "Fleet MPG Validation", "category": "ifta", "severity": "medium", "description": "Fleet MPG should be within a reasonable range (4.0-9.0 MPG for semi-trucks)."},
            {"rule_id": "IFTA-002", "rule_name": "Company Name Consistency", "category": "ifta", "severity": "medium", "description": "Company name on IFTA reports should be consistent across all quarters."},
            {"rule_id": "IFTA-003", "rule_name": "IFTA Name Matches Application", "category": "ifta", "severity": "medium", "description": "Company name on IFTA reports should match the name on the insurance application."},
            {"rule_id": "IFTA-004", "rule_name": "Non-Covered States", "category": "ifta", "severity": "medium", "description": "IFTA reports showing significant mileage in non-covered states should be flagged."},
            # Selective
            {"rule_id": "SEL-001", "rule_name": "Box Truck Minimum Premium", "category": "selective", "severity": "high", "description": "Box trucks and transit vans require a minimum premium of $250,000."},
            {"rule_id": "SEL-002", "rule_name": "Power Unit Minimum Count", "category": "selective", "severity": "high", "description": "Accounts seeking less than $13,000 per power unit must have at least 20 power units."},
            # New Venture
            {"rule_id": "VENT-001", "rule_name": "New Venture: CDL Experience Required", "category": "eligibility", "severity": "high", "description": "Sole proprietors, partnerships, and LLCs must have 2 years documented CDL experience with resume or letter of experience."},
            {"rule_id": "VENT-002", "rule_name": "Corporation: Underwriter Review Required", "category": "eligibility", "severity": "medium", "description": "Corporations are subject to additional underwriter review for new venture eligibility."},
        ]

