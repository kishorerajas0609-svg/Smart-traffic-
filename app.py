import os
import csv
import io
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, abort, Response, send_file
)
from dotenv import load_dotenv
import qrcode
from models import db, Violation

load_dotenv()

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'smart-traffic-violation-logger-secure-key-2026')
db_path = os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
os.makedirs(os.path.join(basedir, 'static', 'qr_codes'), exist_ok=True)

db.init_app(app)

OFFICER_USERNAME = os.getenv('OFFICER_USERNAME', 'rajesh')
OFFICER_NAME = os.getenv('OFFICER_NAME', 'Inspector Rajesh Kumar')
OFFICER_PASSWORD = os.getenv('OFFICER_PASSWORD', 'traffic123')

VIOLATION_TYPES = [
    'No Helmet',
    'Overspeeding',
    'Signal Violation',
    'Drunk Driving',
    'No Seat Belt',
    'Wrong Parking',
    'Driving Without License',
    'Triple Riding',
    'Using Mobile Phone while Driving',
    'Dangerous Driving',
    'Other'
]


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def generate_qr_code(violation_id, base_url=None):
    qr_filename = f'challan_{violation_id}.png'
    qr_dir = os.path.join(basedir, 'static', 'qr_codes')
    qr_path = os.path.join(qr_dir, qr_filename)

    if not os.path.exists(qr_path):
        if base_url:
            target_url = f"{base_url.rstrip('/')}/public/violation/{violation_id}"
        else:
            target_url = f"/public/violation/{violation_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        img.save(qr_path)

    return f'qr_codes/{qr_filename}'


@app.context_processor
def inject_global_vars():
    return {
        'current_year': datetime.utcnow().year,
        'violation_types_list': VIOLATION_TYPES,
        'officer_display_name': session.get('officer_name', OFFICER_NAME)
    }



@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        valid_usernames = [OFFICER_USERNAME.lower(), 'officer', 'rajesh', 'inspector rajesh kumar']
        
        if username.lower() in valid_usernames and password == OFFICER_PASSWORD:
            session['logged_in'] = True
            session['officer_username'] = username
            session['officer_name'] = OFFICER_NAME
            flash(f'Welcome back, {OFFICER_NAME}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html', default_user=OFFICER_USERNAME)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_violations = Violation.query.count()
    paid_violations = Violation.query.filter_by(payment_status='Paid').count()
    unpaid_violations = Violation.query.filter_by(payment_status='Unpaid').count()
    
    total_fine_amount = db.session.query(db.func.sum(Violation.fine_amount)).scalar() or 0.0
    total_collected_amount = db.session.query(db.func.sum(Violation.fine_amount)).filter_by(payment_status='Paid').scalar() or 0.0
    pending_amount = total_fine_amount - total_collected_amount

    recent_violations = Violation.query.order_by(Violation.id.desc()).limit(8).all()

    return render_template(
        'dashboard.html',
        total_violations=total_violations,
        paid_violations=paid_violations,
        unpaid_violations=unpaid_violations,
        total_fine_amount=total_fine_amount,
        total_collected_amount=total_collected_amount,
        pending_amount=pending_amount,
        recent_violations=recent_violations,
        officer_name=session.get('officer_name', OFFICER_NAME)
    )


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_violation():
    if request.method == 'POST':
        raw_vehicle = request.form.get('vehicle_number', '')
        vehicle_number = ''.join(raw_vehicle.upper().split())
        violation_type = request.form.get('violation_type', '').strip()
        location = request.form.get('location', '').strip()
        date_str = request.form.get('violation_date', '').strip()
        fine_amount_str = request.form.get('fine_amount', '').strip()

        errors = []
        if not vehicle_number:
            errors.append('Vehicle Number is required.')
        elif len(vehicle_number) < 4 or len(vehicle_number) > 20:
            errors.append('Vehicle Number must be between 4 and 20 characters.')

        if not violation_type:
            errors.append('Violation Type is required.')

        if not location:
            errors.append('Location is required.')

        violation_date = None
        if not date_str:
            errors.append('Violation Date is required.')
        else:
            try:
                violation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid date format. Expected YYYY-MM-DD.')

        fine_amount = None
        if not fine_amount_str:
            errors.append('Fine Amount is required.')
        else:
            try:
                fine_amount = float(fine_amount_str)
                if fine_amount < 0:
                    errors.append('Fine Amount must be a non-negative number.')
            except ValueError:
                errors.append('Fine Amount must be a valid number.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'add_violation.html',
                form_data=request.form,
                violation_types=VIOLATION_TYPES,
                today_date=date.today().strftime('%Y-%m-%d')
            )

        new_violation = Violation(
            vehicle_number=vehicle_number,
            violation_type=violation_type,
            location=location,
            violation_date=violation_date,
            fine_amount=fine_amount,
            payment_status='Unpaid'
        )

        db.session.add(new_violation)
        db.session.commit()

        base_url = request.host_url
        generate_qr_code(new_violation.id, base_url)

        flash(f'Violation recorded successfully! Challan #{new_violation.id} generated.', 'success')
        return redirect(url_for('view_challan', id=new_violation.id))

    return render_template(
        'add_violation.html',
        violation_types=VIOLATION_TYPES,
        today_date=date.today().strftime('%Y-%m-%d'),
        form_data={}
    )


def build_filtered_query(args):
    raw_vehicle = args.get('vehicle_number', '')
    vehicle_query = ''.join(raw_vehicle.upper().split())
    type_query = args.get('violation_type', '').strip()
    date_query = args.get('violation_date', '').strip()
    status_query = args.get('payment_status', '').strip()

    query = Violation.query

    if vehicle_query:
        query = query.filter(Violation.vehicle_number.ilike(f'%{vehicle_query}%'))

    if type_query:
        query = query.filter(Violation.violation_type == type_query)

    if date_query:
        try:
            parsed_date = datetime.strptime(date_query, '%Y-%m-%d').date()
            query = query.filter(Violation.violation_date == parsed_date)
        except ValueError:
            pass

    if status_query in ['Paid', 'Unpaid']:
        query = query.filter(Violation.payment_status == status_query)

    return query, vehicle_query, type_query, date_query, status_query


@app.route('/violations')
@login_required
def violations_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    
    query, vehicle_query, type_query, date_query, status_query = build_filtered_query(request.args)

    total_matching = query.count()
    pagination = query.order_by(Violation.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    violations = pagination.items

    return render_template(
        'violations.html',
        violations=violations,
        pagination=pagination,
        total_matching=total_matching,
        vehicle_query=vehicle_query,
        type_query=type_query,
        date_query=date_query,
        status_query=status_query,
        violation_types=VIOLATION_TYPES
    )


@app.route('/violations/export')
@login_required
def export_violations_csv():
    """Exports matching violation records as a downloadable CSV file."""
    query, _, _, _, _ = build_filtered_query(request.args)
    records = query.order_by(Violation.id.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Challan ID', 'Vehicle Number', 'Violation Type', 'Location',
        'Violation Date', 'Fine Amount (INR)', 'Payment Status', 'Recorded Timestamp'
    ])

    for r in records:
        writer.writerow([
            r.id,
            r.vehicle_number,
            r.violation_type,
            r.location,
            r.violation_date.strftime('%Y-%m-%d'),
            f'{r.fine_amount:.2f}',
            r.payment_status,
            r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
        ])

    output.seek(0)
    filename = f"traffic_violations_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@app.route('/rules')
@login_required
def traffic_rules():
    rules_data = [
        {
            'section': 'Section 129 / 177',
            'offense': 'Driving Two-Wheeler Without Helmet',
            'fine': 1000.00,
            'penalty_type': 'Compounding / Non-Cognizable',
            'action': 'Compounding fine levied; Warning of 3-month license disqualification for repeat offenders.',
            'category': 'Protective Equipment'
        },
        {
            'section': 'Section 194B',
            'offense': 'Driving Four-Wheeler Without Seat Belt',
            'fine': 1000.00,
            'penalty_type': 'Compounding Fine',
            'action': 'Mandatory for all occupants in moving motor vehicles.',
            'category': 'Protective Equipment'
        },
        {
            'section': 'Section 112 / 183',
            'offense': 'Overspeeding Above Statutory Highway Limit',
            'fine': 2000.00,
            'penalty_type': 'Speed Radar / ANPR Capture',
            'action': 'Light motor vehicle: ₹1,000–₹2,000; Medium/Heavy motor vehicle: ₹2,000–₹4,000 + second offense license seizure.',
            'category': 'Speed Violations'
        },
        {
            'section': 'Section 184 / 177',
            'offense': 'Red Light Signal Jumping / Dangerous Lane Change',
            'fine': 1500.00,
            'penalty_type': 'Automated RLVD Camera',
            'action': 'Digital photo evidence registered with direct e-challan notice generation.',
            'category': 'Signal & Traffic Control'
        },
        {
            'section': 'Section 185',
            'offense': 'Driving Under Influence of Alcohol / Drugs (BAC > 30mg/100ml)',
            'fine': 10000.00,
            'penalty_type': 'Non-Compoundable / Court Cognizable',
            'action': 'Breathalyzer test mandatory; Vehicle impounded; Court appearance required; Up to 6 months imprisonment.',
            'category': 'Severe Safety Threat'
        },
        {
            'section': 'Section 181',
            'offense': 'Driving Vehicle Without Valid Driving License',
            'fine': 5000.00,
            'penalty_type': 'Compounding Fine + Vehicle Custody',
            'action': 'Vehicle immobilized until valid licensed operator presents credentials.',
            'category': 'Authorization & Licensing'
        },
        {
            'section': 'Section 177 / 122',
            'offense': 'Wrong / Obstuctive Parking in No-Parking Zone',
            'fine': 500.00,
            'penalty_type': 'Wheel-Clamping & Towing Fine',
            'action': 'Towing charges ₹500–₹1,000 levied additionally by municipal authority.',
            'category': 'Parking & Obstruction'
        },
        {
            'section': 'Section 184(c)',
            'offense': 'Using Handheld Mobile Phone While Driving',
            'fine': 1500.00,
            'penalty_type': 'Compounding Fine',
            'action': 'Applies to calling, texting, or hand-holding navigational devices while vehicle in motion.',
            'category': 'Distracted Driving'
        },
        {
            'section': 'Section 128',
            'offense': 'Triple Riding on Two-Wheeler',
            'fine': 1000.00,
            'penalty_type': 'Compounding Fine',
            'action': 'Only one pillion rider permitted on registered two-wheeled motor vehicles.',
            'category': 'Overloading & Capacity'
        }
    ]
    return render_template('rules.html', rules=rules_data)


@app.route('/analytics')
@login_required
def enforcement_analytics():
    total_violations = Violation.query.count()
    paid_violations = Violation.query.filter_by(payment_status='Paid').count()
    unpaid_violations = Violation.query.filter_by(payment_status='Unpaid').count()
    
    total_fine_amount = db.session.query(db.func.sum(Violation.fine_amount)).scalar() or 0.0
    total_collected_amount = db.session.query(db.func.sum(Violation.fine_amount)).filter_by(payment_status='Paid').scalar() or 0.0
    
    recovery_rate = (paid_violations / total_violations * 100) if total_violations > 0 else 0.0

    offense_stats = db.session.query(
        Violation.violation_type,
        db.func.count(Violation.id).label('count'),
        db.func.sum(Violation.fine_amount).label('total_fine')
    ).group_by(Violation.violation_type).order_by(db.desc('count')).all()

    hotspot_stats = db.session.query(
        Violation.location,
        db.func.count(Violation.id).label('count'),
        db.func.sum(Violation.fine_amount).label('total_fine')
    ).group_by(Violation.location).order_by(db.desc('count')).limit(10).all()

    return render_template(
        'analytics.html',
        total_violations=total_violations,
        paid_violations=paid_violations,
        unpaid_violations=unpaid_violations,
        total_fine_amount=total_fine_amount,
        total_collected_amount=total_collected_amount,
        recovery_rate=recovery_rate,
        offense_stats=offense_stats,
        hotspot_stats=hotspot_stats
    )


@app.route('/violation/<int:id>')
@login_required
def violation_detail(id):
    violation = db.get_or_404(Violation, id)
    
    generate_qr_code(violation.id, request.host_url)
    return render_template('violation_detail.html', violation=violation)


@app.route('/violation/<int:id>/challan')
@login_required
def view_challan(id):
    violation = db.get_or_404(Violation, id)
    
    generate_qr_code(violation.id, request.host_url)
    qr_filename = f'qr_codes/challan_{violation.id}.png'
    return render_template('challan.html', violation=violation, qr_filename=qr_filename)


@app.route('/violation/<int:id>/pay', methods=['POST'])
@login_required
def update_payment_status(id):
    violation = db.get_or_404(Violation, id)
    new_status = request.form.get('payment_status', 'Paid')
    
    if new_status in ['Paid', 'Unpaid']:
        violation.payment_status = new_status
        db.session.commit()
        flash(f'Payment status for Challan #{violation.id} updated to {new_status.upper()}.', 'success')
    else:
        flash('Invalid payment status provided.', 'danger')

    next_url = request.form.get('next') or request.referrer or url_for('view_challan', id=violation.id)
    return redirect(next_url)


@app.route('/violation/<int:id>/delete', methods=['POST'])
@login_required
def delete_violation(id):
    violation = db.get_or_404(Violation, id)
    
    qr_file = os.path.join(basedir, 'static', 'qr_codes', f'challan_{violation.id}.png')
    if os.path.exists(qr_file):
        try:
            os.remove(qr_file)
        except OSError:
            pass

    db.session.delete(violation)
    db.session.commit()
    flash(f'Challan #{id} has been permanently deleted.', 'info')
    return redirect(url_for('violations_list'))


@app.route('/public/violation/<int:id>')
def public_violation_status(id):
    """Public status page accessible without login by scanning the QR code."""
    violation = db.get_or_404(Violation, id)
    return render_template('public_status.html', violation=violation)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('404.html', error_title="500 - Internal Server Error", error_message="An unexpected server error occurred."), 500


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
