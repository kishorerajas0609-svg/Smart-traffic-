import os
import unittest
from datetime import date
from app import app, db, Violation, generate_qr_code

class SmartTrafficViolationLoggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.app_context():
            db.create_all()

    def setUp(self):
        self.client = app.test_client()

    def login(self, username='officer', password='traffic123'):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_1_login_flow(self):
        print('\n--- TEST 1: Login Flow ---')
        
        res = self.login('wrong', 'creds')
        self.assertIn(b'Invalid username or password', res.data)
        print('[PASS] Invalid login rejected successfully')

        res = self.login('officer', 'traffic123')
        self.assertIn(b'Officer Dashboard', res.data)
        self.assertIn(b'Total Violations', res.data)
        print('[PASS] Valid officer authentication successful')

    def test_2_add_violation_and_qr_generation(self):
        print('\n--- TEST 2: Add Violation & QR Generation ---')
        self.login()

        bad_res = self.client.post('/add', data={
            'vehicle_number': '',
            'violation_type': '',
            'location': '',
            'violation_date': '',
            'fine_amount': ''
        }, follow_redirects=True)
        self.assertIn(b'Vehicle Number is required', bad_res.data)
        print('[PASS] Empty form validation rejected correctly')

        res = self.client.post('/add', data={
            'vehicle_number': 'tn 01 ab 1234', 
            'violation_type': 'No Helmet',
            'location': 'Chennai Central',
            'violation_date': str(date.today()),
            'fine_amount': '1000'
        }, follow_redirects=True)

        self.assertIn(b'Violation recorded successfully', res.data)
        self.assertIn(b'TN01AB1234', res.data)
        self.assertIn(b'UNPAID', res.data)
        print('[PASS] Violation created with normalized vehicle number TN01AB1234')

        with app.app_context():
            v = Violation.query.filter_by(vehicle_number='TN01AB1234').first()
            self.assertIsNotNone(v)
            self.assertEqual(v.payment_status, 'Unpaid')
            self.assertEqual(v.fine_amount, 1000.0)
            
            qr_file = os.path.join(app.static_folder, 'qr_codes', f'challan_{v.id}.png')
            self.assertTrue(os.path.exists(qr_file))
            print(f'[PASS] Dynamic QR code generated on disk: {qr_file}')

    def test_3_search_functionality(self):
        print('\n--- TEST 3: Search Functionality ---')
        self.login()
        res = self.client.get('/violations?vehicle_number=TN01AB1234')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'TN01AB1234', res.data)
        self.assertIn(b'No Helmet', res.data)
        print('[PASS] Search by vehicle number retrieved matching record')

    def test_4_filter_functionality(self):
        print('\n--- TEST 4: Filter Functionality ---')
        self.login()
        res = self.client.get('/violations?payment_status=Unpaid')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'TN01AB1234', res.data)

        res_paid = self.client.get('/violations?vehicle_number=TN01AB1234&payment_status=Paid')
        self.assertNotIn(b'No Helmet', res_paid.data)
        print('[PASS] Status and multi-criteria filters verified')

    def test_5_payment_status_update(self):
        print('\n--- TEST 5: Payment Status Update ---')
        self.login()
        with app.app_context():
            v = Violation.query.filter_by(vehicle_number='TN01AB1234').first()
            self.assertIsNotNone(v, "Violation should exist from test_2")
            v_id = v.id

        res = self.client.post(f'/violation/{v_id}/pay', data={'payment_status': 'Paid'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with app.app_context():
            v_updated = Violation.query.get(v_id)
            self.assertEqual(v_updated.payment_status, 'Paid')
            print(f'[PASS] Challan #{v_id} status updated to PAID in SQLite database')

    def test_6_public_qr_status_page_unauthenticated(self):
        print('\n--- TEST 6: Public QR Status Page (No Login Required) ---')
        self.logout()
        unauth_client = app.test_client()

        with app.app_context():
            v = Violation.query.filter_by(vehicle_number='TN01AB1234').first()
            self.assertIsNotNone(v, "Violation should exist")
            v_id = v.id

        res = unauth_client.get(f'/public/violation/{v_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'CHALLAN SETTLED / PAID', res.data)
        self.assertIn(b'TN01AB1234', res.data)
        self.assertIn(b'No Helmet', res.data)
        self.assertNotIn(b'Mark as PAID', res.data)
        self.assertNotIn(b'Delete Record', res.data)
        print('[PASS] Public verification portal accessible without login, showing correct status & no admin controls')

    def test_7_invalid_violation_id_404(self):
        print('\n--- TEST 7: 404 Handling ---')
        res = self.client.get('/public/violation/999999')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'404', res.data)
        print('[PASS] Non-existent violation ID returns custom 404 page')

    def test_8_delete_operation(self):
        print('\n--- TEST 8: Delete Operation ---')
        self.login()
        with app.app_context():
            v = Violation.query.filter_by(vehicle_number='TN01AB1234').first()
            self.assertIsNotNone(v)
            v_id = v.id

        res = self.client.post(f'/violation/{v_id}/delete', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with app.app_context():
            deleted_v = Violation.query.get(v_id)
            self.assertIsNone(deleted_v)
            print(f'[PASS] Challan #{v_id} permanently deleted from database')

if __name__ == '__main__':
    unittest.main()
