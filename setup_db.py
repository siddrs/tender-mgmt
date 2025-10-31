import sqlite3


# should ideally run once after main function is called
# if you're doing some changes to the schema (not recommended) then try NOT to use ALTER.
# instead replace the .db file with another one, and old schema with new one (yes, the new file will be empty and not have the previous entries)

def setup_database():
    conn = sqlite3.connect("tendermanagement.db")
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
        CREATE TABLE IF NOT EXISTS Tender ( 
            tender_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tender_ref_no TEXT UNIQUE, 
            title TEXT NOT NULL, 
            description TEXT, 
            location TEXT, 
            status TEXT CHECK(status IN ('Open','Closed','Awarded')) DEFAULT 'Open', 
            opening_date DATE, 
            closing_date DATE, 
            publishing_date DATE,
            winner_vendor_id INTEGER,
            FOREIGN KEY (winner_vendor_id) 
                REFERENCES Vendor(vendor_id) 
                ON DELETE SET NULL ON UPDATE CASCADE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Bid ( 
            vendor_id INTEGER NOT NULL, 
            tender_id INTEGER NOT NULL, 
            submission_date DATE, 
            technical_spec TEXT, 
            financial_spec TEXT, 
            status TEXT CHECK(status IN ('Submitted','Under Review','Accepted','Rejected')) DEFAULT 'Submitted', 
            opened_at DATETIME, 
            technical_score REAL, 
            financial_score REAL, 
            final_score REAL, 
            remarks TEXT, 
            PRIMARY KEY (vendor_id, tender_id), 
            FOREIGN KEY (vendor_id) 
                REFERENCES Vendor(vendor_id) 
                ON DELETE CASCADE ON UPDATE CASCADE, 
            FOREIGN KEY (tender_id) 
                REFERENCES Tender(tender_id) 
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        
    """)

    cur.execute(""" CREATE
    TABLE IF NOT EXISTS
    BidLog(vendor_id INTEGER NOT NULL,
    tender_id INTEGER NOT NULL,
    submission_date DATE,
    technical_spec TEXT,
    financial_spec TEXT,
    status TEXT
    CHECK(status
    IN('Submitted', 'Under Review', 'Accepted', 'Rejected')) DEFAULT 'Submitted',
    opened_at DATETIME,
    technical_score REAL,
    financial_score REAL, final_score REAL,
    remarks TEXT,
    closed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_winner TEXT
    CHECK(is_winner
    IN('Yes', 'No')) DEFAULT
    'No',
    PRIMARY
    KEY(vendor_id, tender_id),
    FOREIGN
    KEY(vendor_id)
    REFERENCES
    Vendor(vendor_id) ON
    DELETE
    CASCADE
    ON
    UPDATE
    CASCADE,
    FOREIGN
    KEY(tender_id)
    REFERENCES
    Tender(tender_id)
    ON
    DELETE
    CASCADE
    ON
    UPDATE
    CASCADE
    );
    """)



    # ****** testing purposes only, might wanna delete later (or not) *******

    # cur.execute("""
    # INSERT INTO Bid (vendor_id, tender_id, submission_date, technical_spec, financial_spec, status)
    # VALUES
    # (1, 3, '2025-10-29', 'Specs: 4K materials, ISO-certified components', 'Bid amount: ₹9,80,000', 'Submitted'),
    # (2, 3, '2025-10-30', 'Specs: 3D printed modular parts', 'Bid amount: ₹9,50,000', 'Submitted'),
    # (3, 3, '2025-10-30', 'Specs: Fully automated assembly line', 'Bid amount: ₹10,20,000', 'Submitted'); """)
    #
    # cur.execute("""
    #     INSERT INTO Bid (vendor_id, tender_id, submission_date, technical_spec, financial_spec, status)
    # VALUES
    # (1, 1, '2025-10-30', 'Specs: Environmentally compliant raw materials', 'Bid amount: ₹8,70,000', 'Submitted'),
    # (2, 1, '2025-10-31', 'Specs: Local supplier chain with rapid delivery', 'Bid amount: ₹9,00,000', 'Submitted'),
    # (3, 1, '2025-10-31', 'Specs: Enhanced safety features, 2-year warranty', 'Bid amount: ₹9,20,000', 'Submitted');
    # """)

    # cur.execute("""
    # DELETE FROM Bid WHERE tender_id = 123
    # """)
    # cur.execute("""
    # DELETE FROM Bid WHERE tender_id = 124
    # """)



    conn.commit()
    conn.close()
    print("Database setup complete.")

    


if __name__ == "__main__":
    setup_database()