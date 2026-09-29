"""
PostgreSQL Database Initializer for Smart Traffic Violation Logger.
Creates the database if it doesn't exist, initializes all tables,
and seeds initial officer credentials and sample violations.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import Config
from app import create_app
from models import db, Officer, Violation
from utils import generate_challan_number
from qr_utils import generate_qr_code
from flask import url_for
from datetime import datetime, timedelta

def setup_postgres():
    pg_user = Config.PG_USER
    pg_password = Config.PG_PASSWORD
    pg_host = Config.PG_HOST
    pg_port = Config.PG_PORT
    target_db = Config.PG_DB

    print(f"Connecting to PostgreSQL server at {pg_host}:{pg_port} as user '{pg_user}'...")

    try:
        # Connect to default 'postgres' database to check/create target database
        conn = psycopg2.connect(
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port,
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
        exists = cur.fetchone()

        if not exists:
            print(f"Database '{target_db}' does not exist. Creating database...")
            cur.execute(f'CREATE DATABASE "{target_db}";')
            print(f"[OK] Database '{target_db}' created successfully.")
        else:
            print(f"[OK] Database '{target_db}' already exists.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Could not connect to PostgreSQL server: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL service is started.")
        print("2. Credentials in .env (or config.py) match your PostgreSQL configuration.")
        return False

    # Now initialize tables and seed via Flask application context
    app = create_app()
    with app.app_context():
        print("Creating database schema tables in PostgreSQL...")
        db.create_all()
        print("[OK] Schema tables initialized successfully.")

        # Seed Officer
        if Officer.query.count() == 0:
            officer = Officer(
                username='officer1',
                full_name='Officer R. Sharma',
                badge_number='TP-8492'
            )
            officer.set_password('password123')
            db.session.add(officer)
            db.session.commit()
            print("[OK] Created default officer: 'officer1' / 'password123'")

        # Seed sample violations
        if Violation.query.count() == 0:
            print("Seeding sample traffic violations with generated QR codes...")
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
                    "vehicle_number": "TN59CD5678",
                    "violation_type": "Drunk Driving",
                    "location": "100 Feet Road, Near City Mall",
                    "violation_date": datetime.now() - timedelta(hours=5),
                    "fine_amount": 10000.0,
                    "payment_status": "Unpaid",
                    "notes": "Breathalyzer reading 64mg/100ml. Vehicle impounded temporarily."
                }
            ]

            with app.test_request_context():
                for item in sample_data:
                    challan_num = generate_challan_number()
                    public_url = url_for('public_challan', challan_number=challan_num, _external=True)
                    qr_file = generate_qr_code(challan_num, public_url, app.config['QR_FOLDER'])

                    v = Violation(
                        challan_number=challan_num,
                        vehicle_number=item['vehicle_number'],
                        violation_type=item['violation_type'],
                        location=item['location'],
                        violation_date=item['violation_date'],
                        fine_amount=item['fine_amount'],
                        payment_status=item['payment_status'],
                        officer_badge='TP-8492',
                        officer_name='Officer R. Sharma',
                        qr_filename=qr_file,
                        notes=item['notes']
                    )
                    db.session.add(v)
                    db.session.commit()
                    print(f"[OK] Seeded Challan {challan_num} for vehicle {item['vehicle_number']}")

    print("\n[SUCCESS] PostgreSQL setup and initialization complete!")
    return True

if __name__ == '__main__':
    setup_postgres()
