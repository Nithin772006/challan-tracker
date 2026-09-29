import os
import unittest
from datetime import datetime
from app import create_app
from models import db, Officer, Violation

class SmartTrafficLoggerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Ensure an active test officer exists for authenticated tests
            if not Officer.query.filter_by(username='test_officer').first():
                test_off = Officer(
                    username='test_officer',
                    badge_number='TP-TEST-01',
                    full_name='Test Officer'
                )
                test_off.set_password('TestSecurePassword123!')
                db.session.add(test_off)
                db.session.commit()

    def login(self, username='test_officer', password='TestSecurePassword123!'):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_01_public_access_no_login_needed(self):
        """Public pages should be accessible without authentication."""
        res = self.client.get('/public/search')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'CITIZEN E-ENFORCEMENT PORTAL', res.data)

        # Test valid public challan status
        with self.app.app_context():
            v = Violation.query.first()
            if v:
                res = self.client.get(f'/public/challan/{v.challan_number}')
                self.assertEqual(res.status_code, 200)
                self.assertIn(b'Verified Digital Challan', res.data)
                self.assertIn(v.vehicle_number.encode(), res.data)

    def test_02_protected_routes_redirect_to_login(self):
        """Officer routes should require authentication."""
        routes = ['/dashboard', '/violations', '/violations/add']
        for route in routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 302)
            self.assertIn('/login', res.headers['Location'])

    def test_03_officer_registration_and_login(self):
        """Test registering a new officer and logging in."""
        import random
        rand_suffix = random.randint(1000, 9999)
        reg_username = f"officer_{rand_suffix}"
        reg_badge = f"TP-{rand_suffix}"

        # Test registration
        res = self.client.post('/register', data={
            'full_name': f'Officer Test {rand_suffix}',
            'badge_number': reg_badge,
            'username': reg_username,
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Officer account successfully created', res.data)

        # Test login with newly registered username
        res_login = self.login(username=reg_username, password='StrongPassword2026!')
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Enforcement Dashboard', res_login.data)

        # Test login with badge number instead of username
        self.logout()
        res_badge_login = self.login(username=reg_badge, password='StrongPassword2026!')
        self.assertEqual(res_badge_login.status_code, 200)
        self.assertIn(b'Enforcement Dashboard', res_badge_login.data)

        # Invalid password rejected
        self.logout()
        res_fail = self.login(username=reg_username, password='wrong_password')
        self.assertIn(b'Invalid credentials', res_fail.data)

    def test_04_dashboard_metrics(self):
        """Dashboard must show metrics and KPI cards."""
        self.login()
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'TOTAL VIOLATIONS', res.data)
        self.assertIn(b'PAID REVENUE', res.data)
        self.assertIn(b'PENDING / UNPAID', res.data)
        self.assertIn(b'TODAY\'S LOGS', res.data)

    def test_05_add_violation_validation(self):
        """Add violation should validate inputs."""
        self.login()

        # Missing vehicle number
        res = self.client.post('/violations/add', data={
            'vehicle_number': '',
            'violation_type': 'Overspeeding',
            'location': 'Main Street',
            'violation_date': '2026-09-29T10:00',
            'fine_amount': '1000'
        }, follow_redirects=True)
        self.assertIn(b'Vehicle registration number is mandatory', res.data)

        # Invalid fine amount <= 0
        res = self.client.post('/violations/add', data={
            'vehicle_number': 'TN99ZZ9999',
            'violation_type': 'Overspeeding',
            'location': 'Main Street',
            'violation_date': '2026-09-29T10:00',
            'fine_amount': '-500'
        }, follow_redirects=True)
        self.assertIn(b'Fine amount must be greater than zero', res.data)

    def test_06_add_violation_success_and_qr(self):
        """Add violation creates record, generates QR, sets Unpaid, unique challan."""
        self.login()
        unique_vehicle = "KL07XY9999"
        res = self.client.post('/violations/add', data={
            'vehicle_number': unique_vehicle,
            'violation_type': 'Signal Jump',
            'location': 'Kaloor Junction Signal',
            'violation_date': '2026-09-29T14:30',
            'fine_amount': '1000',
            'notes': 'Captured on camera jumping amber to red'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'created successfully with verified QR code', res.data)
        self.assertIn(b'Digital QR Authenticator', res.data)
        self.assertIn(b'Unpaid', res.data)

        # Verify entry in Supabase
        with self.app.app_context():
            v = Violation.query.filter_by(vehicle_number=unique_vehicle).first()
            self.assertIsNotNone(v)
            self.assertEqual(v.payment_status, 'Unpaid')
            self.assertEqual(v.fine_amount, 1000.0)
            self.assertTrue(v.challan_number.startswith('TVL-'))

            # Verify QR code exists
            qr_path = os.path.join(self.app.config['QR_FOLDER'], v.qr_filename)
            self.assertTrue(os.path.exists(qr_path))

    def test_07_search_and_filtering(self):
        """Search by vehicle and filter by status and violation type."""
        self.login()

        # Vehicle search
        res = self.client.get('/violations?vehicle=tn38ab1234')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'TN38AB1234', res.data)
        self.assertIn(b'Searched Vehicle', res.data)

        # Filter by Unpaid status
        res = self.client.get('/violations?status=Unpaid')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b'>Paid <', res.data)

        # Filter by type
        res = self.client.get('/violations?violation_type=Overspeeding')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Overspeeding', res.data)

    def test_08_payment_update(self):
        """Test marking a violation as Paid."""
        self.login()
        with self.app.app_context():
            unpaid = Violation.query.filter_by(payment_status='Unpaid').first()
            self.assertIsNotNone(unpaid)
            v_id = unpaid.id
            challan_no = unpaid.challan_number

        res = self.client.post(f'/violations/{v_id}/pay', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(f'Challan {challan_no} has been marked as Paid'.encode(), res.data)

        with self.app.app_context():
            updated = db.session.get(Violation, v_id)
            self.assertEqual(updated.payment_status, 'Paid')

    def test_09_digital_challan_and_print_view(self):
        """Test printable digital challan receipt."""
        self.login()
        with self.app.app_context():
            v = Violation.query.first()
            v_id = v.id

        res = self.client.get(f'/challan/{v_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'DEPARTMENT OF TRAFFIC ENFORCEMENT', res.data)
        self.assertIn(b'Print Challan', res.data)
        self.assertIn(b'Scan to Verify or Pay', res.data)

    def test_10_edit_and_delete_violation(self):
        """Test updating violation and deleting violation."""
        self.login()
        with self.app.app_context():
            v = Violation.query.filter_by(vehicle_number='KL07XY9999').first()
            if not v:
                v = Violation.query.first()
            v_id = v.id
            challan_no = v.challan_number

        # Edit
        res = self.client.post(f'/violations/{v_id}/edit', data={
            'vehicle_number': 'KL07XY9999',
            'violation_type': 'Overspeeding',
            'location': 'Marine Drive Promenade',
            'violation_date': '2026-09-29T15:00',
            'fine_amount': '2500',
            'payment_status': 'Unpaid',
            'notes': 'Recalibrated radar check'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'updated successfully', res.data)
        self.assertIn(b'2,500.00', res.data)

        # Delete
        res = self.client.post(f'/violations/{v_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'permanently deleted', res.data)

        with self.app.app_context():
            deleted = db.session.get(Violation, v_id)
            self.assertIsNone(deleted)

    def test_11_invalid_challan_404(self):
        """Non-existent challan should return 404."""
        res = self.client.get('/public/challan/TVL-9999-999999')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'Challan / Record Not Found', res.data)

    def test_12_public_citizen_payment(self):
        """Citizen can pay online through the public portal without login."""
        with self.app.app_context():
            unpaid = Violation.query.filter_by(payment_status='Unpaid').first()
            if not unpaid:
                unpaid = Violation.query.first()
                if unpaid:
                    unpaid.payment_status = 'Unpaid'
                    db.session.commit()
            self.assertIsNotNone(unpaid)
            c_num = unpaid.challan_number

        res = self.client.post(f'/public/challan/{c_num}/pay', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Payment of', res.data)
        self.assertIn(b'Fine Status: Paid', res.data)

if __name__ == '__main__':
    unittest.main()
