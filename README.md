# e-Tender Management System

DBMS Mini Project

A web-based e-Tender Management System that digitizes the tendering workflow between Administrators, Organisations, and Vendors.
Built with Streamlit (for interface and logic) and SQLite (for data storage).

## Features
### 1. Administrator

- Manage Organisations
    - View and delete registered organisations
- Manage Vendors
    - Add, view, or delete vendors
- View System Logs
    - Access bid and tender logs for auditing

### 2. Organisation
- Tenders
     - Create, edit, and delete tenders
     - View tenders (grouped by location or status)

- Bids
    - View and evaluate bids (technical + financial)
    - Award tenders to winning vendors
    - Automatically notify all participants
    - View detailed historical bid logs

- Vendors
    - Add, view, and delete vendors linked to the organisation

### 3. Vendor
- Browse & Filter Tenders
    - Filter by organisation, location, or keywords
    - View tender details and descriptions

- Submit Bids
    - Place bids with technical and financial details
    - Edit or withdraw bids while tender is open

- Track Bids
    - View active and historical bids (shows win/loss result)
    - See associated organisation name and tender status

- Notifications
    - Receive automatic updates on bid submission, tender closure, and results

## Tech Stack
- Frontend & Backend: Streamlit
- Database: SQLite
- Language: Python 3.11+
- Libraries:
    - pandas
    - streamlit
    - sqlite3 (standard library)

## Installation & Usage

1. Clone the repository
```
git clone https://github.com/real-sarah/tender-mgmt.git
cd tender-mgmt
```

2. Create and activate a virtual environment
```
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Run the app
```
streamlit run main.py
```

The database (database.db) is created and initialized automatically on first run.


## Project Structure
```lua
tender-mgmt/
├── main.py
├── setup_db.py
├── requirements.txt
├── dashboards/
│   ├── admin_dashboard.py
│   ├── org_dashboard.py
│   └── vendor_dashboard.py
└── database/
    └── db_utils.py
```

## Team
- Purva Khaire
- Sumati Kulkarni
- Siddharth Shete