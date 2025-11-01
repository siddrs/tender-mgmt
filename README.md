# tender-mgmt
Databases Project - Course Work

A simple e-Tender Management System built using **Streamlit** and **SQLite** as part of the DBMS course.  
It allows administrators to manage tenders and vendors, while vendors can browse tenders, submit bids, and receive updates in real time.

## Tech Used:
1. Streamlit (frontend + backend)
2. SQLite (DBMS)

## Features:

### Admin:
1. Manage Tenders:
   - view all tenders — filter by location, status  
   - add new tender  
   - edit or delete open tenders  
2. Manage Vendors:
   - view all vendors  
   - add new vendor  
   - delete vendor  
3. Manage Bids:
   - view and evaluate bids (technical & financial)  
   - award tenders to winners  
   - view bid logs and history  
   - automatic notifications to vendors  

### Vendor:
1. Tenders:
   - View and filter open tenders by location or keyword  
   - View detailed tender information  
2. Bidding:
   - Submit new bids with technical and financial specifications  
   - Edit or withdraw bids while tender is open  
   - View submitted and historical bids  
3. Notifications:
   - Receive automated notifications on bid submission, updates, and tender results  

<hr>

### How to Run
1. Clone the repository  
   ```bash
   git clone https://github.com/real-sarah/tender-mgmt.git
   cd tender-mgmt
   ```
2. Create and activate a virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app
   ```bash
   streamlit run main.py
   ```
Database setup happens automatically on first run (tendermanagement.db).

<hr>

### Project Structure
```lua
tender-mgmt/
├── main.py
├── setup_db.py
├── requirements.txt
├── dashboards/
│   ├── admin_dashboard.py
│   └── vendor_dashboard.py
└── database/
    └── db_utils.py
```

<hr>

### Team
- Purva Khaire
- Sumati Kulkarni
- Siddharth Shete