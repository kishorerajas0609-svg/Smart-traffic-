import os
import csv
from datetime import datetime
from app import app, db, Violation, generate_qr_code

def seed_from_csv(csv_path=None, reset=True):
    if csv_path is None:
        csv_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'traffic_violations.csv')

    if not os.path.exists(csv_path):
        print(f'Error: CSV file not found at {csv_path}')
        return

    with app.app_context():
        if reset:
            db.drop_all()
            db.create_all()
            print('Cleared existing SQLite database tables.')

        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                v_date = datetime.strptime(row['violation_date'], '%Y-%m-%d').date()
                created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S') if 'created_at' in row and row['created_at'] else datetime.utcnow()
                
                v = Violation(
                    vehicle_number=row['vehicle_number'].strip().upper(),
                    violation_type=row['violation_type'].strip(),
                    location=row['location'].strip(),
                    violation_date=v_date,
                    fine_amount=float(row['fine_amount']),
                    payment_status=row['payment_status'].strip(),
                    created_at=created_at
                )
                records.append(v)

        db.session.bulk_save_objects(records)
        db.session.commit()
        
        total_count = Violation.query.count()
        print(f'Successfully imported and seeded {total_count} violation records from {csv_path}!')

        initial_violations = Violation.query.limit(30).all()
        for v in initial_violations:
            generate_qr_code(v.id, 'http://127.0.0.1:5000')
        print(f'Generated QR codes for {len(initial_violations)} sample challans (remaining are generated on-demand).')

if __name__ == '__main__':
    seed_from_csv(reset=True)
