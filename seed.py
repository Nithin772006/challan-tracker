import os
from datetime import datetime, timedelta
from app import create_app
from models import db, Officer, Violation
from utils import generate_challan_number
from qr_utils import generate_qr_code
from flask import url_for

def seed_database():
    app = create_app()
    with app.app_context():
        # Ensure tables
        db.create_all()

        # Find existing registered officer
        officer = Officer.query.first()
        if not officer:
            print("[NOTICE] No officer found in database. Please register an officer first at /register or run:")
            print("  python create_officer.py")
            return
        print(f"[OK] Linking violations to registered officer: {officer.full_name} ({officer.badge_number})")

        # Sample Violations
        sample_data = [
            {
                "vehicle_number": "TN38AB1234",
                "violation_type": "No Helmet",
                "location": "Crosscut Road, Gandhipuram Junction",
                "violation_date": datetime.now() - timedelta(hours=2),
                "fine_amount": 1000.0,
                "payment_status": "Unpaid",
                "notes": "Rider without approved ISI safety helmet observed via junction PTZ camera."
            },
            {
                "vehicle_number": "TN38AB1234",
                "violation_type": "Overspeeding",
                "location": "Avinashi Road Flyover, Sector 2",
                "violation_date": datetime.now() - timedelta(days=3),
                "fine_amount": 2000.0,
                "payment_status": "Paid",
                "notes": "Radar speed trap captured 84 km/h in 50 km/h urban zone."
            },
            {
                "vehicle_number": "TN38AB1234",
                "violation_type": "Signal Jump",
                "location": "Lakshmi Mills Signal, Trichy Rd",
                "violation_date": datetime.now() - timedelta(days=12),
                "fine_amount": 1000.0,
                "payment_status": "Paid",
                "notes": "Crossed stop line 4.2 seconds into red cycle."
            },
            {
                "vehicle_number": "TN59CD5678",
                "violation_type": "Drunk Driving",
                "location": "100 Feet Road, Near City Mall",
                "violation_date": datetime.now() - timedelta(hours=5),
                "fine_amount": 10000.0,
                "payment_status": "Unpaid",
                "notes": "Breathalyzer reading 64mg/100ml. Vehicle impounded temporarily."
            },
            {
                "vehicle_number": "TN37EF9012",
                "violation_type": "Wrong Parking",
                "location": "RS Puram DB Road Commercial Zone",
                "violation_date": datetime.now() - timedelta(days=1),
                "fine_amount": 500.0,
                "payment_status": "Unpaid",
                "notes": "Obstructing emergency fire hydrant access."
            },
            {
                "vehicle_number": "KA01MJ4589",
                "violation_type": "Mobile Phone While Driving",
                "location": "Airport Road Junction",
                "violation_date": datetime.now() - timedelta(days=2),
                "fine_amount": 1500.0,
                "payment_status": "Paid",
                "notes": "Handheld phone usage during active vehicular maneuvering."
            },
            {
                "vehicle_number": "MH02BQ7711",
                "violation_type": "Triple Riding",
                "location": "Mettupalayam Highway Checkpost",
                "violation_date": datetime.now() - timedelta(days=4),
                "fine_amount": 1000.0,
                "payment_status": "Unpaid",
                "notes": "Three persons riding on a two-wheeler without protective headgear."
            },
            {
                "vehicle_number": "DL04AK3399",
                "violation_type": "Driving Without License",
                "location": "Race Course Outer Ring",
                "violation_date": datetime.now() - timedelta(days=7),
                "fine_amount": 5000.0,
                "payment_status": "Paid",
                "notes": "Driver unable to produce valid driving license or Digilocker credential."
            }
        ]

        # Check existing count
        existing_count = Violation.query.count()
        if existing_count >= len(sample_data):
            print(f"Database already contains {existing_count} violations. Skipping seed insertion.")
            return

        with app.test_request_context():
            for item in sample_data:
                challan_num = generate_challan_number()
                public_url = url_for('public_challan', challan_number=challan_num, _external=True)

                qr_file = generate_qr_code(
                    challan_number=challan_num,
                    public_url=public_url,
                    qr_folder=app.config['QR_FOLDER']
                )

                violation = Violation(
                    challan_number=challan_num,
                    vehicle_number=item['vehicle_number'],
                    violation_type=item['violation_type'],
                    location=item['location'],
                    violation_date=item['violation_date'],
                    fine_amount=item['fine_amount'],
                    payment_status=item['payment_status'],
                    officer_badge=officer.badge_number,
                    officer_name=officer.full_name,
                    qr_filename=qr_file,
                    notes=item['notes']
                )
                db.session.add(violation)
                db.session.commit()
                print(f"[OK] Seeded Challan {challan_num} for vehicle {item['vehicle_number']} (Status: {item['payment_status']})")

        print("\nAll sample violations and QR codes generated successfully!")

if __name__ == '__main__':
    seed_database()
