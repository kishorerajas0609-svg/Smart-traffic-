# Smart Traffic Violation Logger

A complete, production-style Flask web application designed for traffic police and authorized enforcement officers to digitally record, manage, search, filter, export, and update traffic violation challan records, with dynamic QR code generation for citizen verification.

Includes an out-of-the-box **150+ record realistic CSV dataset** across multiple Indian states and cities with full pagination and CSV export functionality.

---

## Key Features

1. **150+ Realistic Dataset & CSV Support**: Pre-packaged with 	raffic_violations.csv containing 150 diverse violation records.
2. **Server-Side Pagination**: Clean Bootstrap pagination (15 records per page) with full query parameter persistence across pages.
3. **Instant CSV Export**: One-click download (/violations/export) to export the entire dataset or filtered search views directly as a .csv file.
4. **Secure Officer Authentication**: Session-based login system for authorized traffic officers.
5. **Real-time Analytics Dashboard**: Live metrics for Total Violations, Paid vs Unpaid counts, Total Fine Amount, Collected Revenue, and Pending Collections.
6. **Challan Issuance & Validation**: Record offenses with vehicle number normalization, input sanitization, non-negative penalty amounts, and automatic initial "Unpaid" status.
7. **Dynamic QR Code Generation**: Automatically creates a unique QR code for every challan using the qrcode library, stored in static/qr_codes/.
8. **Printable Digital E-Challan**: Official receipt format with embedded QR code, police seal stamp, and dedicated @media print styling for receipt printing.
9. **Multi-Parameter Search & Filtering**: Case-insensitive partial search by vehicle number combined with violation type, date, and payment status filters executed directly against SQLite via SQLAlchemy.
10. **Payment Status Lifecycle**: Easy one-click transition from Unpaid to Paid with instant database persistence and audit trail.
11. **Public-Facing Verification Portal**: Secure, standalone status page (/public/violation/<id>) accessible by citizens without login to verify validity and payment status.
12. **Responsive Bootstrap 5 UI**: Clean, mobile-friendly interface styled with Bootstrap 5 and Bootstrap Icons.

---

## Technology Stack

- **Backend**: Python 3, Flask 3.x, Flask-SQLAlchemy, SQLite
- **QR Engine**: qrcode, Pillow
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Vanilla JavaScript
- **Dataset**: CSV (	raffic_violations.csv)
- **Configuration**: python-dotenv

---

## Project Structure

`
smart_traffic_violation_logger/
│
├── app.py                      # Main application entry point, routes & business logic
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
├── .env.example                # Example environment variables
├── traffic_violations.csv      # 150+ Record Traffic Offenses Dataset
├── seed.py                     # CSV dataset importer & database seeder
├── verify_system.py            # Automated 9-step end-to-end test suite
│
├── models/
│   ├── __init__.py
│   └── violation.py            # SQLAlchemy database model
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom styles, print stylesheet & badge themes
│   ├── js/
│   │   └── script.js           # UI utilities & print handlers
│   └── qr_codes/               # Directory for dynamically generated QR PNGs
│
├── templates/
│   ├── base.html               # Base layout with navbar & flash alerts
│   ├── login.html              # Officer authentication page
│   ├── dashboard.html          # Stats dashboard & recent offenses
│   ├── add_violation.html      # Offense recording form
│   ├── violations.html         # History table with pagination, search, filters & export
│   ├── violation_detail.html   # Detailed violation view & status update
│   ├── challan.html            # Printable digital challan receipt with QR
│   ├── public_status.html      # Public citizen verification page (no login required)
│   └── 404.html                # Error page
│
└── instance/
    └── database.db             # SQLite database file (auto-generated)
`

---

## Installation & Setup

### 1. Navigate to the Project Directory
`powershell
cd C:\Users\Deepika\.gemini\antigravity\scratch\smart_traffic_violation_logger
`

### 2. Create and Activate Virtual Environment (Optional)
`powershell
python -m venv venv
venv\Scripts\activate
`

### 3. Install Dependencies
`powershell
pip install -r requirements.txt
`

### 4. Seed Database with 150+ CSV Records
To populate the SQLite database directly from 	raffic_violations.csv:
`powershell
python seed.py
`

### 5. Run the Application
`powershell
python app.py
`

Open your browser and navigate to:
`
http://127.0.0.1:5000/
`

---

## Default Officer Login Credentials

| Field | Value |
|---|---|
| **Username** | officer |
| **Password** | 	raffic123 |

*(Configurable via OFFICER_USERNAME and OFFICER_PASSWORD environment variables)*

---

## CSV Dataset Schema (	raffic_violations.csv)

| Column Name | Data Type | Example |
|---|---|---|
| id | Integer | 1 |
| ehicle_number | String | HR26AZ5507 |
| iolation_type | String | Drunk Driving |
| location | String | Cyber City, Gurugram |
| iolation_date | Date (YYYY-MM-DD) | 2026-08-26 |
| ine_amount | Float | 10000.0 |
| payment_status | String | Paid / Unpaid |
| created_at | DateTime | 2026-08-26 10:43:00 |

---

## Main Routes & Endpoints

| Route | Method | Access | Description |
|---|---|---|---|
| / | GET | Public | Redirects to Dashboard (if logged in) or Login |
| /login | GET, POST | Public | Officer login portal |
| /logout | GET | Officer | Clears officer session |
| /dashboard | GET | Officer | Key metrics, revenue totals, recent violations |
| /add | GET, POST | Officer | Record new violation, validate, generate QR |
| /violations | GET | Officer | Multi-page paginated violation history with live search & filters |
| /violations/export | GET | Officer | Export matching violation records as downloadable .csv |
| /violation/<id> | GET | Officer | Individual violation view & status update |
| /violation/<id>/challan | GET | Officer | Printable digital challan receipt with QR |
| /violation/<id>/pay | POST | Officer | Mark violation as Paid / Unpaid |
| /violation/<id>/delete | POST | Officer | Delete violation & cleanup QR image |
| /public/violation/<id> | GET | Public | Citizen verification page (No login needed) |
