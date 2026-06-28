"""
Generate multiple test submission scenarios for the Knight Insurance AI pipeline.
Each scenario tests different edge cases and failure modes.

Test Scenarios:
  1. perfect       — All docs, all rules pass
  2. missing-dl    — No driver licenses submitted
  3. bad-driver    — Driver with DUI, excessive points
  4. wrong-names   — Misleading filenames (tests content-based classification)
  5. incomplete    — Missing IFTA reports and loss runs
"""
import os
import json
import shutil
from datetime import datetime, timedelta
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

BASE_DIR = os.path.join(os.path.dirname(__file__), "test-scenarios")
STYLES = getSampleStyleSheet()


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


# ═══════════════════════════════════════════════════════════
# Helper: Generate PDF
# ═══════════════════════════════════════════════════════════
def make_pdf(filepath, title, paragraphs, tables=None):
    """Create a simple PDF with title, paragraphs, and optional tables."""
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []
    title_style = ParagraphStyle('CustomTitle', parent=STYLES['Heading1'],
                                  fontSize=16, spaceAfter=12)
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))

    for p in paragraphs:
        story.append(Paragraph(p, STYLES['Normal']))
        story.append(Spacer(1, 6))

    if tables:
        for header, rows in tables:
            story.append(Spacer(1, 12))
            story.append(Paragraph(header, STYLES['Heading2']))
            story.append(Spacer(1, 6))
            t = Table(rows, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
            ]))
            story.append(t)

    doc.build(story)


def make_excel(filepath, sheet_name, headers, rows):
    """Create an Excel file with one sheet."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(filepath)


# ═══════════════════════════════════════════════════════════
# Common data generators
# ═══════════════════════════════════════════════════════════
def gen_application(out_dir, company, state="TN", fein="62-7834521",
                    mc="MC-789456", dot="DOT-2345678", units=5,
                    hazmat=False, towing=False, mexico=False,
                    premium="$75,000"):
    filepath = os.path.join(out_dir, f"{company.replace(' ', '_')}_Application.pdf")
    paras = [
        f"<b>Commercial Auto Insurance Application</b>",
        f"<b>Business Name:</b> {company}",
        f"<b>Business Type:</b> LLC",
        f"<b>FEIN:</b> {fein}",
        f"<b>MC Number:</b> {mc}",
        f"<b>DOT Number:</b> {dot}",
        f"<b>Mailing Address:</b> 123 Freight Lane, Nashville, {state} 37201",
        f"<b>Owner:</b> Thomas Anderson",
        f"<b>Years in Business:</b> 8",
        f"<b>Years Trucking Experience:</b> 12",
        f"<b>Commodities Hauled:</b> General freight, dry goods, consumer products",
        f"<b>Operation Type:</b> For-hire, Interstate",
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
        f"  Physical Damage: Not Requested",
        f"  Cargo: $100,000",
        f"<b>Base State:</b> {state}",
        f"<b>States of Operation:</b> {state}, AL, AR, VA, SC",
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
        f"<b>Cancelled or Non-Renewed:</b> No - continuous coverage since 2018",
        "",
        f"<b>SAFETY & COMPLIANCE</b>",
        f"<b>Employment Background Check:</b> Yes",
        f"<b>Pre-Employment Drug Test:</b> Yes - DOT 5-panel",
        f"<b>Criminal Background Check:</b> Yes",
        f"<b>MVR Review (Pre-Employment):</b> Yes",
        f"<b>Annual MVR Review:</b> Yes",
        f"<b>Road Test:</b> Yes - all new hires",
        f"<b>Telematics / GPS:</b> Yes - Samsara fleet tracking on all units",
        f"<b>Safety Director:</b> Yes - Thomas Anderson",
        f"<b>Drug Testing Program:</b> Yes - random quarterly DOT testing",
        f"<b>Safety Meetings:</b> Yes - monthly, documented",
        f"<b>Dash Cameras:</b> Yes - forward and driver-facing",
        f"<b>ELD Compliance:</b> Yes - fully compliant",
    ]
    make_pdf(filepath, "Commercial Auto Insurance Application", paras)
    return filepath


def gen_driver_roster(out_dir, company, drivers, filename=None):
    fname = filename or f"{company.replace(' ', '_')}_Driver_Roster.xlsx"
    filepath = os.path.join(out_dir, fname)
    headers = ["#", "Driver Name", "DOB", "Age", "CDL Number", "State",
               "Class", "Years Exp", "Hire Date", "Violations (3yr)", "Accidents (3yr)", "Status"]
    rows = []
    for i, d in enumerate(drivers, 1):
        rows.append([i, d["name"], d["dob"], d.get("age", 35),
                     d["cdl"], d["state"], d.get("cls", "A"),
                     d.get("exp", 5), d.get("hire", "2020-01-15"),
                     d.get("violations", 0), d.get("accidents", 0),
                     d.get("status", "Active")])
    make_excel(filepath, "Driver Roster", headers, rows)
    return filepath


def gen_vehicle_schedule(out_dir, company, vehicles, filename=None):
    fname = filename or f"{company.replace(' ', '_')}_Vehicle_Schedule.xlsx"
    filepath = os.path.join(out_dir, fname)
    headers = ["Unit #", "Year", "Make", "Model", "VIN", "Type", "GVW", "Value"]
    rows = []
    for v in vehicles:
        rows.append([v["unit"], v["year"], v["make"], v["model"],
                     v["vin"], v.get("type", "Semi-Truck"),
                     v.get("gvw", "80,000 lbs"), v.get("value", "$95,000")])
    make_excel(filepath, "Vehicle Schedule", headers, rows)
    return filepath


def gen_loss_runs(out_dir, company, filename=None, years=3, claims=None):
    fname = filename or f"{company.replace(' ', '_')}_Loss_Runs.pdf"
    filepath = os.path.join(out_dir, fname)
    today = datetime.now()
    val_date = today.strftime("%m/%d/%Y")

    paras = [
        f"<b>Loss Run Report</b>",
        f"<b>Carrier:</b> National Indemnity Insurance",
        f"<b>Insured:</b> {company}",
        f"<b>FEIN:</b> 62-7834521",
        f"<b>DOT:</b> DOT-2345678",
        f"<b>Valuation Date:</b> {val_date}",
    ]

    year_data = []
    year_header = ["Policy Year", "Earned Premium", "Claims", "Total Incurred", "Loss Ratio"]
    for y in range(years):
        yr_start = today.year - y - 1
        year_data.append([f"{yr_start}-{yr_start+1}", "$68,000", "1", "$12,400", "18.2%"])
    if not claims:
        claims = [
            ["CLM-2024-001", "03/15/2024", "Minor fender bender at truck stop", "Closed", "$4,200"],
            ["CLM-2023-001", "09/22/2023", "Rear-end collision, low speed", "Closed", "$8,200"],
        ]
    claim_header = ["Claim #", "Date of Loss", "Description", "Status", "Incurred"]

    make_pdf(filepath, "Loss Run Report", paras,
             tables=[("Policy Years", [year_header] + year_data),
                     ("Claims Detail", [claim_header] + claims)])
    return filepath


def gen_ifta(out_dir, company, quarter, year, filename=None):
    fname = filename or f"{company.replace(' ', '_')}_IFTA_{quarter}_{year}.pdf"
    filepath = os.path.join(out_dir, fname)

    states = [
        ("TN", 28500, 4250), ("AL", 15200, 2280),
        ("AR", 12800, 1920), ("VA", 9500, 1425), ("SC", 8400, 1260),
    ]
    total_miles = sum(s[1] for s in states)
    total_gal = sum(s[2] for s in states)
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
    jur_rows = [[s, str(m), str(g), f"${round(g * 0.244, 2)}"] for s, m, g in states]
    jur_rows.append(["TOTAL", str(total_miles), str(total_gal), f"${round(total_gal * 0.244, 2)}"])

    summary = [["Fleet MPG", str(mpg)], ["Total Miles", str(total_miles)],
               ["Total Gallons", str(total_gal)]]

    make_pdf(filepath, f"IFTA Report — {quarter} {year}", paras,
             tables=[("Jurisdictions", [jur_header] + jur_rows),
                     ("Summary", [["Metric", "Value"]] + summary)])
    return filepath


# ═══════════════════════════════════════════════════════════
# Standard test data
# ═══════════════════════════════════════════════════════════
GOOD_DRIVERS = [
    {"name": "James R Mitchell", "dob": "04/12/1978", "cdl": "TN-88234591", "state": "TN", "exp": 10, "age": 48},
    {"name": "Robert L Williams", "dob": "11/03/1980", "cdl": "TN-77123488", "state": "TN", "exp": 8, "age": 46},
    {"name": "David A Thompson", "dob": "07/22/1975", "cdl": "AL-55987234", "state": "AL", "exp": 14, "age": 51},
    {"name": "Michael J Garcia", "dob": "02/18/1982", "cdl": "AR-44321876", "state": "AR", "exp": 7, "age": 44},
    {"name": "Kevin P Brown", "dob": "09/30/1985", "cdl": "TN-99876543", "state": "TN", "exp": 5, "age": 41},
]

GOOD_VEHICLES = [
    {"unit": "T-101", "year": 2022, "make": "Freightliner", "model": "Cascadia 126", "vin": "3AKJHHDR5NSLA4521"},
    {"unit": "T-102", "year": 2021, "make": "Kenworth", "model": "T680", "vin": "1XKYD49X1MJ567234"},
    {"unit": "T-103", "year": 2023, "make": "Peterbilt", "model": "579", "vin": "2NP2HJ7X4PT345678"},
    {"unit": "T-104", "year": 2020, "make": "Volvo", "model": "VNL 760", "vin": "4V4NC9EH5LN234567"},
    {"unit": "T-105", "year": 2022, "make": "International", "model": "LT Series", "vin": "3HSDJAPR4NN876543"},
]


# ═══════════════════════════════════════════════════════════
# Scenario 1: Perfect Submission (copy existing)
# ═══════════════════════════════════════════════════════════
def gen_scenario_1():
    """Perfect submission — all documents present, all rules should pass."""
    out = ensure_dir(os.path.join(BASE_DIR, "test-1-perfect"))
    company = "Heartland Express Inc"
    gen_application(out, company)
    gen_driver_roster(out, company, GOOD_DRIVERS)
    gen_vehicle_schedule(out, company, GOOD_VEHICLES)
    gen_loss_runs(out, company)
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)
    # Copy CDL images from perfect-submission
    src_dl = os.path.join(os.path.dirname(__file__), "perfect-submission", "driver-licenses")
    if os.path.exists(src_dl):
        dst_dl = os.path.join(out, "driver-licenses")
        if os.path.exists(dst_dl):
            shutil.rmtree(dst_dl)
        shutil.copytree(src_dl, dst_dl)
    print(f"✅ Scenario 1: Perfect submission → {out}")


# ═══════════════════════════════════════════════════════════
# Scenario 2: Missing Driver Licenses
# ═══════════════════════════════════════════════════════════
def gen_scenario_2():
    """All docs except CDL images — should flag missing DL verification."""
    out = ensure_dir(os.path.join(BASE_DIR, "test-2-missing-dl"))
    company = "Pacific Freight Lines"
    gen_application(out, company, fein="45-9876321", mc="MC-654321", dot="DOT-9876543")
    gen_driver_roster(out, company, GOOD_DRIVERS)
    gen_vehicle_schedule(out, company, GOOD_VEHICLES)
    gen_loss_runs(out, company)
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)
    # NO driver license images
    print(f"✅ Scenario 2: Missing DL images → {out}")


# ═══════════════════════════════════════════════════════════
# Scenario 3: Bad Driver History
# ═══════════════════════════════════════════════════════════
def gen_scenario_3():
    """Drivers with DUI, excessive points — should trigger DRV-100, DRV-005/006."""
    out = ensure_dir(os.path.join(BASE_DIR, "test-3-bad-driver"))
    company = "Summit Transport LLC"

    bad_drivers = [
        {"name": "James R Mitchell", "dob": "04/12/1978", "cdl": "TN-88234591", "state": "TN",
         "exp": 10, "age": 48, "violations": "None", "accidents": "None"},
        {"name": "Robert L Williams", "dob": "11/03/1980", "cdl": "TN-77123488", "state": "TN",
         "exp": 8, "age": 46,
         "violations": "DUI/DWI (03/2023), Speeding 35mph over (08/2023), Reckless Driving (11/2023)",
         "accidents": "At-fault collision (04/2023)"},
        {"name": "David A Thompson", "dob": "07/22/1975", "cdl": "AL-55987234", "state": "AL",
         "exp": 14, "age": 51,
         "violations": "Speeding (02/2024), Following too close (05/2024), Improper lane change (08/2024), Speeding (11/2024), Running red light (01/2025)",
         "accidents": "None"},
        {"name": "Michael J Garcia", "dob": "02/18/2003", "cdl": "AR-44321876", "state": "AR",
         "exp": 1, "age": 22, "violations": "None", "accidents": "None"},
        {"name": "Kevin P Brown", "dob": "09/30/1985", "cdl": "TN-99876543", "state": "TN",
         "exp": 5, "age": 41, "violations": "None", "accidents": "None"},
    ]

    gen_application(out, company, fein="38-1234567", mc="MC-111222", dot="DOT-3334444")
    gen_driver_roster(out, company, bad_drivers)
    gen_vehicle_schedule(out, company, GOOD_VEHICLES)
    gen_loss_runs(out, company)
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)
    print(f"✅ Scenario 3: Bad driver history → {out}")


# ═══════════════════════════════════════════════════════════
# Scenario 4: Wrong/Misleading Filenames
# ═══════════════════════════════════════════════════════════
def gen_scenario_4():
    """Files have misleading names — tests content-based classification."""
    out = ensure_dir(os.path.join(BASE_DIR, "test-4-wrong-names"))
    company = "Mountain Ridge Carriers"

    # Application named as "LossRuns.pdf"
    gen_application(out, company, fein="71-5678901", mc="MC-333444", dot="DOT-5556667")
    os.rename(os.path.join(out, "Mountain_Ridge_Carriers_Application.pdf"),
              os.path.join(out, "LossRuns_2025.pdf"))

    # Driver roster named as "Equipment_List.xlsx"
    gen_driver_roster(out, company, GOOD_DRIVERS, filename="Equipment_List.xlsx")

    # Vehicle schedule named as "Drivers.xlsx"
    gen_vehicle_schedule(out, company, GOOD_VEHICLES, filename="Drivers.xlsx")

    # Actual loss runs named as "Application.pdf"
    gen_loss_runs(out, company, filename="Application_Form.pdf")

    # IFTA with wrong names
    gen_ifta(out, company, "Q1", 2026, filename="misc_report_jan.pdf")
    gen_ifta(out, company, "Q2", 2025, filename="financial_statement_q2.pdf")
    gen_ifta(out, company, "Q3", 2025, filename="driver_summary_q3.pdf")
    gen_ifta(out, company, "Q4", 2025, filename="insurance_docs_q4.pdf")

    print(f"✅ Scenario 4: Wrong filenames → {out}")


# ═══════════════════════════════════════════════════════════
# Scenario 5: Incomplete Submission
# ═══════════════════════════════════════════════════════════
def gen_scenario_5():
    """Missing IFTA reports and loss runs — should flag SUB-003, SUB-005."""
    out = ensure_dir(os.path.join(BASE_DIR, "test-5-incomplete"))
    company = "Valley Express Trucking"

    gen_application(out, company, fein="55-7777888", mc="MC-999000", dot="DOT-1112223")
    gen_driver_roster(out, company, GOOD_DRIVERS[:3])  # Only 3 drivers
    gen_vehicle_schedule(out, company, GOOD_VEHICLES[:3])  # Only 3 vehicles
    # NO loss runs
    # Only 2 IFTA quarters (need 4)
    gen_ifta(out, company, "Q1", 2026)
    gen_ifta(out, company, "Q2", 2025)

    print(f"✅ Scenario 5: Incomplete submission → {out}")


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating test scenarios for Knight Insurance AI Pipeline\n")
    print(f"Output directory: {BASE_DIR}\n")

    gen_scenario_1()
    gen_scenario_2()
    gen_scenario_3()
    gen_scenario_4()
    gen_scenario_5()

    print(f"\n{'='*60}")
    print(f"Generated 5 test scenarios in {BASE_DIR}/")
    print(f"\nScenario descriptions:")
    print(f"  1. test-1-perfect     → All docs, all rules pass")
    print(f"  2. test-2-missing-dl  → No CDL images submitted")
    print(f"  3. test-3-bad-driver  → DUI, excessive points, underage")
    print(f"  4. test-4-wrong-names → Misleading filenames")
    print(f"  5. test-5-incomplete  → Missing IFTA and loss runs")
