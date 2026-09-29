import re
from datetime import datetime
from models import db, Violation

VIOLATION_TYPES = [
    ("No Helmet", 1000),
    ("Overspeeding", 2000),
    ("Signal Jump", 1000),
    ("No Seat Belt", 1000),
    ("Drunk Driving", 10000),
    ("Wrong Parking", 500),
    ("Driving Without License", 5000),
    ("Triple Riding", 1000),
    ("Mobile Phone While Driving", 1500),
    ("Other", 1000),
]

def get_suggested_fine(v_type):
    for name, amount in VIOLATION_TYPES:
        if name.lower() == (v_type or "").strip().lower():
            return amount
    return 1000

def generate_challan_number():
    """
    Generates a unique challan number formatted as TVL-YYYY-XXXXXX
    e.g. TVL-2026-000001
    """
    current_year = datetime.now().year
    prefix = f"TVL-{current_year}-"

    # Find the latest violation with this year's prefix
    latest = (
        Violation.query.filter(Violation.challan_number.like(f"{prefix}%"))
        .order_by(Violation.id.desc())
        .first()
    )

    next_seq = 1
    if latest and latest.challan_number:
        try:
            seq_part = latest.challan_number.split("-")[-1]
            next_seq = int(seq_part) + 1
        except (ValueError, IndexError):
            next_seq = Violation.query.count() + 1

    # Ensure uniqueness loop
    while True:
        candidate = f"{prefix}{next_seq:06d}"
        if not Violation.query.filter_by(challan_number=candidate).first():
            return candidate
        next_seq += 1

def clean_vehicle_number(vehicle_number):
    """
    Trims, strips special characters (or spaces), and converts to uppercase.
    Example: 'tn 38 ab 1234' -> 'TN38AB1234'
    """
    if not vehicle_number:
        return ""
    # Remove whitespace and hyphens for consistency
    cleaned = re.sub(r'[\s\-]', '', vehicle_number).upper()
    return cleaned
