"""
Generate test scenarios 11-12 for cross-document conflict and duplicate detection.

Test Scenarios:
  11. conflicting-info  — Mismatched counts, company names, FEIN across docs (CON-001/002/003/004)
  12. duplicate-info    — Duplicate CDL numbers, duplicate VINs (CON-005/006)
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(__file__))
from generate_test_scenarios import (
    ensure_dir, make_pdf, make_excel, gen_ifta, GOOD_DRIVERS, GOOD_VEHICLES,
    BASE_DIR
)
from generate_additional_scenarios import gen_application_custom, gen_loss_runs_custom


def gen_driver_roster_custom(out_dir, company, drivers, filename=None):
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


def gen_vehicle_schedule_custom(out_dir, company, vehicles, filename=None):
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


# ═══════════════════════════════════════════════════════════
# Scenario 11: Conflicting Information Across Documents
# Triggers: CON-001, CON-002, CON-003, CON-004
# ═══════════════════════════════════════════════════════════
def gen_scenario_11():
    out = ensure_dir(os.path.join(BASE_DIR, "test-11-conflicting-info"))
    company = "Reliable Freight Corp"

    # Application says 5 units, 5 drivers
    gen_application_custom(out, company,
        fein="62-7834521", mc="MC-789456", dot="DOT-2345678",
        units=5, premium="$75,000",
    )

    # But roster has 7 drivers (mismatch!)
    extra_drivers = GOOD_DRIVERS + [
        {"name": "Sarah L Johnson", "dob": "03/15/1983", "cdl": "TN-55667788", "state": "TN", "exp": 6, "age": 43},
        {"name": "Chris M Davis", "dob": "09/22/1979", "cdl": "AL-66778899", "state": "AL", "exp": 11, "age": 47},
    ]
    gen_driver_roster_custom(out, company, extra_drivers)

    # Equipment schedule has 8 vehicles (mismatch with application's 5!)
    extra_vehicles = GOOD_VEHICLES + [
        {"unit": "T-106", "year": 2021, "make": "Kenworth", "model": "T880", "vin": "1XKYD49X1MJ111111"},
        {"unit": "T-107", "year": 2022, "make": "Freightliner", "model": "Cascadia", "vin": "3AKJHHDR5NSLA2222"},
        {"unit": "T-108", "year": 2023, "make": "Peterbilt", "model": "389", "vin": "2NP2HJ7X4PT333333"},
    ]
    gen_vehicle_schedule_custom(out, company, extra_vehicles)

    # Loss runs with DIFFERENT FEIN (mismatch!)
    gen_loss_runs_custom(out, "Reliable Freight Corp",
        claims=[["CLM-2024-001", "03/15/2024", "Minor fender bender", "Closed", "$4,200"]]
    )

    # IFTA with DIFFERENT company name (slight variation — "Reliable Freight Corporation" vs "Reliable Freight Corp")
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, "Reliable Freight Corporation", q, y)

    # Copy DLs
    src_dl = os.path.join(BASE_DIR, "test-1-perfect", "driver-licenses")
    dst_dl = os.path.join(out, "driver-licenses")
    if os.path.exists(src_dl):
        if os.path.exists(dst_dl):
            shutil.rmtree(dst_dl)
        shutil.copytree(src_dl, dst_dl)

    print(f"✅ Scenario 11: Conflicting Info → {out}")
    print(f"   Expected: REFER (CON-001 vehicle count, CON-002 driver count, CON-003 company name)")


# ═══════════════════════════════════════════════════════════
# Scenario 12: Duplicate Information
# Triggers: CON-005, CON-006
# ═══════════════════════════════════════════════════════════
def gen_scenario_12():
    out = ensure_dir(os.path.join(BASE_DIR, "test-12-duplicate-info"))
    company = "Precision Logistics LLC"

    gen_application_custom(out, company,
        fein="73-9988776", mc="MC-556677", dot="DOT-5566778",
        units=5, premium="$80,000",
    )

    # Driver roster with DUPLICATE CDL number (James Mitchell listed twice with same CDL!)
    dup_drivers = [
        {"name": "James R Mitchell", "dob": "04/12/1978", "cdl": "TN-88234591", "state": "TN", "exp": 10, "age": 48},
        {"name": "Robert L Williams", "dob": "11/03/1980", "cdl": "TN-77123488", "state": "TN", "exp": 8, "age": 46},
        {"name": "David A Thompson", "dob": "07/22/1975", "cdl": "AL-55987234", "state": "AL", "exp": 14, "age": 51},
        {"name": "Michael J Garcia", "dob": "02/18/1982", "cdl": "AR-44321876", "state": "AR", "exp": 7, "age": 44},
        # DUPLICATE: Same CDL as James Mitchell!
        {"name": "James Mitchell Jr", "dob": "01/05/1999", "cdl": "TN-88234591", "state": "TN", "exp": 3, "age": 27},
    ]
    gen_driver_roster_custom(out, company, dup_drivers)

    # Vehicle schedule with DUPLICATE VIN
    dup_vehicles = [
        {"unit": "T-101", "year": 2022, "make": "Freightliner", "model": "Cascadia 126", "vin": "3AKJHHDR5NSLA4521"},
        {"unit": "T-102", "year": 2021, "make": "Kenworth", "model": "T680", "vin": "1XKYD49X1MJ567234"},
        {"unit": "T-103", "year": 2023, "make": "Peterbilt", "model": "579", "vin": "2NP2HJ7X4PT345678"},
        {"unit": "T-104", "year": 2020, "make": "Volvo", "model": "VNL 760", "vin": "4V4NC9EH5LN234567"},
        # DUPLICATE VIN: Same as T-101!
        {"unit": "T-105", "year": 2022, "make": "Freightliner", "model": "Cascadia 126", "vin": "3AKJHHDR5NSLA4521"},
    ]
    gen_vehicle_schedule_custom(out, company, dup_vehicles)

    gen_loss_runs_custom(out, company,
        claims=[["CLM-2024-001", "03/15/2024", "Parking lot incident", "Closed", "$2,100"]]
    )
    for q, y in [("Q1", 2026), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025)]:
        gen_ifta(out, company, q, y)

    # Copy DLs
    src_dl = os.path.join(BASE_DIR, "test-1-perfect", "driver-licenses")
    dst_dl = os.path.join(out, "driver-licenses")
    if os.path.exists(src_dl):
        if os.path.exists(dst_dl):
            shutil.rmtree(dst_dl)
        shutil.copytree(src_dl, dst_dl)

    print(f"✅ Scenario 12: Duplicate Info → {out}")
    print(f"   Expected: REFER (CON-005 duplicate CDL, CON-006 duplicate VIN)")


if __name__ == "__main__":
    print("Generating conflict test scenarios (11-12)...")
    print("=" * 60)
    gen_scenario_11()
    gen_scenario_12()
    print("=" * 60)
    print("✅ All conflict scenarios generated!")
