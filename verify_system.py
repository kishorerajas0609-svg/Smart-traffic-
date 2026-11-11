import os
import csv
import io
from datetime import date
from app import app, db, Violation, generate_qr_code

def run_verification():
    print('======================================================')
    print(' SMART TRAFFIC VIOLATION LOGGER - SYSTEM VERIFICATION ')
    print('======================================================\n')
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
    
    client = app.test_client()
    
    print('[TEST 1] Testing Officer Authentication...')
    bad_login = client.post('/login', data={'username': 'wrong', 'password': 'bad'}, follow_redirects=True)
    assert b'Invalid username or password' in bad_login.data, 'Bad login must show error'
    
    good_login = client.post('/login', data={'username': 'officer', 'password': 'traffic123'}, follow_redirects=True)
    assert b'Officer Dashboard' in good_login.data, 'Valid login must reach dashboard'
    assert b'Total Violations' in good_login.data, 'Dashboard must render stats'
    print('  --> SUCCESS: Officer Login & Session working.\n')

    print('[TEST 2] Testing Add Violation & Dynamic QR Code Generation...')
    test_veh = 'TEST99ZZ7777'
    add_post = client.post('/add', data={
        'vehicle_number': test_veh,
        'violation_type': 'No Helmet',
        'location': 'Anna Salai, Chennai',
        'violation_date': str(date.today()),
        'fine_amount': '1000'
    }, follow_redirects=True)
    
    assert b'Violation recorded successfully' in add_post.data
    assert test_veh.encode() in add_post.data
    assert b'UNPAID' in add_post.data
    
    with app.app_context():
        v = Violation.query.filter_by(vehicle_number=test_veh).first()
        assert v is not None
        v_id = v.id
        qr_path = os.path.join(app.static_folder, 'qr_codes', f'challan_{v_id}.png')
        assert os.path.exists(qr_path)
        print(f'  --> SUCCESS: Violation #{v_id} created & QR image generated at {qr_path}.\n')

    print('[TEST 3] Testing Search by Vehicle Number...')
    search_res = client.get(f'/violations?vehicle_number={test_veh}')
    assert search_res.status_code == 200
    assert test_veh.encode() in search_res.data
    print('  --> SUCCESS: Search query retrieved matching record.\n')

    print('[TEST 4] Testing Filter Functionality & 100+ Dataset Pagination...')
    with app.app_context():
        total_in_db = Violation.query.count()
        assert total_in_db >= 100, f'Expected > 100 records in DB, found {total_in_db}'
        print(f'  --> Verified database contains {total_in_db} records (>100).')

    page1_res = client.get('/violations?page=1&per_page=15')
    assert page1_res.status_code == 200
    assert b'Showing page 1 of' in page1_res.data
    
    page2_res = client.get('/violations?page=2&per_page=15')
    assert page2_res.status_code == 200
    assert b'Showing page 2 of' in page2_res.data
    print('  --> SUCCESS: Multi-page pagination working over 100+ records callset.\n')

    print('[TEST 5] Testing CSV Export Route (/violations/export)...')
    csv_res = client.get('/violations/export?payment_status=Unpaid')
    assert csv_res.status_code == 200
    assert csv_res.mimetype == 'text/csv'
    csv_content = csv_res.data.decode('utf-8')
    assert 'Challan ID,Vehicle Number,Violation Type,Location' in csv_content
    lines = [line for line in csv_content.splitlines() if line.strip()]
    assert len(lines) > 10
    print(f'  --> SUCCESS: CSV export generated valid dataset with {len(lines)-1} exported records.\n')

    print('[TEST 6] Testing New Navigation Categories (/rules & /analytics)...')
    rules_res = client.get('/rules')
    assert rules_res.status_code == 200
    assert b'Traffic Rules & Penalties Directory' in rules_res.data
    assert b'Section 129' in rules_res.data
    print('  --> SUCCESS: Category 1 (Traffic Rules & Statutory Tariff Directory) working.')

    analytics_res = client.get('/analytics')
    assert analytics_res.status_code == 200
    assert b'Enforcement Analytics & Zone Hotspots' in analytics_res.data
    assert b'Recovery Efficiency' in analytics_res.data
    print('  --> SUCCESS: Category 2 (Enforcement Analytics & Zone Hotspots) working.\n')

    print('[TEST 7] Testing Payment Status Update (Unpaid -> Paid)...')
    pay_res = client.post(f'/violation/{v_id}/pay', data={'payment_status': 'Paid'}, follow_redirects=True)
    assert pay_res.status_code == 200
    assert b'PAID' in pay_res.data
    
    with app.app_context():
        v_updated = db.session.get(Violation, v_id)
        assert v_updated.payment_status == 'Paid'
    print(f'  --> SUCCESS: Challan #{v_id} status transitioned to PAID.\n')

    print('[TEST 8] Testing Public QR Status Page...')
    public_client = app.test_client()
    public_res = public_client.get(f'/public/violation/{v_id}')
    assert public_res.status_code == 200
    assert b'CHALLAN SETTLED / PAID' in public_res.data
    assert test_veh.encode() in public_res.data
    assert b'Mark as PAID' not in public_res.data
    print('  --> SUCCESS: Unauthenticated public citizen status page verified.\n')

    print('[TEST 9] Testing 404 Error Handling...')
    not_found_res = client.get('/public/violation/999999')
    assert not_found_res.status_code == 404
    assert b'404' in not_found_res.data
    print('  --> SUCCESS: Custom 404 handler verified.\n')

    print('[TEST 10] Testing Deletion & Cleanup...')
    del_res = client.post(f'/violation/{v_id}/delete', follow_redirects=True)
    assert del_res.status_code == 200
    with app.app_context():
        deleted_v = db.session.get(Violation, v_id)
        assert deleted_v is None
        assert not os.path.exists(qr_path)
    print(f'  --> SUCCESS: Challan #{v_id} removed cleanly.\n')

    print('======================================================')
    print(' ALL 10 VERIFICATION CHECKS PASSED SUCCESSFULLY (100%)')
    print('======================================================')

if __name__ == '__main__':
    run_verification()
