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

    conn.commit()
    conn.close()
    print("Database setup complete.")

    


if __name__ == "__main__":
    setup_database()