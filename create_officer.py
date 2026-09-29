"""
CLI Utility to create authentic Officer accounts directly in the database (Supabase).
Usage:
  python create_officer.py --username r_sharma --badge TP-8492 --name "Officer R. Sharma" --password MySecretPassword123!
Or interactively:
  python create_officer.py
"""

import sys
import argparse
import getpass
from app import create_app
from models import db, Officer

def create_officer(username, badge_number, full_name, password):
    app = create_app()
    with app.app_context():
        # Check uniqueness
        if Officer.query.filter_by(username=username.lower()).first():
            print(f"[ERROR] Officer with username '{username}' already exists.")
            return False

        if badge_number and Officer.query.filter_by(badge_number=badge_number.upper()).first():
            print(f"[ERROR] Officer with badge number '{badge_number}' already exists.")
            return False

        officer = Officer(
            username=username.lower(),
            badge_number=badge_number.upper() if badge_number else None,
            full_name=full_name
        )
        officer.set_password(password)

        db.session.add(officer)
        db.session.commit()
        print(f"[SUCCESS] Officer '{full_name}' (Badge: {badge_number}, Username: {username}) registered successfully in database!")
        return True

def main():
    parser = argparse.ArgumentParser(description="Register a new officer in the database.")
    parser.add_argument("--username", help="Terminal login username")
    parser.add_argument("--badge", help="Official badge number (e.g. TP-8492)")
    parser.add_argument("--name", help="Officer full name")
    parser.add_argument("--password", help="Account password")

    args = parser.parse_args()

    username = args.username
    badge = args.badge
    name = args.name
    password = args.password

    # Interactive prompt if arguments not provided
    if not username:
        username = input("Enter Terminal Username: ").strip()
    if not badge:
        badge = input("Enter Official Badge Number (e.g. TP-8492): ").strip()
    if not name:
        name = input("Enter Full Name: ").strip()
    if not password:
        password = getpass.getpass("Enter Secure Password (min 6 chars): ")
        confirm = getpass.getpass("Confirm Password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)

    if len(password) < 6:
        print("[ERROR] Password must be at least 6 characters long.")
        sys.exit(1)

    create_officer(username, badge, name, password)

if __name__ == '__main__':
    main()
