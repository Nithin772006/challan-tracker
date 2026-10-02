"""
Seed Script: Populates 100 distinct traffic violation records into the database.
Each record has:
- A unique vehicle registration number across various states (TN, KA, MH, DL, KL, TS, AP, GJ, RJ, UP, etc.)
- A diverse set of violation types and corresponding realistic fine amounts
- Both Paid and Unpaid statuses (~50/50 distribution)
- Authentic locations, realistic dates/times across the past 60 days
- Linked to active registered officers
- Fully generated QR codes saved to static/qr/
- Synced to both active Supabase database and local SQLite database.
"""

import os
import sys
import random
import sqlite3
from datetime import datetime, timedelta, timezone

# Ensure project root is in python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from app import create_app
from models import db, Officer, Violation
from qr_utils import generate_qr_code

# Predefined 100 distinct vehicle registration numbers across different Indian states and RTOs
UNIQUE_VEHICLE_NUMBERS = [
    # Tamil Nadu (TN)
    "TN01AW4921", "TN02BF8312", "TN03CL1743", "TN04DX9204", "TN05ER3851",
    "TN07FK6472", "TN09GH2193", "TN10HJ7534", "TN11JM4865", "TN14KP1256",
    "TN18LQ9387", "TN20MR5618", "TN22NT8049", "TN37PU3470", "TN38QV6791",
    "TN39RW9122", "TN43SX2453", "TN45TY5784", "TN58UZ8115", "TN59VA1446",
    "TN66WB4777", "TN72XC7008", "TN74YD9339", "TN85ZE2660", "TN99AF5991",
    
    # Karnataka (KA)
    "KA01BG8213", "KA02CH1544", "KA03DJ4875", "KA04EK7106", "KA05FL9437",
    "KA19GM2768", "KA20HN5099", "KA25JP8320", "KA51KR1651", "KA53LS4982",
    "KA09MT7213", "KA14PU9544", "KA22QV2875", "KA32RW5106", "KA41SX7437",

    # Maharashtra (MH)
    "MH01TY9768", "MH02UZ3099", "MH03VA5320", "MH04WB7651", "MH12XC9982",
    "MH14YD2213", "MH20ZE4544", "MH31AF6875", "MH43BG9106", "MH47CH1437",
    "MH09DJ3768", "MH15EK6099", "MH18FL8320", "MH27GM1651", "MH48HN3982",

    # Delhi (DL)
    "DL01JP6213", "DL02KR8544", "DL03LS1875", "DL04MT4106", "DL05PU6437",
    "DL06QV8768", "DL07RW1099", "DL08SX3320", "DL09TY5651", "DL10UZ7982",
    "DL11VA9213", "DL12WB2544", "DL04XC4875", "DL08YD7106", "DL09ZE9437",

    # Kerala (KL)
    "KL01AF1768", "KL07BG4099", "KL08CH6320", "KL11DJ8651", "KL14EK1982",
    "KL40FL3213", "KL65GM5544", "KL02HN7875",

    # Telangana (TS)
    "TS07JP9106", "TS08KR2437", "TS09LS4768", "TS10MT7099", "TS11PU9320",
    "TS12QV1651", "TS15RW3982",

    # Andhra Pradesh (AP)
    "AP03SX5213", "AP09TY7544", "AP16UZ9875", "AP21VA2106", "AP39WB4437",

    # Gujarat (GJ)
    "GJ01XC6768", "GJ03YD9099", "GJ05ZE1320", "GJ06AF3651", "GJ27BG5982",

    # Rajasthan (RJ)
    "RJ14CH7213", "RJ20DJ9544", "RJ27EK1875", "RJ45FL4106",

    # Uttar Pradesh (UP)
    "UP14GM6437", "UP16HN8768", "UP32JP1099", "UP78KR3320",

    # West Bengal (WB) & Haryana (HR)
    "WB02LS5651", "WB06MT7982", "WB20PU9213", "HR26QV2544", "HR51RW4875",
]

# Violation catalog with realistic notes templates and fine amounts
VIOLATION_CATALOG = [
    {
        "type": "No Helmet",
        "fine": 1000.0,
        "notes_pool": [
            "Rider without approved ISI safety helmet observed via junction camera.",
            "Rider and pillion both operating motorized two-wheeler without protective headgear.",
            "Two-wheeler operator observed with non-standard helmet unstrapped.",
            "Captured by automated ANPR camera during morning rush hour without helmet."
        ]
    },
    {
        "type": "Overspeeding",
        "fine": 2000.0,
        "notes_pool": [
            "Radar speed gun captured vehicle at 86 km/h in a designated 50 km/h urban sector.",
            "Doppler radar clocked 104 km/h on expressway sector with 70 km/h statutory ceiling.",
            "Speed sensor detected high speed crossing at 78 km/h in hospital silence zone.",
            "Laser speed trap flagged vehicle exceeding posted limit by 32 km/h."
        ]
    },
    {
        "type": "Signal Jump",
        "fine": 1000.0,
        "notes_pool": [
            "Crossed stop line 3.8 seconds after red signal engaged at intersection.",
            "Failed to stop at red aspect, forcing cross-traffic right of way blockage.",
            "Automated red light violation detection system (RLVD) triggered at signal pole.",
            "Disregarded amber and entered junction during active red phase."
        ]
    },
    {
        "type": "No Seat Belt",
        "fine": 1000.0,
        "notes_pool": [
            "Driver observed operating four-wheeler without primary safety restraint engaged.",
            "Driver and front passenger traveling without wearing factory fitted seatbelts.",
            "Traffic surveillance camera flagged unbuckled seatbelt during highway transit.",
            "Driver intercepted at checkpost with seatbelt tucked behind backrest."
        ]
    },
    {
        "type": "Drunk Driving",
        "fine": 10000.0,
        "notes_pool": [
            "Breathalyzer screening recorded 68 mg/100 ml BAC. Vehicle impounded pending magistrate hearing.",
            "Sobriety checkpoint test indicated 82 mg/100 ml BAC. Summary court appearance ordered.",
            "Suspect flagged during late night special enforcement drive; test reading 58 mg/100 ml BAC.",
            "Alcohol breath test positive at 94 mg/100 ml. Vehicle keys retained under section 185 MV Act."
        ]
    },
    {
        "type": "Wrong Parking",
        "fine": 500.0,
        "notes_pool": [
            "Vehicle parked in marked 'No Parking' commercial corridor obstructing delivery bay.",
            "Parked within 5 meters of active fire hydrant and emergency egress lane.",
            "Vehicle parked parallel to curb in designated double-parking restriction zone.",
            "Stationary vehicle abandoned in front of hospital main ambulance gate."
        ]
    },
    {
        "type": "Driving Without License",
        "fine": 5000.0,
        "notes_pool": [
            "Driver unable to produce valid permanent DL or electronic Digilocker credential upon demand.",
            "Operating class of vehicle not endorsed on driver license. Section 3/181 MV Act applied.",
            "Driver license expired over 18 months ago with no renewal receipt or application proof.",
            "Minor/unlicensed driver apprehended operating motor vehicle on public highway."
        ]
    },
    {
        "type": "Triple Riding",
        "fine": 1000.0,
        "notes_pool": [
            "Three individuals riding simultaneously on a two-wheeler vehicle.",
            "Triple riding observed without protective helmets on arterial flyover.",
            "Two-wheeler overloaded with three adult passengers endangering public safety.",
            "Captured by smart city PTZ camera carrying two pillion passengers."
        ]
    },
    {
        "type": "Mobile Phone While Driving",
        "fine": 1500.0,
        "notes_pool": [
            "Handheld mobile phone use while actively steering motor vehicle in traffic stream.",
            "Driver observed texting/browsing screen while negotiating busy traffic rotary.",
            "Holding cell phone against ear with shoulder during active highway transition.",
            "Video evidence recorded driver engaged in handheld phone conversation at 45 km/h."
        ]
    },
    {
        "type": "Other",
        "fine": 1000.0,
        "notes_pool": [
            "Defective and non-standard high security registration plate (HSRP) with obscured numerals.",
            "Unauthorized fitment of heavy tint sun control film below statutory 70% VLT visibility limit.",
            "Driving against designated one-way vehicular direction during peak hour.",
            "Operating vehicle emitting visible black smoke; failure to present valid PUC certificate."
        ]
    }
]

# Diverse realistic locations
LOCATIONS = [
    # Coimbatore
    "Gandhipuram Crosscut Road Junction, Coimbatore",
    "Avinashi Road Flyover, Sector 2, Coimbatore",
    "Lakshmi Mills Signal, Trichy Road, Coimbatore",
    "RS Puram DB Road Commercial Zone, Coimbatore",
    "100 Feet Road, Near City Center Mall, Coimbatore",
    "Airport Road Junction, SITRA, Coimbatore",
    "Race Course Ring Road, Near Collectorate, Coimbatore",
    "Saibaba Colony 7th Street Cross, Coimbatore",
    "Peelamedu Hope College Signal, Coimbatore",
    "Singanallur Bus Stand Signal, Trichy Rd, Coimbatore",
    "Ramanathapuram Junction, Coimbatore",
    "Ukkadam Bypass Toll Plaza, Coimbatore",
    "Saravanampatti IT Corridor, Sathy Rd, Coimbatore",
    "Thudiyalur Checkpost, Mettupalayam Rd, Coimbatore",
    "Brookefields Mall Signal, Sukrawarpet, Coimbatore",
    # Chennai
    "Anna Salai Gemini Flyover, Chennai",
    "OMR Sholinganallur Junction, Chennai",
    "Guindy Kathipara Grade Separator, Chennai",
    "T. Nagar Pondy Bazaar Pedestrian Cross, Chennai",
    "Marina Beach Kamarajar Salai, Chennai",
    "Koyambedu CMBT Roundabout, Chennai",
    "Velachery Bypass Road Signal, Chennai",
    # Bangalore
    "Indiranagar 100 Feet Road Signal, Bangalore",
    "Silk Board Junction, Hosur Road, Bangalore",
    "Koramangala 80 Feet Road Intersection, Bangalore",
    "MG Road - Brigade Road Junction, Bangalore",
    "Whitefield ITPL Main Road Signal, Bangalore",
    "Hebbal Flyover Inbound Lane, Bangalore",
    # Mumbai & Hyderabad & Delhi
    "Marine Drive Promenade, Churchgate, Mumbai",
    "Bandra-Worli Sea Link Toll Plaza, Mumbai",
    "Western Express Highway, Andheri East, Mumbai",
    "HITEC City Cyber Towers Junction, Hyderabad",
    "Gachibowli Outer Ring Road Exit, Hyderabad",
    "Connaught Place Outer Circle, Radial 4, New Delhi",
    "Ring Road AIIMS Flyover, New Delhi",
    "DND Flyway Expressway Toll, New Delhi",
]

def seed_100_violations():
    # Trim to exactly 100 plates and ensure uniqueness
    plate_list = list(dict.fromkeys(UNIQUE_VEHICLE_NUMBERS))[:100]
    assert len(plate_list) == 100, f"Expected 100 plates, got {len(plate_list)}"

    app = create_app()
    with app.app_context():
        # Ensure tables exist
        db.create_all()

        # Fetch all available registered officers
        officers = Officer.query.all()
        if not officers:
            print("[ERROR] No officers found in database. Please run create_officer.py first.")
            return

        print(f"[INFO] Found {len(officers)} officers in database to assign violations:")
        for off in officers:
            print(f"  - {off.full_name} ({off.badge_number})")

        # Determine starting sequence for unique challan numbers
        # Find maximum sequence existing in both Supabase and SQLite
        current_year = datetime.now().year
        prefix = f"TVL-{current_year}-"

        # Check Supabase max
        existing_violations = Violation.query.filter(Violation.challan_number.like(f"{prefix}%")).all()
        max_seq = 0
        existing_plates_sb = set()
        for v in existing_violations:
            existing_plates_sb.add(v.vehicle_number)
            try:
                seq = int(v.challan_number.split("-")[-1])
                if seq > max_seq:
                    max_seq = seq
            except (ValueError, IndexError):
                pass

        # Check SQLite max if database.db exists
        sqlite_path = os.path.join(BASE_DIR, 'database.db')
        if os.path.exists(sqlite_path):
            try:
                conn = sqlite3.connect(sqlite_path)
                c = conn.cursor()
                rows = c.execute("SELECT challan_number FROM violations WHERE challan_number LIKE ?", (f"{prefix}%",)).fetchall()
                for (ch_num,) in rows:
                    try:
                        seq = int(ch_num.split("-")[-1])
                        if seq > max_seq:
                            max_seq = seq
                    except (ValueError, IndexError):
                        pass
                conn.close()
            except Exception as e:
                print(f"[WARN] Error reading sqlite max sequence: {e}")

        start_seq = max(max_seq, 12) + 1
        print(f"[INFO] Starting challan sequence at: {prefix}{start_seq:06d}")

        # Distribution of statuses: 50 Unpaid, 50 Paid
        statuses = ["Unpaid"] * 50 + ["Paid"] * 50
        # Deterministic shuffle with seed for reproducibility
        rng = random.Random(42)
        rng.shuffle(statuses)

        # Distribute 100 records evenly across the 10 violation types (10 records each)
        types_pool = []
        for v_cat in VIOLATION_CATALOG:
            for _ in range(10):
                types_pool.append(v_cat)
        rng.shuffle(types_pool)

        created_violations = []
        qr_folder = app.config['QR_FOLDER']
        os.makedirs(qr_folder, exist_ok=True)

        now = datetime.now(timezone.utc)

        print("\n[START] Generating 100 distinct violation records...")

        for i in range(100):
            seq_num = start_seq + i
            challan_num = f"{prefix}{seq_num:06d}"
            vehicle_plate = plate_list[i]
            v_info = types_pool[i]
            status = statuses[i]

            # Realistic date: spread between 60 days ago and today
            days_ago = rng.randint(0, 58)
            hours_ago = rng.randint(0, 23)
            minutes_ago = rng.randint(0, 59)
            offense_dt = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            # Assign officer cyclically
            officer = officers[i % len(officers)]

            # Location and notes
            loc = LOCATIONS[i % len(LOCATIONS)]
            note = rng.choice(v_info["notes_pool"])

            # Amount variations for realistic diversity
            base_fine = v_info["fine"]
            if v_info["type"] == "Overspeeding":
                fine_amount = rng.choice([1500.0, 2000.0, 2500.0, 3000.0])
            elif v_info["type"] == "Wrong Parking":
                fine_amount = rng.choice([500.0, 1000.0])
            elif v_info["type"] == "Drunk Driving":
                fine_amount = rng.choice([10000.0, 15000.0])
            elif v_info["type"] == "Other":
                fine_amount = rng.choice([500.0, 1000.0, 1500.0, 2000.0])
            else:
                fine_amount = base_fine

            # Generate public URL for QR Code
            public_url = f"http://127.0.0.1:5000/public/challan/{challan_num}"

            # Generate QR Code file
            qr_file = generate_qr_code(
                challan_number=challan_num,
                public_url=public_url,
                qr_folder=qr_folder
            )

            violation = Violation(
                challan_number=challan_num,
                vehicle_number=vehicle_plate,
                violation_type=v_info["type"],
                location=loc,
                violation_date=offense_dt,
                fine_amount=fine_amount,
                payment_status=status,
                officer_badge=officer.badge_number,
                officer_name=officer.full_name,
                qr_filename=qr_file,
                notes=note,
                created_at=offense_dt,
                updated_at=offense_dt
            )

            created_violations.append(violation)
            db.session.add(violation)

        # Commit all to primary database (Supabase)
        db.session.commit()
        print(f"[SUCCESS] Successfully committed 100 violations to primary DB (Supabase)!")

        # Also sync to SQLite database.db so both engines have identical records
        if os.path.exists(sqlite_path):
            try:
                conn = sqlite3.connect(sqlite_path)
                c = conn.cursor()
                for v in created_violations:
                    # Check if already in SQLite
                    exists = c.execute("SELECT id FROM violations WHERE challan_number = ?", (v.challan_number,)).fetchone()
                    if not exists:
                        c.execute("""
                            INSERT INTO violations (
                                challan_number, vehicle_number, violation_type, location,
                                violation_date, fine_amount, payment_status, officer_badge,
                                officer_name, qr_filename, notes, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            v.challan_number,
                            v.vehicle_number,
                            v.violation_type,
                            v.location,
                            v.violation_date.strftime('%Y-%m-%d %H:%M:%S'),
                            v.fine_amount,
                            v.payment_status,
                            v.officer_badge,
                            v.officer_name,
                            v.qr_filename,
                            v.notes,
                            v.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            v.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                        ))
                conn.commit()
                conn.close()
                print(f"[SUCCESS] Successfully synchronized 100 violations to local SQLite (database.db)!")
            except Exception as e:
                print(f"[WARN] SQLite sync notice: {e}")

        # Summary statistics
        total_count = Violation.query.count()
        paid_count = Violation.query.filter_by(payment_status='Paid').count()
        unpaid_count = Violation.query.filter_by(payment_status='Unpaid').count()
        print("\n================ DATABASE SUMMARY ================")
        print(f"Total Violations in DB : {total_count}")
        print(f"Total Paid Violations  : {paid_count}")
        print(f"Total Unpaid Violations: {unpaid_count}")
        print("==================================================")

if __name__ == '__main__':
    seed_100_violations()
