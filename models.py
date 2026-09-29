from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class Officer(db.Model):
    __tablename__ = 'officers'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    badge_number = db.Column(db.String(50), unique=True, nullable=True)
    full_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Officer {self.username} - {self.badge_number}>'


class Violation(db.Model):
    __tablename__ = 'violations'

    id = db.Column(db.Integer, primary_key=True)
    challan_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    vehicle_number = db.Column(db.String(20), nullable=False, index=True)
    violation_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    violation_date = db.Column(db.DateTime, nullable=False, default=utc_now)
    fine_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), nullable=False, default='Unpaid')
    officer_badge = db.Column(db.String(50), nullable=True)
    officer_name = db.Column(db.String(120), nullable=True)
    qr_filename = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    @property
    def is_paid(self):
        return self.payment_status.strip().lower() == 'paid'

    @property
    def formatted_date(self):
        if self.violation_date:
            return self.violation_date.strftime('%d %b %Y, %I:%M %p')
        return 'N/A'

    @property
    def formatted_amount(self):
        return f"₹{self.fine_amount:,.2f}"

    def __repr__(self):
        return f'<Violation {self.challan_number} - {self.vehicle_number}>'
