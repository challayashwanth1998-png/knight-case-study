"""
Generate additional test scenarios (6-10) for the Knight Insurance AI pipeline.
These scenarios test rule failures across different categories.

Test Scenarios:
  6. hazmat-exposure   — Hazardous materials + prohibited commodities (EXP-001/002/007/008)
  7. ineligible-vehicles — Box trucks, dump trucks, tow trucks (ELIG-001/002, SEL-002)
  8. new-venture       — New company, sole proprietor with <2yr experience (VENT-001/002)
  9. too-many-units    — 30 power units (>26 max), Mexico border ops (EXP-003)
  10. high-loss-ratio   — Heavy claims history, bad loss ratio
"""
import os
import sys
import shutil

# Add parent dir so we can import the existing generators
sys.path.insert(0, os.path.dirname(__file__))
from generate_test_scenarios import (
    ensure_dir, make_pdf, make_excel, gen_application, gen_driver_roster,
    gen_vehicle_schedule, gen_loss_runs, gen_ifta, GOOD_DRIVERS, GOOD_VEHICLES,
    BASE_DIR, STYLES
)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from openpyxl import Workbook


# ═══════════════════════════════════════════════════════════
# Custom application generator with more parameters
# ═══════════════════════════════════════════════════════════
def gen_application_custom(out_dir, company, **kwargs):
    """Generate an insurance application with custom fields."""
    filepath = os.path.join(out_dir, f"{company.replace(' ', '_')}_Application.pdf")
    state = kwargs.get("state", "TN")
    fein = kwargs.get("fein", "62-7834521")
    mc = kwargs.get("mc", "MC-789456")
    dot = kwargs.get("dot", "DOT-2345678")
    units = kwargs.get("units", 5)
    hazmat = kwargs.get("hazmat", False)
    towing = kwargs.get("towing", False)
    mexico = kwargs.get("mexico", False)
    premium = kwargs.get("premium", "$75,000")
    commodities = kwargs.get("commodities", "General freight, dry goods, consumer products")
    biz_type = kwargs.get("biz_type", "LLC")
    years_biz = kwargs.get("years_biz", 8)
    years_trucking = kwargs.get("years_trucking", 12)
    operation_type = kwargs.get("operation_type", "For-hire, Interstate")
    pd = kwargs.get("physical_damage", "Not Requested")
    states_of_op = kwargs.get("states_of_op", f"{state}, AL, AR, VA, SC")

    paras = [
        f"<b>Commercial Auto Insurance Application</b>",
        f"<b>Business Name:</b> {company}",
        f"<b>Business Type:</b> {biz_type}",
        f"<b>FEIN:</b> {fein}",
        f"<b>MC Number:</b> {mc}",
        f"<b>DOT Number:</b> {dot}",
        f"<b>Mailing Address:</b> 123 Freight Lane, Nashville, {state} 37201",
        f"<b>Owner:</b> Thomas Anderson",
        f"<b>Years in Business:</b> {years_biz}",
        f"<b>Years Trucking Experience:</b> {years_trucking}",
        f"<b>Commodities Hauled:</b> {commodities}",
        f"<b>Operation Type:</b> {operation_type}",
        f"<b>Hazardous Materials:</b> {'Yes' if hazmat else 'No'}",
        f"<b>Towing/Recovery:</b> {'Yes' if towing else 'No'}",
        f"<b>Mexico Border (within 50mi):</b> {'Yes' if mexico else 'No'}",
        f"<b>Number of Power Units:</b> {units}",
        f"<b>Number of Drivers:</b> {units}",
        f"<b>Regular Drivers:</b> {units}",
        f"<b>Part-Time Drivers:</b> 0",
        f"<b>Owner Operators:</b> 0",
        f"<b>Estimated Annual Premium:</b> {premium}",
        f"<b>Coverage Requested:</b>",
        f"  Auto Liability: $1,000,000 CSL",
        f"  Physical Damage: {pd}",
        f"  Cargo: $100,000",
        f"<b>Base State:</b> {state}",
        f"<b>States of Operation:</b> {states_of_op}",
        f"<b>Annual Revenue:</b> $2,400,000",
        f"<b>Annual Mileage:</b> 625,000",
        f"<b>Intermodal/Container:</b> No",
        "",
        f"<b>PRIOR INSURANCE</b>",
        f"<b>Current Carrier:</b> National Indemnity Insurance",
        f"<b>Policy Number:</b> NAT-2024-TRK-77234",
        f"<b>Effective Date:</b> January 1, 2024",
        f"<b>Expiration Date:</b> January 1, 2026",
        f"<b>Current Premium:</b> $165,000",
        f"<b>Cancelled or Non-Renewed:</b> No",
        "",
        f"<b>SAFETY & COMPLIANCE</b>",
        f"<b>Employment Background Check:</b> Yes",
        f"<b>Pre-Employment Drug Test:</b> Yes - DOT 5-panel",
        f"<b>Criminal Background Check:</b> Yes",
        f"<b>MVR Review (Pre-Employment):</b> Yes",
        f"<b>Annual MVR Review:</b> Yes",
        f"<b>Road Test:</b> Yes - all new hires",
        f"<b>Telematics / GPS:</b> Yes",
        f"<b>Dash Cameras:</b> Yes",
        f"<b>ELD Compliance:</b> Yes - fully compliant",
    ]
    make_pdf(filepath, "Commercial Auto Insurance Application", paras)
    return filepath


def gen_ifta_custom(out_dir, company, quarter, year, states_data=None, filename=None):
    """Generate IFTA with custom state/mileage data."""
    fname = filename or f"{company.replace(' ', '_')}_IFTA_{quarter}_{year}.pdf"
    filepath = os.path.join(out_dir, fname)

    if states_data is None:
        states_data = [
            ("TN", 28500, 4250), ("AL", 15200, 2280),
            ("AR", 12800, 1920), ("VA", 9500, 1425), ("SC", 8400, 1260),
        ]
    total_miles = sum(s[1] for s in states_data)
    total_gal = sum(s[2] for s in states_data)
    mpg = round(total_miles / total_gal, 2) if total_gal else 0

    paras = [
        f"<b>IFTA Quarterly Fuel Tax Report</b>",
        f"<b>Company:</b> {company}",
        f"<b>IFTA License:</b> TN-2345-6789",
        f"<b>FEIN:</b> 62-7834521",
        f"<b>DOT:</b> DOT-2345678",
        f"<b>Base State:</b> TN",
        f"<b>Quarter:</b> {quarter} {year}",
    ]

    jur_header = ["State", "Miles", "Gallons", "Tax Paid"]
    jur_rows = [[s, str(m), str(g), f"${round(g * 0.244, 2)}"]
                for s, m, g in states_data]
    jur_rows.append(["TOTAL", str(total_miles), str(total_gal),
                     f"${round(total_gal * 0.244, 2)}"])

    summary = [["Fleet MPG", str(mpg)], ["Total Miles", str(total_miles)],
               ["Total Gallons", str(total_gal)]]

    make_pdf(filepath, f"IFTA Report — {quarter} {year}", paras,
             tables=[("Jurisdictions", [jur_header] + jur_rows),
                     ("Summary", [["Metric", "Value"]] + summary)])
    return filepath


def gen_loss_runs_custom(out_dir, company, claims=None, years=3, loss_ratio="85.3%"):
    """Generate loss runs with custom claims data."""
    filepath = os.path.join(out_dir, f"{company.replace(' ', '_')}_Loss_Runs.pdf")
    today = datetime.now()

    paras = [
        f"<b>Loss Run Report</b>",
        f"<b>Carrier:</b> National Indemnity Insurance",
        f"<b>Insured:</b> {company}",
        f"<b>FEIN:</b> 62-7834521",
        f"<b>DOT:</b> DOT-2345678",
        f"<b>Valuation Date:</b> {today.strftime('%m/%d/%Y')}",
    ]

    year_data = []
    year_header = ["Policy Year", "Earned Premium", "Claims", "Total Incurred", "Loss Ratio"]
    for y in range(years):
        yr_start = today.year - y - 1
        year_data.append([f"{yr_start}-{yr_start+1}", "$68,000", "5", "$57,900", loss_ratio])

    if claims is None:
        claims = [
            ["CLM-2024-001", "03/15/2024", "Minor fender bender", "Closed", "$4,200"],
        ]
    claim_header = ["Claim #", "Date of Loss", "Description", "Status", "Incurred"]

    make_pdf(filepath, "Loss Run Report", paras,
             tables=[("Policy Years", [year_header] + year_data),
                     ("Claims Detail", [claim_header] + claims)])
    return filepath


# ═══════════════════════════════════════════════════════════
# Scenario 6: Hazardous Materials & Prohibited Exposures
# Triggers: EXP-001 (hazmat), EXP-007 (intermodal), EXP-008 (waste)
# ═══════════════════════════════════════════════════════════
def gen_scenario_6():
    out = ensure_dir(os.path.join(BASE_DIR, "test-6-hazmat-exposure"))
    company = "Toxic Freight Solutions LLC"

    gen_application_custom(out, company,
        fein="83-1234567", mc="MC-998877", dot="DOT-7654321",
        hazmat=True,
        commodities="Hazardous materials, chemical waste, industrial solvents, lithium batteries",
        operation_type="For-hire, Interstate, Hazmat carrier",
        states_of_op="TX, AZ, CA, NM, TN",
    )
    gen_driver_roster(out, company, GOOD_DRIVERS)
    gen_vehicle_schedule(out, company, GOOD_VEHICLES)
    gen_loss_runs(out, company)
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)

    # Copy DLs
    src_dl = os.path.join(BASE_DIR, "test-1-perfect", "driver-licenses")
    dst_dl = os.path.join(out, "driver-licenses")
    if os.path.exists(src_dl):
        if os.path.exists(dst_dl):
            shutil.rmtree(dst_dl)
        shutil.copytree(src_dl, dst_dl)

    print(f"✅ Scenario 6: Hazmat & Prohibited Exposure → {out}")
    print(f"   Expected: DECLINE (EXP-001 hazmat FAIL, EXP-002 lithium FAIL)")


# ═══════════════════════════════════════════════════════════
# Scenario 7: Ineligible Vehicles (not semi-trucks)
# Triggers: ELIG-001 (not semi), ELIG-002 (prohibited types), SEL-002 (box trucks)
# ═══════════════════════════════════════════════════════════
def gen_scenario_7():
    out = ensure_dir(os.path.join(BASE_DIR, "test-7-ineligible-vehicles"))
    company = "Metro City Delivery LLC"

    ineligible_vehicles = [
        {"unit": "V-201", "year": 2022, "make": "Ford", "model": "F-650", "vin": "1FDNF6CC0NDA12345",
         "type": "Box Truck", "gvw": "26,000 lbs", "value": "$45,000"},
        {"unit": "V-202", "year": 2021, "make": "Isuzu", "model": "NPR-HD", "vin": "JALE5W162M7123456",
         "type": "Box Truck", "gvw": "14,500 lbs", "value": "$35,000"},
        {"unit": "V-203", "year": 2023, "make": "Hino", "model": "268A", "vin": "5PVNJ8JV5P4S12345",
         "type": "Straight Truck", "gvw": "25,500 lbs", "value": "$55,000"},
        {"unit": "V-204", "year": 2020, "make": "Peterbilt", "model": "348", "vin": "2NP3LJ9X1LT234567",
         "type": "Dump Truck", "gvw": "33,000 lbs", "value": "$75,000"},
        {"unit": "V-205", "year": 2022, "make": "Ford", "model": "Transit 350", "vin": "1FTBW3XM2NKA56789",
         "type": "Cargo Van", "gvw": "10,360 lbs", "value": "$42,000"},
    ]

    gen_application_custom(out, company,
        fein="71-9876543", mc="MC-445566", dot="DOT-5556667",
        units=5, premium="$120,000",
        commodities="Local deliveries, parcels, building materials, sand/gravel",
    )
    gen_driver_roster(out, company, GOOD_DRIVERS)
    gen_vehicle_schedule(out, company, ineligible_vehicles)
    gen_loss_runs(out, company)
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)

    src_dl = os.path.join(BASE_DIR, "test-1-perfect", "driver-licenses")
    dst_dl = os.path.join(out, "driver-licenses")
    if os.path.exists(src_dl):
        if os.path.exists(dst_dl):
            shutil.rmtree(dst_dl)
        shutil.copytree(src_dl, dst_dl)

    print(f"✅ Scenario 7: Ineligible Vehicles → {out}")
    print(f"   Expected: DECLINE (ELIG-001 not semi FAIL, ELIG-002 prohibited FAIL)")


# ═══════════════════════════════════════════════════════════
# Scenario 8: New Venture / Inexperienced Owner
# Triggers: VENT-001 (new venture CDL exp), low experience drivers
# ═══════════════════════════════════════════════════════════
def gen_scenario_8():
    out = ensure_dir(os.path.join(BASE_DIR, "test-8-new-venture"))
    company = "Fresh Start Trucking"

    new_drivers = [
        {"name": "Tyler J Ross", "dob": "06/15/2001", "cdl": "TN-11223344", "state": "TN",
         "exp": 1, "age": 25, "hire": "2025-11-01", "violations": 0, "accidents": 0},
        {"name": "Brandon K Lee", "dob": "03/22/2000", "cdl": "TN-22334455", "state": "TN",
         "exp": 1, "age": 26, "hire": "2025-10-15", "violations": "1 speeding", "accidents": 0},
        {"name": "Jason M White", "dob": "11/08/2002", "cdl": "AL-33445566", "state": "AL",
         "exp": 1, "age": 24, "hire": "2026-01-01", "violations": 0, "accidents": 0},
    ]

    gen_application_custom(out, company,
        fein="92-1112233", mc="MC-112233", dot="DOT-1112233",
        units=3, premium="$35,000",
        biz_type="Sole Proprietor",
        years_biz=0,
        years_trucking=1,
        commodities="General freight",
    )
    gen_driver_roster(out, company, new_drivers)

    new_vehicles = [
        {"unit": "T-301", "year": 2024, "make": "Freightliner", "model": "Cascadia", "vin": "3AKJHHDR5NSLA9999"},
        {"unit": "T-302", "year": 2023, "make": "Kenworth", "model": "T680", "vin": "1XKYD49X1MJ888888"},
        {"unit": "T-303", "year": 2024, "make": "Peterbilt", "model": "579", "vin": "2NP2HJ7X4PT777777"},
    ]
    gen_vehicle_schedule(out, company, new_vehicles)
    gen_loss_runs(out, company, claims=[
        ["N/A", "N/A", "No prior claims history — new venture", "N/A", "$0"],
    ])
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)

    # NO driver license images — new venture may not have them yet
    print(f"✅ Scenario 8: New Venture → {out}")
    print(f"   Expected: DECLINE/REFER (VENT-001 FAIL, DRV-002 FAIL, SUB-008 FAIL, SEL-003 WARNING)")


# ═══════════════════════════════════════════════════════════
# Scenario 9: Mexico Border + Too Many Units
# Triggers: EXP-003 (border), ELIG-003 (non-covered states)
# ═══════════════════════════════════════════════════════════
def gen_scenario_9():
    out = ensure_dir(os.path.join(BASE_DIR, "test-9-border-operations"))
    company = "Southwest Border Logistics"

    # IFTA with Mexico border states and non-covered states
    border_states = [
        ("TX", 35000, 5250), ("AZ", 22000, 3300), ("NM", 18000, 2700),
        ("CA", 15000, 2250), ("NV", 8000, 1200), ("CO", 6000, 900),
    ]

    gen_application_custom(out, company,
        fein="85-4433221", mc="MC-667788", dot="DOT-6677889",
        state="TX",
        units=8, premium="$200,000",
        mexico=True,
        commodities="Cross-border freight, auto parts, electronics, produce",
        states_of_op="TX, AZ, NM, CA, NV, CO",
    )
    gen_driver_roster(out, company, GOOD_DRIVERS + [
        {"name": "Carlos M Rivera", "dob": "05/12/1988", "cdl": "TX-66778899", "state": "TX", "exp": 6, "age": 38},
        {"name": "Diego L Santos", "dob": "08/22/1982", "cdl": "AZ-77889900", "state": "AZ", "exp": 10, "age": 44},
        {"name": "Maria T Gonzalez", "dob": "12/01/1990", "cdl": "TX-88990011", "state": "TX", "exp": 4, "age": 36},
    ])

    more_vehicles = GOOD_VEHICLES + [
        {"unit": "T-106", "year": 2021, "make": "Kenworth", "model": "T880", "vin": "1XKYD49X1MJ111111"},
        {"unit": "T-107", "year": 2022, "make": "Freightliner", "model": "Cascadia", "vin": "3AKJHHDR5NSLA2222"},
        {"unit": "T-108", "year": 2023, "make": "Peterbilt", "model": "389", "vin": "2NP2HJ7X4PT333333"},
    ]
    gen_vehicle_schedule(out, company, more_vehicles)

    gen_loss_runs(out, company)
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta_custom(out, company, q, y, states_data=border_states)

    src_dl = os.path.join(BASE_DIR, "test-1-perfect", "driver-licenses")
    dst_dl = os.path.join(out, "driver-licenses")
    if os.path.exists(src_dl):
        if os.path.exists(dst_dl):
            shutil.rmtree(dst_dl)
        shutil.copytree(src_dl, dst_dl)

    print(f"✅ Scenario 9: Border Operations → {out}")
    print(f"   Expected: REFER (EXP-003 border WARNING, ELIG-003 non-covered states WARNING)")


# ═══════════════════════════════════════════════════════════
# Scenario 10: Towing/Recovery Operations
# Triggers: EXP-006 (towing prohibited)
# ═══════════════════════════════════════════════════════════
def gen_scenario_10():
    out = ensure_dir(os.path.join(BASE_DIR, "test-10-towing-operations"))
    company = "Roadside Recovery Services"

    tow_vehicles = [
        {"unit": "TW-01", "year": 2022, "make": "Peterbilt", "model": "389", "vin": "2NP2HJ7X4PT111111",
         "type": "Tow Truck", "gvw": "52,000 lbs", "value": "$120,000"},
        {"unit": "TW-02", "year": 2021, "make": "Kenworth", "model": "T880", "vin": "1XKYD49X1MJ222222",
         "type": "Tow Truck", "gvw": "52,000 lbs", "value": "$115,000"},
        {"unit": "TW-03", "year": 2023, "make": "Freightliner", "model": "M2 112", "vin": "3AKJHHDR5NSLA3333",
         "type": "Semi-Truck", "gvw": "80,000 lbs", "value": "$95,000"},
        {"unit": "TW-04", "year": 2020, "make": "International", "model": "HV", "vin": "3HSDJAPR4NN444444",
         "type": "Semi-Truck", "gvw": "80,000 lbs", "value": "$85,000"},
        {"unit": "TW-05", "year": 2022, "make": "Volvo", "model": "VHD", "vin": "4V4NC9EH5LN555555",
         "type": "Semi-Truck", "gvw": "80,000 lbs", "value": "$90,000"},
    ]

    gen_application_custom(out, company,
        fein="73-5566778", mc="MC-334455", dot="DOT-3344556",
        units=5, premium="$95,000",
        towing=True,
        operation_type="Towing and recovery, roadside assistance",
        commodities="Vehicle recovery, disabled vehicles, accident scene clearance",
    )
    gen_driver_roster(out, company, GOOD_DRIVERS)
    gen_vehicle_schedule(out, company, tow_vehicles)
    gen_loss_runs(out, company)
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)

    src_dl = os.path.join(BASE_DIR, "test-1-perfect", "driver-licenses")
    dst_dl = os.path.join(out, "driver-licenses")
    if os.path.exists(src_dl):
        if os.path.exists(dst_dl):
            shutil.rmtree(dst_dl)
        shutil.copytree(src_dl, dst_dl)

    print(f"✅ Scenario 10: Towing Operations → {out}")
    print(f"   Expected: DECLINE (EXP-006 towing FAIL, ELIG-001 tow trucks FAIL, ELIG-002 prohibited FAIL)")


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating additional test scenarios (6-10)...")
    print("=" * 60)
    gen_scenario_6()
    gen_scenario_7()
    gen_scenario_8()
    gen_scenario_9()
    gen_scenario_10()
    print("=" * 60)
    print("✅ All additional scenarios generated!")
