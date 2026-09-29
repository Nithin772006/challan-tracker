# 🚦 Smart Traffic Violation Logger

> **Official Digital Traffic Enforcement, E-Challan & QR Verification System**  
> Built strictly adhering to the **3D Organic Modernist Green FinTech Design System** specified in `design.md`.

---

## 📖 Project Overview

**Smart Traffic Violation Logger** is a full-stack Flask web application engineered for municipal traffic police authorities and citizens. It digitizes the recording, auditing, fine calculation, and payment status lifecycle of traffic offenses.

Every recorded violation automatically generates:
1. A strictly unique, standardized e-Challan identifier (`TVL-YYYY-XXXXXX`).
2. An on-demand cryptographic **QR Code** pointing to an unauthenticated public verification and payment ledger.
3. An official printable legal digital challan adhering to Section 133 of the Motor Vehicles Act.

---

## 🎨 Visual Design & Architecture (`design.md`)

The user interface follows the **3D Organic Modernist Green FinTech** specifications defined in [`design.md`](file:///c:/nandu/nithin/Cybernaut-mini-project-3/design.md):
- **Core Color Palette**:
  - Deep Forest (`#0d261c`, `#1b4332`)
  - Emerald (`#2d6a4f`)
  - Spring Mint (`#52b788`)
  - Sage Pale (`#d8f3dc`)
  - Ivory Cream Canvas (`#f4f8f5`)
- **Atmospheric Background**: Multi-point ambient radial gradients with a 32px computational dot-matrix grid overlay.
- **Micro-Elevations**: 18px border radius cards with 16px backdrop blur, subtle green-tinted borders (`rgba(82, 183, 136, 0.24)`), and custom cubic-bezier hover lift animations.
- **Capsule Top Navigation**: 70px fixed top navigation bar with a floating pill menu, officer badge status indicator, and quick actions.
- **KPI Stat Cards**: Top 3px gradient border line (`linear-gradient(90deg, var(--eb-mint), var(--eb-emerald))`) that smoothly illuminates on hover.
- **Print Optimization**: Native print layout that strips navigation and controls to output a clean, official e-Challan document.

---

## ✨ Features

### 👮‍♂️ For Traffic Officers (Protected Terminal)
- **Secure Authentication**: Session-based login with Werkzeug password hashing.
- **Executive Enforcement Dashboard**:
  - Total Violations count.
  - Total Paid revenue cleared (₹).
  - Pending/Unpaid fine amounts requiring recovery (₹).
  - Today's shift violation count.
  - AI Traffic Enforcement summary banner with real-time compliance calculations.
  - Recent violation feed with instant action buttons.
- **Offense Logging (Add Violation)**:
  - Vehicle registration number input with auto-capitalization and whitespace normalization.
  - Violation offense dropdown with automatic standard penalty fine suggestions:
    - *No Helmet* (₹1,000)
    - *Overspeeding* (₹2,000)
    - *Signal Jump* (₹1,000)
    - *No Seat Belt* (₹1,000)
    - *Drunk Driving* (₹10,000)
    - *Wrong Parking* (₹500)
    - *Driving Without License* (₹5,000)
    - *Triple Riding* (₹1,000)
    - *Mobile Phone While Driving* (₹1,500)
    - *Other* (₹1,000)
  - Location, datetime-local picker, and optional officer remarks.
  - Server-side validation preventing malformed or zero-value fines.
  - Automatically initializes as **Unpaid**.
  - Immediate QR code generation and redirection to violation dossier.
- **Violation Registry & History**:
  - Live vehicle registration search (case-insensitive, whitespace-agnostic).
  - Dynamic **Vehicle Summary Strip** displaying total lifetime offenses, paid count, unpaid count, and total penalty sum.
  - Multi-criteria filters: Offense Date, Payment Status (`All`, `Paid`, `Unpaid`), and Violation Type.
  - Integrated CRUD actions: View Details, Edit Offense, Delete (with safety modal dialog), Mark Paid, and Digital Challan.
- **Status Reconciliation**: Single-click "Mark as Paid" action with instant status badge refresh.
- **Official Digital Challan**: Printable legal notice with official emblem, watermark, fine receipt breakdown, and QR verification stamp.

### 🌐 For Citizens & The Public (No Login Required)
- **Instant QR Code Scan Verification**:
  - Scanning the physical or digital QR code navigates to `/public/challan/<challan_number>`.
  - Displays verified status: **PAID** (Emerald Badge) or **UNPAID** (Red Warning Badge).
  - Zero internal officer security details are exposed.
- **Public Online Fine Settlement**: Citizens can click "Pay Fine Online" to simulate immediate clearance and reconciliation.
- **Citizen Search Portal**: Check vehicle or challan outstanding fines at `/public/search`.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.13, Flask 3.0.3, Jinja2 |
| **ORM & Database** | Flask-SQLAlchemy 3.1.1, PostgreSQL (via `psycopg2-binary`) & SQLite fallback |
| **Security** | Werkzeug password hashing, secure session management |
| **QR Engine** | Python `qrcode` 8.2, Pillow 12.3.0 |
| **Frontend** | HTML5 Semantic, Vanilla CSS3 (3D Green FinTech tokens from `design.md`), JavaScript ES6 |
| **Testing** | Python `unittest` test suite |

---

## 📁 Project Structure

```
Cybernaut-mini-project-3/
│
├── app.py                     # Main Flask application factory, routes, and error handlers
├── config.py                  # Environment and database configuration
├── models.py                  # SQLAlchemy models (Officer, Violation)
├── utils.py                   # Challan generation, vehicle plate cleaning, and standard penalties
├── qr_utils.py                # QR code image generator with custom high-contrast color scheme
├── seed.py                    # Database seeding script for sample vehicles and demo officer
├── test_app.py                # Automated test suite (12 test cases verifying all requirements)
├── requirements.txt           # Verified Python package dependencies
├── design.md                  # Design authority specification (single source of truth)
├── README.md                  # Comprehensive technical documentation
├── database.db                # SQLite database instance
│
├── static/
│   ├── css/
│   │   └── style.css          # Design system stylesheet implementing design.md tokens
│   ├── js/
│   │   └── app.js             # Interactive behavior (modals, toasts, auto-fine, plate formatter)
│   └── qr/                    # Generated high-resolution QR code PNGs
│
└── templates/
    ├── base.html              # Base layout with capsule top nav, atmospheric background, toasts
    ├── login.html             # Officer login with glassmorphic card & demo hints
    ├── dashboard.html         # Officer dashboard (4 KPI cards, AI summary, recent table)
    ├── add_violation.html     # Violation recording form with auto fine suggestion
    ├── edit_violation.html    # Violation update form
    ├── violations.html        # Registry history with multi-filter and vehicle summary strip
    ├── violation_detail.html  # Detailed violation view with QR preview & action buttons
    ├── challan.html           # Official printable digital challan receipt
    ├── public_status.html     # Public citizen verification and online payment page
    ├── public_search.html     # Public citizen vehicle fine search portal
    ├── 404.html               # Clean not-found error template
    └── 500.html               # Internal server error template
```

---

## 🚀 Installation & Setup

### 1. Clone or Open Workspace
Ensure your shell is inside the project directory:
```bash
cd Cybernaut-mini-project-3
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL
Set your credentials in `.env` or set `DATABASE_URL`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=traffic_logger
```

Initialize your PostgreSQL database and schema:
```bash
python init_postgres.py
```
*(Note: If PostgreSQL is not yet running on port 5432, the application automatically uses local `database.db` so you can continue developing without disruption.)*

### 5. Seed Database (Optional but Recommended)
Populates demo vehicles (`TN38AB1234`, `TN59CD5678`, `TN37EF9012`, etc.) and generates QR codes:
```bash
python seed.py
```

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 🔑 Officer Authentication & Registration

The application uses real database authentication with **Werkzeug password hashing** and strictly enforces uniqueness on both username and badge number in Supabase.

### 1. Register via Web Interface
Navigate to **`/register`** (or click **"Register"** in the top navigation bar) to register an official account with:
- Officer Full Name
- Official Badge Number (e.g. `TP-9901`)
- Login Username
- Secure Password (min 6 characters)

### 2. Register via Command Line (CLI)
You can also create officers directly via the included administrative CLI script:
```bash
python create_officer.py --username r_sharma --badge TP-8492 --name "Officer R. Sharma" --password "YourStrongPassword123!"
```
Or run interactively:
```bash
python create_officer.py
```

## 🧪 Testing the Application

A complete automated unit test suite is included in [`test_app.py`](file:///c:/nandu/nithin/Cybernaut-mini-project-3/test_app.py):

```bash
python test_app.py
```

### Test Suite Coverage:
1. `test_01_public_access_no_login_needed`: Verifies public portals are accessible without authentication.
2. `test_02_protected_routes_redirect_to_login`: Verifies officer endpoints require authentication.
3. `test_03_login_validation`: Validates credential verification and rejection of bad passwords.
4. `test_04_dashboard_metrics`: Verifies all 4 KPI stat counters and revenue aggregates.
5. `test_05_add_violation_validation`: Validates rejection of empty vehicle numbers and invalid amounts.
6. `test_06_add_violation_success_and_qr`: Verifies record creation, automatic unique challan format, Unpaid status, and QR image generation on disk.
7. `test_07_search_and_filtering`: Tests vehicle search, status filtering, and offense type filtering.
8. `test_08_payment_update`: Tests the Mark as Paid workflow and state update.
9. `test_09_digital_challan_and_print_view`: Verifies printable digital challan receipt structure.
10. `test_10_edit_and_delete_violation`: Verifies editing fields and permanent record deletion.
11. `test_11_invalid_challan_404`: Validates clean 404 error page for non-existent challans.
12. `test_12_public_citizen_payment`: Verifies citizen self-service payment workflow.

---

## 📱 QR Code Verification Workflow

1. An officer logs a violation for vehicle `TN38AB1234` at `/violations/add`.
2. The server assigns an immutable identifier, e.g., `TVL-2026-000002`.
3. The server invokes `generate_qr_code()` which writes `static/qr/TVL-2026-000002.png` embedding the direct URL:
   `http://<host>:<port>/public/challan/TVL-2026-000002`
4. The QR image renders directly on the officer's dashboard, detail view, and printable challan.
5. When a citizen scans the QR with any standard mobile camera:
   - They are routed to `/public/challan/TVL-2026-000002`.
   - No login prompt appears.
   - The verified status (PAID or UNPAID) displays prominently.
   - If unpaid, the citizen can click "Pay Fine Online" to immediately settle the fine.

---

## 📄 License & Academic Attribution
Developed as a high-fidelity academic mini project adhering to production engineering and clean architectural standards.
