import os
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, abort
)

from config import Config
from models import db, Officer, Violation
from utils import (
    VIOLATION_TYPES,
    generate_challan_number,
    clean_vehicle_number,
    get_suggested_fine
)
from qr_utils import generate_qr_code


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Ensure QR directory exists
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

    # Authentication decorator
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'officer_id' not in session:
                flash('Authentication required. Please sign in to access officer controls.', 'warning')
                return redirect(url_for('login', next=request.path))
            return f(*args, **kwargs)
        return decorated_function

    # =========================================================================
    # AUTHENTICATION ROUTES
    # =========================================================================
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'officer_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            login_id = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            # Query by username or badge number
            officer = Officer.query.filter(
                (Officer.username == login_id.lower()) |
                (Officer.badge_number == login_id.upper())
            ).first()

            if officer and officer.check_password(password):
                session['officer_id'] = officer.id
                session['username'] = officer.username
                session['officer_name'] = officer.full_name or officer.username
                session['badge_number'] = officer.badge_number or 'HQ-OFFICER'
                flash(f'Welcome back, {session["officer_name"]}!', 'success')

                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials. Please verify your badge number or username and password.', 'danger')

        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'officer_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            full_name = request.form.get('full_name', '').strip()
            badge_number = request.form.get('badge_number', '').strip().upper()
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            errors = []
            if not full_name:
                errors.append('Officer full name is required.')
            if not badge_number:
                errors.append('Official badge number is required.')
            if not username:
                errors.append('Terminal username is required.')
            elif len(username) < 3:
                errors.append('Username must be at least 3 characters.')
            if not password:
                errors.append('Password is required.')
            elif len(password) < 6:
                errors.append('Password must be at least 6 characters.')
            elif password != confirm_password:
                errors.append('Passwords do not match.')

            if not errors:
                if Officer.query.filter_by(username=username).first():
                    errors.append('This username is already registered. Please choose another.')
                elif Officer.query.filter_by(badge_number=badge_number).first():
                    errors.append('An officer with this badge number is already registered.')

            if errors:
                for err in errors:
                    flash(err, 'danger')
                return render_template('register.html', form_data=request.form)

            new_officer = Officer(
                full_name=full_name,
                badge_number=badge_number,
                username=username
            )
            new_officer.set_password(password)

            db.session.add(new_officer)
            db.session.commit()

            flash('Officer account successfully created! You may now sign in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html', form_data=None)

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been securely signed out.', 'info')
        return redirect(url_for('login'))

    # =========================================================================
    # DASHBOARD
    # =========================================================================
    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        total_violations = Violation.query.count()
        paid_count = Violation.query.filter_by(payment_status='Paid').count()
        unpaid_count = Violation.query.filter_by(payment_status='Unpaid').count()

        total_amount = db.session.query(db.func.sum(Violation.fine_amount)).scalar() or 0.0
        paid_amount = (
            db.session.query(db.func.sum(Violation.fine_amount))
            .filter_by(payment_status='Paid')
            .scalar() or 0.0
        )
        unpaid_amount = (
            db.session.query(db.func.sum(Violation.fine_amount))
            .filter_by(payment_status='Unpaid')
            .scalar() or 0.0
        )

        today_start = datetime.combine(date.today(), datetime.min.time())
        today_violations = Violation.query.filter(Violation.violation_date >= today_start).count()

        recent_violations = (
            Violation.query.order_by(Violation.id.desc())
            .limit(8)
            .all()
        )

        return render_template(
            'dashboard.html',
            total_violations=total_violations,
            paid_count=paid_count,
            unpaid_count=unpaid_count,
            total_amount=total_amount,
            paid_amount=paid_amount,
            unpaid_amount=unpaid_amount,
            today_violations=today_violations,
            recent_violations=recent_violations
        )

    # =========================================================================
    # VIOLATION HISTORY & ADVANCED SEARCH / FILTERS
    # =========================================================================
    @app.route('/violations')
    @login_required
    def violations():
        vehicle_param = request.args.get('vehicle', '').strip()
        status_param = request.args.get('status', 'All').strip()
        type_param = request.args.get('violation_type', 'All').strip()
        date_param = request.args.get('date', '').strip()

        query = Violation.query

        cleaned_vehicle = clean_vehicle_number(vehicle_param)
        if cleaned_vehicle:
            query = query.filter(Violation.vehicle_number.ilike(f"%{cleaned_vehicle}%"))

        if status_param and status_param != 'All':
            query = query.filter(Violation.payment_status == status_param)

        if type_param and type_param != 'All':
            query = query.filter(Violation.violation_type == type_param)

        if date_param:
            try:
                filter_d = datetime.strptime(date_param, '%Y-%m-%d').date()
                day_start = datetime.combine(filter_d, datetime.min.time())
                day_end = datetime.combine(filter_d, datetime.max.time())
                query = query.filter(Violation.violation_date.between(day_start, day_end))
            except ValueError:
                pass

        results = query.order_by(Violation.violation_date.desc(), Violation.id.desc()).all()

        # Vehicle specific summary when vehicle search is requested
        vehicle_summary = None
        if cleaned_vehicle:
            all_for_vehicle = Violation.query.filter(
                Violation.vehicle_number.ilike(f"%{cleaned_vehicle}%")
            ).all()
            if all_for_vehicle:
                v_total = len(all_for_vehicle)
                v_unpaid = sum(1 for v in all_for_vehicle if not v.is_paid)
                v_paid = sum(1 for v in all_for_vehicle if v.is_paid)
                v_total_fine = sum(v.fine_amount for v in all_for_vehicle)
                v_unpaid_fine = sum(v.fine_amount for v in all_for_vehicle if not v.is_paid)
                v_paid_fine = sum(v.fine_amount for v in all_for_vehicle if v.is_paid)

                vehicle_summary = {
                    'vehicle_number': cleaned_vehicle,
                    'total_count': v_total,
                    'unpaid_count': v_unpaid,
                    'paid_count': v_paid,
                    'total_fine': v_total_fine,
                    'unpaid_total': v_unpaid_fine,
                    'paid_total': v_paid_fine
                }

        all_types = [t[0] for t in VIOLATION_TYPES]

        return render_template(
            'violations.html',
            violations=results,
            vehicle_query=cleaned_vehicle,
            selected_status=status_param,
            selected_type=type_param,
            selected_date=date_param,
            all_types=all_types,
            vehicle_summary=vehicle_summary
        )

    # =========================================================================
    # ADD VIOLATION (CREATE)
    # =========================================================================
    @app.route('/violations/add', methods=['GET', 'POST'])
    @login_required
    def add_violation():
        if request.method == 'POST':
            raw_vehicle = request.form.get('vehicle_number', '')
            violation_type = request.form.get('violation_type', '').strip()
            location = request.form.get('location', '').strip()
            date_str = request.form.get('violation_date', '').strip()
            fine_str = request.form.get('fine_amount', '').strip()
            notes = request.form.get('notes', '').strip()

            cleaned_vehicle = clean_vehicle_number(raw_vehicle)

            # Server-side validation
            errors = []
            if not cleaned_vehicle:
                errors.append('Vehicle registration number is mandatory.')
            elif len(cleaned_vehicle) < 3:
                errors.append('Vehicle registration number is too short.')

            if not violation_type:
                errors.append('Violation offense type is required.')

            if not location:
                errors.append('Offense location is required.')

            violation_dt = None
            if not date_str:
                violation_dt = datetime.now()
            else:
                try:
                    violation_dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        violation_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        errors.append('Invalid date and time format.')

            fine_amount = None
            try:
                fine_amount = float(fine_str)
                if fine_amount <= 0:
                    errors.append('Fine amount must be greater than zero.')
            except (ValueError, TypeError):
                errors.append('Fine amount must be a valid positive number.')

            if errors:
                for err in errors:
                    flash(err, 'danger')
                return render_template(
                    'add_violation.html',
                    violation_types=VIOLATION_TYPES,
                    current_datetime_str=datetime.now().strftime('%Y-%m-%dT%H:%M'),
                    form_data=request.form
                )

            # Generate unique challan number
            challan_number = generate_challan_number()

            # Dynamic public URL for QR Code
            public_url = url_for('public_challan', challan_number=challan_number, _external=True)

            # Generate QR Code
            qr_filename = generate_qr_code(
                challan_number=challan_number,
                public_url=public_url,
                qr_folder=app.config['QR_FOLDER']
            )

            # Create Violation Record
            new_violation = Violation(
                challan_number=challan_number,
                vehicle_number=cleaned_vehicle,
                violation_type=violation_type,
                location=location,
                violation_date=violation_dt,
                fine_amount=fine_amount,
                payment_status='Unpaid',
                officer_badge=session.get('badge_number'),
                officer_name=session.get('officer_name'),
                qr_filename=qr_filename,
                notes=notes
            )

            db.session.add(new_violation)
            db.session.commit()

            flash(f'Challan {challan_number} created successfully with verified QR code!', 'success')
            return redirect(url_for('violation_detail', id=new_violation.id))

        return render_template(
            'add_violation.html',
            violation_types=VIOLATION_TYPES,
            current_datetime_str=datetime.now().strftime('%Y-%m-%dT%H:%M'),
            form_data=None
        )

    # =========================================================================
    # VIOLATION DETAILS (READ)
    # =========================================================================
    @app.route('/violations/<int:id>')
    @login_required
    def violation_detail(id):
        violation = db.get_or_404(Violation, id)

        public_url = url_for('public_challan', challan_number=violation.challan_number, _external=True)

        # Ensure QR file exists on disk
        qr_path = os.path.join(app.config['QR_FOLDER'], f"{violation.challan_number}.png")
        if not os.path.exists(qr_path):
            violation.qr_filename = generate_qr_code(
                challan_number=violation.challan_number,
                public_url=public_url,
                qr_folder=app.config['QR_FOLDER']
            )
            db.session.commit()

        return render_template(
            'violation_detail.html',
            violation=violation,
            public_url=public_url
        )

    # =========================================================================
    # EDIT VIOLATION (UPDATE)
    # =========================================================================
    @app.route('/violations/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_violation(id):
        violation = db.get_or_404(Violation, id)

        if request.method == 'POST':
            raw_vehicle = request.form.get('vehicle_number', '')
            violation_type = request.form.get('violation_type', '').strip()
            location = request.form.get('location', '').strip()
            date_str = request.form.get('violation_date', '').strip()
            fine_str = request.form.get('fine_amount', '').strip()
            payment_status = request.form.get('payment_status', 'Unpaid').strip()
            notes = request.form.get('notes', '').strip()

            cleaned_vehicle = clean_vehicle_number(raw_vehicle)

            # Validation
            errors = []
            if not cleaned_vehicle:
                errors.append('Vehicle registration number is required.')
            if not violation_type:
                errors.append('Violation type is required.')
            if not location:
                errors.append('Location is required.')

            try:
                fine_amount = float(fine_str)
                if fine_amount <= 0:
                    errors.append('Fine amount must be greater than zero.')
            except (ValueError, TypeError):
                errors.append('Fine amount must be numeric.')

            violation_dt = violation.violation_date
            if date_str:
                try:
                    violation_dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        violation_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        errors.append('Invalid date format.')

            if errors:
                for err in errors:
                    flash(err, 'danger')
                return render_template(
                    'edit_violation.html',
                    violation=violation,
                    violation_types=VIOLATION_TYPES,
                    formatted_dt=violation.violation_date.strftime('%Y-%m-%dT%H:%M')
                )

            violation.vehicle_number = cleaned_vehicle
            violation.violation_type = violation_type
            violation.location = location
            violation.violation_date = violation_dt
            violation.fine_amount = fine_amount
            violation.payment_status = payment_status
            violation.notes = notes

            db.session.commit()
            flash(f'Challan {violation.challan_number} updated successfully.', 'success')
            return redirect(url_for('violation_detail', id=violation.id))

        formatted_dt = (
            violation.violation_date.strftime('%Y-%m-%dT%H:%M')
            if violation.violation_date else ''
        )

        return render_template(
            'edit_violation.html',
            violation=violation,
            violation_types=VIOLATION_TYPES,
            formatted_dt=formatted_dt
        )

    # =========================================================================
    # DELETE VIOLATION (DELETE)
    # =========================================================================
    @app.route('/violations/<int:id>/delete', methods=['POST'])
    @login_required
    def delete_violation(id):
        violation = db.get_or_404(Violation, id)
        challan_no = violation.challan_number

        # Optionally delete QR file from disk
        if violation.qr_filename:
            qr_path = os.path.join(app.config['QR_FOLDER'], violation.qr_filename)
            if os.path.exists(qr_path):
                try:
                    os.remove(qr_path)
                except OSError:
                    pass

        db.session.delete(violation)
        db.session.commit()

        flash(f'Challan {challan_no} has been permanently deleted.', 'success')
        return redirect(url_for('violations'))

    # =========================================================================
    # PAYMENT STATUS UPDATE
    # =========================================================================
    @app.route('/violations/<int:id>/pay', methods=['POST'])
    @login_required
    def mark_paid(id):
        violation = db.get_or_404(Violation, id)
        violation.payment_status = 'Paid'
        db.session.commit()
        flash(f'Challan {violation.challan_number} has been marked as Paid.', 'success')
        return redirect(request.referrer or url_for('violation_detail', id=violation.id))

    # =========================================================================
    # DIGITAL PRINTABLE CHALLAN
    # =========================================================================
    @app.route('/challan/<int:id>')
    @login_required
    def challan_view(id):
        violation = db.get_or_404(Violation, id)
        public_url = url_for('public_challan', challan_number=violation.challan_number, _external=True)

        # Ensure QR file exists on disk
        qr_path = os.path.join(app.config['QR_FOLDER'], f"{violation.challan_number}.png")
        if not os.path.exists(qr_path):
            violation.qr_filename = generate_qr_code(
                challan_number=violation.challan_number,
                public_url=public_url,
                qr_folder=app.config['QR_FOLDER']
            )
            db.session.commit()

        return render_template(
            'challan.html',
            violation=violation,
            public_url=public_url
        )

    # =========================================================================
    # PUBLIC CHALLAN STATUS (ACCESSIBLE WITHOUT LOGIN)
    # =========================================================================
    @app.route('/public/challan/<string:challan_number>')
    def public_challan(challan_number):
        violation = Violation.query.filter_by(challan_number=challan_number).first()
        if not violation:
            return render_template('404.html'), 404

        return render_template(
            'public_status.html',
            violation=violation
        )

    @app.route('/public/challan/<string:challan_number>/pay', methods=['POST'])
    def public_pay_challan(challan_number):
        violation = Violation.query.filter_by(challan_number=challan_number).first()
        if not violation:
            return render_template('404.html'), 404

        violation.payment_status = 'Paid'
        db.session.commit()
        flash(f'Payment of ₹{violation.fine_amount:,.2f} verified and reconciled successfully. Thank you!', 'success')
        return redirect(url_for('public_challan', challan_number=challan_number))

    # =========================================================================
    # PUBLIC CITIZEN SEARCH PORTAL
    # =========================================================================
    @app.route('/public/search')
    def public_search():
        query_str = request.args.get('q', '').strip()
        results = []
        searched = False
        unpaid_count = 0
        paid_count = 0
        unpaid_total = 0.0
        paid_total = 0.0

        if query_str:
            searched = True
            cleaned = clean_vehicle_number(query_str)
            # Search by vehicle number or challan number
            results = Violation.query.filter(
                (Violation.vehicle_number.ilike(f"%{cleaned}%")) |
                (Violation.challan_number.ilike(f"%{query_str}%"))
            ).order_by(Violation.violation_date.desc()).all()

            unpaid_count = sum(1 for v in results if not v.is_paid)
            paid_count = sum(1 for v in results if v.is_paid)
            unpaid_total = sum(v.fine_amount for v in results if not v.is_paid)
            paid_total = sum(v.fine_amount for v in results if v.is_paid)

        return render_template(
            'public_search.html',
            search_query=query_str,
            searched=searched,
            results=results,
            unpaid_count=unpaid_count,
            paid_count=paid_count,
            unpaid_total=unpaid_total,
            paid_total=paid_total
        )

    # =========================================================================
    # ERROR HANDLERS
    # =========================================================================
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Ensure database schema is initialized
    with app.app_context():
        db.create_all()
        print(f"[DATABASE] Connected to: {app.config.get('DB_ENGINE', app.config['SQLALCHEMY_DATABASE_URI'])}")

    return app


if __name__ == '__main__':
    app = create_app()
    print("Starting Smart Traffic Violation Logger on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
