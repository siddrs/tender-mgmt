import sqlite3


# should ideally run once after main function is called
# if you're doing some changes to the schema (not recommended) then try NOT to use ALTER.
# instead replace the .db file with another one, and old schema with new one (yes, the new file will be empty and not have the previous entries)

def setup_database():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Vendors table
    cur.execute("""
            CREATE TABLE IF NOT EXISTS Vendor (
                vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                password TEXT NOT NULL
            )
        """)

    cur.execute("""
                CREATE TABLE IF NOT EXISTS Organisation (
                    org_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT,
                    address TEXT,
                    password TEXT NOT NULL
                )
            """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Tender ( 
        tender_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tender_ref_no TEXT UNIQUE, 
        org_id INTEGER NOT NULL,
        title TEXT NOT NULL, 
        description TEXT, 
        location TEXT, 
        status TEXT CHECK(status IN ('Open','Closed','Awarded')) DEFAULT 'Open', 
        opening_date DATE, 
        closing_date DATE, 
        publishing_date DATE,
        winner_vendor_id INTEGER,
        FOREIGN KEY (org_id) REFERENCES Organisation(org_id) ON DELETE CASCADE,
        FOREIGN KEY (winner_vendor_id) REFERENCES Vendor(vendor_id) ON DELETE SET NULL ON UPDATE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Bid (
        vendor_id INTEGER NOT NULL,
        tender_id INTEGER NOT NULL,
        submission_date DATE,
        technical_spec TEXT,
        financial_spec TEXT,
        status TEXT CHECK(status IN ('Submitted','Under Review','Accepted','Rejected','Withdrawn')) DEFAULT 'Submitted',
        opened_at DATETIME,
        technical_score REAL,
        financial_score REAL,
        final_score REAL,
        remarks TEXT,
        PRIMARY KEY (vendor_id, tender_id),
        FOREIGN KEY (vendor_id) REFERENCES Vendor(vendor_id) 
            ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (tender_id) REFERENCES Tender(tender_id) 
            ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)

    cur.execute(""" 
    CREATE TABLE IF NOT EXISTS BidLog (
        vendor_id INTEGER NOT NULL,
        tender_id INTEGER NOT NULL,
        submission_date DATE,
        technical_spec TEXT,
        financial_spec TEXT,
        status TEXT CHECK(status IN('Submitted','Under Review','Accepted','Rejected','Withdrawn')) DEFAULT 'Submitted',
        opened_at DATETIME,
        technical_score REAL,
        financial_score REAL,
        final_score REAL,
        remarks TEXT,
        closed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_winner TEXT CHECK(is_winner IN('Yes', 'No')) DEFAULT 'No',
        PRIMARY KEY (vendor_id, tender_id),
        FOREIGN KEY (vendor_id) REFERENCES Vendor(vendor_id) 
            ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (tender_id) REFERENCES Tender(tender_id) 
            ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)

    # notifications table
    cur.execute(
    """
        CREATE TABLE IF NOT EXISTS Notification (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY(vendor_id) REFERENCES Vendor(vendor_id) ON DELETE CASCADE
        );
    """)

    # ##################
    # ### DUMMY DATA ###
    # ##################

    # # 5 Govt. Orgs
    # cur.executescript("""
    # INSERT INTO Organisation (name, email, phone, address, password) VALUES
    #     ('Public Works Department (PWD)', 'contact@pwd.pune.gov.in', '91123011234', 'Pune', 'pwd123'),
    #     ('Indian Railways', 'tenders@indianrail.gov.in', '91123381222', 'New Delhi', 'rail123'),
    #     ('National Thermal Power Corporation (NTPC)', 'procurement@ntpc.co.in', '91202451234', 'Noida', 'ntpc123'),
    #     ('Municipal Corporation of Pune (MCP)', 'eprocure@mcpune.gov.in', '92025501234', 'Pune', 'mcp123'),
    #     ('Indian Institute of Technology Bombay (IITB)', 'tenders@iitb.ac.in', '92225721234', 'Mumbai', 'iitb123');
    # """)
    
    
    # ## 7 Vendors
    # cur.executescript("""
    #     INSERT INTO Vendor (name, email, phone, address, password) VALUES
    #     ('Nova Trade Links', 'contact@novatradelinks.in', '9810011122', 'Delhi', 'nova123'),
    #     ('Orion Industrial Services', 'info@orionis.co.in', '9822022233', 'Mumbai', 'orion123'),
    #     ('Vertex Global Pvt. Ltd.', 'sales@vertexglobal.in', '9833033344', 'Bengaluru', 'vertex123'),
    #     ('Summit Engineering Works', 'support@summiteng.in', '9844044455', 'Hyderabad', 'summit123'),
    #     ('Keystone Enterprises', 'admin@keystoneent.in', '9855055566', 'Pune', 'keystone123'),
    #     ('Atlas Solutions', 'team@atlassolutions.in', '9866066677', 'Pune', 'atlas123'),
    #     ('Prime TechnoCorp', 'hello@primetechcorp.in', '9877077788', 'Kolkata', 'prime123');
    # """)
    
    # ## Tenders (1-2 per org)
    # cur.executescript("""
    #     INSERT INTO Tender (tender_ref_no, org_id, title, description, location, status, opening_date, closing_date, publishing_date)
    #     VALUES
    #     -- PWD
    #     ('PWD-2025-01', 1, 'Road Repair and Maintenance', 'Annual resurfacing and repair of arterial roads in Delhi region.', 'Delhi', 'Open', '2025-11-01', '2025-11-30', '2025-10-31'),
    #     ('PWD-2025-02', 1, 'Drainage System Upgrade', 'Upgradation of stormwater drainage system in Central Delhi zone.', 'Delhi', 'Open', '2025-11-05', '2025-12-05', '2025-11-02'),
    
    #     -- Indian Railways
    #     ('IR-2025-01', 2, 'Railway Station Renovation', 'Modernization of passenger amenities at New Delhi Station.', 'New Delhi', 'Open', '2025-11-02', '2025-12-06', '2025-11-01'),
    #     ('IR-2025-02', 2, 'Track Electrification Project', 'Electrification of 50 km of railway track in the Northern Division.', 'Haryana', 'Open', '2025-11-07', '2025-12-15', '2025-11-03'),
    
    #     -- NTPC
    #     ('NTPC-2025-01', 3, 'Procurement of Solar Panels', 'Supply and installation of 1000 high-efficiency solar panels.', 'Noida', 'Open', '2025-11-03', '2025-11-28', '2025-11-02'),
    
    #     -- MCP
    #     ('MCP-2025-01', 4, 'Solid Waste Management Project', 'Design and operation of automated waste collection systems.', 'Pune', 'Open', '2025-11-05', '2025-12-10', '2025-11-03'),
    #     ('MCP-2025-02', 4, 'Street Lighting Installation', 'Installation of LED streetlights in newly developed wards.', 'Pune', 'Open', '2025-11-09', '2025-12-05', '2025-11-04'),
    
    #     -- IITB
    #     ('IITB-2025-01', 5, 'Campus Network Upgrade', 'Deployment of Wi-Fi 6 access points across academic blocks.', 'Mumbai', 'Open', '2025-11-06', '2025-11-25', '2025-11-04');
    # """)
    
    # ## Bids
    # cur.executescript("""
    #     INSERT INTO Bid (vendor_id, tender_id, submission_date, technical_spec, financial_spec, status)
    #     VALUES
    #     -- PWD-2025-01
    #     (1, 1, '2025-11-02', 'Durable bitumen mix; ISO-certified process', '₹8,90,000', 'Submitted'),
    #     (2, 1, '2025-11-03', 'Rapid-lay asphalt solution', '₹9,10,000', 'Submitted'),
    #     (3, 1, '2025-11-03', 'Smart road sensors integrated', '₹9,30,000', 'Submitted'),
    
    #     -- PWD-2025-02
    #     (4, 2, '2025-11-06', 'HDPE drainage pipes; 10-year warranty', '₹14,50,000', 'Submitted'),
    #     (5, 2, '2025-11-07', 'Concrete reinforced chambers', '₹14,20,000', 'Submitted'),
    
    #     -- IR-2025-01
    #     (1, 3, '2025-11-04', 'Modular renovation design; fire-safety compliant', '₹18,40,000', 'Submitted'),
    #     (6, 3, '2025-11-04', 'Modern seating and LED signage', '₹18,10,000', 'Submitted'),
    
    #     -- IR-2025-02
    #     (2, 4, '2025-11-08', 'High-capacity transformers; BIS approved', '₹24,80,000', 'Submitted'),
    #     (7, 4, '2025-11-09', 'Copper wiring and energy-efficient motors', '₹25,10,000', 'Submitted'),
    
    #     -- NTPC-2025-01
    #     (3, 5, '2025-11-06', 'Mono PERC solar modules; 25-year warranty', '₹52,00,000', 'Submitted'),
    #     (4, 5, '2025-11-06', 'Tier-1 panels; on-site maintenance', '₹51,50,000', 'Submitted'),
    #     (5, 5, '2025-11-07', 'Hybrid inverter system included', '₹53,00,000', 'Submitted'),
    
    #     -- MCP-2025-01
    #     (6, 6, '2025-11-07', 'IoT-based waste collection system', '₹39,00,000', 'Submitted'),
    #     (7, 6, '2025-11-08', 'Automated sorting and compacting units', '₹38,70,000', 'Submitted'),
    
    #     -- MCP-2025-02
    #     (1, 7, '2025-11-10', 'LED lights with motion sensors', '₹16,50,000', 'Submitted'),
    #     (2, 7, '2025-11-10', 'Solar-powered street lights', '₹16,80,000', 'Submitted'),
    
    #     -- IITB-2025-01
    #     (3, 8, '2025-11-09', 'Wi-Fi 6 deployment; managed cloud control', '₹21,00,000', 'Submitted'),
    #     (5, 8, '2025-11-09', 'Full-fiber backbone with redundant routing', '₹20,70,000', 'Submitted'),
    #     (7, 8, '2025-11-10', 'High-density mesh setup', '₹20,90,000', 'Submitted');
    # """)
    
    
    conn.commit()
    conn.close()
    print("Database setup complete.")

    


if __name__ == "__main__":
    setup_database()