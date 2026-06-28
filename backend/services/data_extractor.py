"""
Knight Insurance — Structured Data Extractor
Uses Google Gemini to extract structured data from classified documents.
Each document type has a specific extraction schema.
"""
import json
import logging
from typing import Optional

from config import settings
from utils.gemini import call_gemini_json

logger = logging.getLogger(__name__)


EXTRACTION_PROMPTS = {
    "insurance_application": """You are extracting data from a commercial auto insurance application.
Read the document text below and return a JSON object with these fields.
Use null for any missing values. Use true/false for boolean fields.

Required JSON structure:
- business_name (string)
- business_type (string: Individual/Corporation/Partnership/LLC/Other)
- fein_ssn (string or null) - Federal Employer ID Number or SSN
- mc_number (string or null) - Motor Carrier number
- dot_number (string or null) - DOT number
- mailing_address: object with street, city, state (2-letter), zip
- owner_name (string)
- years_in_business (number or null)
- years_experience_trucking (number or null)
- commodities_hauled (array of strings)
- operation_type (string: for_hire / private / non_trucking)
- interstate (boolean)
- intrastate (boolean)
- hazmat (boolean)
- hazmat_details (string or null)
- driver_count: object with regular, part_time, owner_operator, total (all numbers)
- power_unit_count (number or null)
- coverage_requested: object with auto_liability_limit, physical_damage, cargo_limit, general_liability, medical_payments (strings or null)
- estimated_premium (string or null) - estimated annual premium amount
- prior_insurance: object with carrier_name, policy_number, expiration_date, current_premium, cancelled_or_nonrenewed (boolean), cancellation_reason
- safety_features: object with employment_background_check, pre_employment_drug_test, criminal_background_check, mvr_review, road_test, annual_mvr_review, telematics, safety_director (all booleans)
- states_operated (array of 2-letter state codes)
- base_state (string, 2-letter state code)
- annual_revenue (string or null)
- annual_mileage (string or null)
- towing_recovery (boolean)
- mexico_border (boolean)
- intermodal_container (boolean)

Document content:
---
{content}
---

Return ONLY the JSON object.""",

    "driver_list": """You are extracting driver roster data from a commercial trucking document.
Read the document text below and return a JSON object.
Use null for any missing values.

Required JSON structure:
- company_name (string)
- drivers (array of objects, each with):
  - number (integer, row number)
  - name (string, full name)
  - date_of_birth (string, YYYY-MM-DD format)
  - age (integer)
  - license_number (string, CDL number)
  - license_state (string, 2-letter state code)
  - license_class (string, e.g. "A", "B")
  - years_experience (number)
  - date_of_hire (string, YYYY-MM-DD or null)
  - violations_3yr (string, description or "None")
  - accidents_3yr (string, description or "None")
  - status (string, e.g. "Active")
- total_drivers (integer)

Document content:
---
{content}
---

Return ONLY the JSON object.""",

    "equipment_list": """You are extracting vehicle/equipment schedule data from a commercial trucking document.
Read the document text below and return a JSON object.
Use null for any missing values.

Required JSON structure:
- vehicles (array of objects, each with):
  - unit_number (string or integer)
  - year (integer)
  - make (string)
  - model (string)
  - vin (string)
  - vehicle_type (string, e.g. "Semi-Truck", "Trailer", "Dry Van")
  - gvw (string or null, gross vehicle weight)
  - stated_value (string or null)
- total_power_units (integer)
- total_trailers (integer)
- total_vehicles (integer)

Document content:
---
{content}
---

Return ONLY the JSON object.""",

    "ifta_report": """You are extracting IFTA (International Fuel Tax Agreement) report data.
Read the document text below and return a JSON object.
Use null for any missing values.

Required JSON structure:
- company_name (string)
- ifta_license (string or null)
- dot_number (string or null)
- mc_number (string or null)
- fein (string or null)
- base_state (string, 2-letter state code)
- quarter (string, e.g. "Q1 2026")
- period (string, e.g. "January - March 2026")
- jurisdictions (array of objects, each with):
  - state (string, 2-letter state code)
  - miles (number)
  - gallons (number)
  - tax_paid (number)
- total_miles (number)
- total_gallons (number)
- total_tax (number)
- fleet_mpg (number or null, calculated as total_miles / total_gallons)

Document content:
---
{content}
---

Return ONLY the JSON object.""",

    "loss_run": """You are extracting loss run / claims history data from an insurance document.
Read the document text below and return a JSON object.
Use null for any missing values.

Required JSON structure:
- carrier_name (string)
- insured_name (string)
- fein (string or null)
- dot_number (string or null)
- mc_number (string or null)
- policy_number (string or null)
- valuation_date (string, date of the report)
- policy_years (array of objects, each with):
  - year (string, e.g. "2024-2025")
  - earned_premium (string or null)
  - claim_count (integer)
  - total_incurred (number)
  - total_paid (number)
  - loss_ratio (string or null)
- claims (array of objects, each with):
  - claim_number (string)
  - date_of_loss (string)
  - driver (string or null)
  - description (string)
  - status (string: "Open" or "Closed")
  - incurred (number)
- total_claims_3yr (integer)
- total_incurred_3yr (number)
- overall_loss_ratio (string or null)

Document content:
---
{content}
---

Return ONLY the JSON object.""",

    "mvr": """You are extracting Motor Vehicle Record (MVR) data.
Read the document text below and return a JSON object.
Use null for any missing values.

Required JSON structure:
- driver_name (string)
- date_of_birth (string, YYYY-MM-DD)
- license_number (string)
- license_state (string, 2-letter)
- license_class (string)
- license_status (string: valid/suspended/revoked)
- violations (array of objects with date, description, points, conviction)
- accidents (array of objects with date, description, at_fault)
- total_points (integer)
- points_last_12_months (integer)
- points_last_3_years (integer)
- has_dui (boolean)
- has_reckless_driving (boolean)
- has_serious_violations (boolean)

Document content:
---
{content}
---

Return ONLY the JSON object.""",

    "drivers_license": """You are extracting data from a driver's license or CDL (Commercial Driver License) image/scan.
Read the document text below and return a JSON object with the driver's information.
Use null for any missing values.

Required JSON structure:
- driver_name (string, full name as shown on license)
- date_of_birth (string, YYYY-MM-DD format)
- age (integer, calculated from DOB to today)
- license_number (string, the DL/CDL number)
- license_state (string, 2-letter state code)
- license_class (string, e.g. "A", "B", "C")
- license_status (string: "Valid", "Expired", "Suspended", etc.)
- expiration_date (string, YYYY-MM-DD or MM/DD/YYYY format)
- endorsements (string, e.g. "T, N, H" or "None")
- restrictions (string, e.g. "None" or description)
- sex (string, M or F)
- height (string)
- weight (string)
- eye_color (string)
- is_commercial (boolean, whether this is a CDL)
- issue_date (string or null)

Document content:
---
{content}
---

Return ONLY the JSON object."""
}


class DataExtractor:
    """Extracts structured data from classified documents using Gemini AI."""

    def __init__(self):
        pass

    def extract(self, document_type: str, extracted_text: str,
                structured_data: dict = None, filename: str = "") -> Optional[dict]:
        """
        Extract structured data based on document type.

        Args:
            document_type: The classified document type
            extracted_text: Raw text from the document
            structured_data: Structured data (from Excel, etc.)
            filename: Original filename for context

        Returns:
            Extracted structured data as a dict, or None on failure
        """
        prompt_template = EXTRACTION_PROMPTS.get(document_type)

        if not prompt_template:
            logger.info(f"No extraction template for document type '{document_type}'. Skipping.")
            return {"raw_text": extracted_text[:5000], "note": "No extraction template for this document type"}

        # Prepare content
        content = extracted_text[:5000]
        if structured_data:
            struct_str = json.dumps(structured_data, indent=1, default=str)[:2000]
            content = f"STRUCTURED DATA:\n{struct_str}\n\nRAW TEXT:\n{content}"

        prompt = prompt_template.format(content=content)

        try:
            result = call_gemini_json(prompt, temperature=0.1)
            logger.info(f"Successfully extracted data from '{filename}' (type: {document_type})")
            return result

        except Exception as e:
            logger.error(f"Extraction failed for '{filename}': {e}")
            return {"error": str(e)}
