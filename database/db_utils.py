import sqlite3
import pandas as pd
import os
import streamlit as st
from datetime import datetime

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)
DB_PATH = os.path.join(BASE_DIR, "database.db")


# sql queries here


def get_connection():
    return sqlite3.connect(DB_PATH)



# ----------------------------------------------------------------------------

# add new vendor (either by signing up, or via admin)
def add_vendor(name, email, phone, address, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Vendor (name, email, phone, address, password)
        VALUES (?, ?, ?, ?, ?)
    """,
        (name, email, phone, address, password),
    )
    conn.commit()
    conn.close()



# ----------------------------------------------------------------

# authentication for vendor
def verify_vendor(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM Vendor WHERE email = ? AND password = ?", (email, password)
    )
    data = cur.fetchone()
    conn.close()
    return data


# --------------------------------------------------------------

# show all the vendors in a pandas table
def get_all_vendors():
    conn = get_connection()
    query = "SELECT vendor_id, name, email, phone, address FROM Vendor"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# -------------------------------------------------------------


def get_all_tenders(org_id):

    st.subheader("View All Tenders")

    # Select grouping mode
    group_by = st.selectbox("Group tenders by:", ["None", "Location", "Status"])

    conn = get_connection()
    cur = conn.cursor()


    ###### debugging purposes ---> do no touch
    # st.write("Testing query")
    # cur.execute("SELECT * FROM Tender")
    # st.write(cur.fetchall())


    cur.execute(
        """
        SELECT 
            tender_id,
            tender_ref_no, 
            title, 
            description, location, 
            status, 
            opening_date, 
            closing_date, 
            publishing_date 
        FROM Tender WHERE org_id = ?
    """, (org_id,)
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        st.warning("No tenders found.")
        return

    df = pd.DataFrame(
        rows,
        columns=[
            "Tender ID",
            "Tender Reference",
            "Title",
            "Description",
            "Location",
            "Status",
            "Opening Date",
            "Closing Date",
            "Publishing Date",
        ],
    )

    # display all tenders
    if group_by == "None":
        st.dataframe(df, use_container_width=True, hide_index=True)
        return

    # filter for locations
    elif group_by == "Location":
        for location, group_df in df.groupby("Location", dropna=False):

            st.write(f" **Location:** {location}" if location else "Not Applicable")
            st.dataframe(group_df.reset_index(drop=True), use_container_width=True, hide_index=True)



    # filter for status
    elif group_by == "Status":
        for status, group_df in df.groupby("Status", dropna=False):

            st.write(f" **Status:** {status}" if status else "Not Applicable")
            st.dataframe(group_df.reset_index(drop=True), use_container_width=True, hide_index=True)

# ----------------------------------------------------------

# delete vendor with the entered email_id
def delete_vendor_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Vendor WHERE email=?", (email,))
    conn.commit()
    conn.close()




# ------------------------------------------------------------

# this function will add a new tender
def add_tender(ref_no, org_id, title, description, location, opening_date, closing_date):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO Tender 
            (tender_ref_no, org_id, title, description, location, status, opening_date, closing_date, publishing_date)
            VALUES (?, ?, ?, ?, ?, 'Open', ?, ?, DATE('now'))
            """,
            (ref_no, org_id, title, description, location, opening_date, closing_date),
        )

        conn.commit()
        print("Tender created successfully!")

    except sqlite3.Error as e:
        print("Database error while creating tender:", e)

    finally:
        conn.close()

 # ------------------------------------------------------------


def delete_tender(org_id):
    """
    Allows deletion only if today is before opening_date.
    If the tender is currently in its open window (opening_date <= today <= closing_date),
    shows and performs a withdraw operation instead.
    """
    from datetime import datetime as _dt

    conn = get_connection()
    cur = conn.cursor()

    # Fetch open tenders (status 'Open') for this org
    cur.execute("""
        SELECT tender_id, tender_ref_no, title, description, location, status,
               opening_date, closing_date, publishing_date
        FROM Tender WHERE status = 'Open' AND org_id = ?
    """, (org_id,))
    tenders = cur.fetchall()

    df = pd.DataFrame(
        tenders,
        columns=[
            "Tender ID", "Reference No", "Title", "Description", "Location", "Status",
            "Opening Date", "Closing Date", "Publishing Date"
        ]
    )

    if df.empty:
        st.warning("No tenders found that are available for deletion or withdrawal.")
        conn.close()
        return

    st.markdown("### Open Tenders")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

    options = []
    meta = {}
    for _, row in df.iterrows():
        s = f"{row['Reference No']} - {row['Title']}"
        options.append(s)
        meta[s] = {
            "tender_id": row["Tender ID"],
            "opening_date": row["Opening Date"],
            "closing_date": row["Closing Date"],
        }

    selected = st.selectbox("Select a Tender", options)

    # parse dates and compare with today
    selected_meta = meta[selected]
    today = _dt.now().date()

    try:
        opening = _dt.strptime(str(selected_meta["opening_date"]), "%Y-%m-%d").date()
    except Exception:
        opening = None
    try:
        closing = _dt.strptime(str(selected_meta["closing_date"]), "%Y-%m-%d").date()
    except Exception:
        closing = None

    # Decision logic
    if opening and today < opening:
        st.info(f"Tender opens on {opening}. You may delete it before opening.")
        if st.button("Delete Tender"):
            try:
                cur.execute(
                    "DELETE FROM Tender WHERE tender_id = ? AND status = 'Open'",
                    (selected_meta["tender_id"],)
                )
                conn.commit()
                if cur.rowcount > 0:
                    st.success(f"Tender '{selected}' deleted successfully.")
                else:
                    st.error("Tender could not be deleted. It may have changed status.")
            except sqlite3.Error as e:
                st.error(f"Database error: {e}")
            finally:
                conn.close()
                return

    elif opening and closing and opening <= today <= closing:
        st.warning(f"Tender is currently open ({opening} → {closing}). You cannot delete it but you can withdraw it.")
        st.markdown("Withdrawing will close the tender, move existing bids to BidLog as 'Withdrawn', and notify bidders.")
        if st.button("Withdraw Tender"):
            withdraw_tender(selected_meta["tender_id"], selected.split(" - ")[0], cur, conn)
            conn.close()
            return

    else:
        # If dates missing or today > closing
        if closing and today > closing:
            st.error(f"Tender closed on {closing}. It cannot be deleted or withdrawn via this interface.")
        else:
            # fallback if opening/closing not parsable
            st.error("Tender dates are not available or invalid. Deletion/withdrawal blocked.")
        conn.close()
        return


def withdraw_tender(tender_id, tender_ref_no, cur=None, conn=None):
    """
    Withdraw a tender that is currently in its open window.
    - Moves current Bid rows to BidLog with status 'Withdrawn' and is_winner='No'
    - Deletes moved rows from Bid
    - Updates Tender.status to 'Closed'
    - Inserts notifications for all affected vendors
    """
    close_conn_here = False
    if conn is None:
        conn = get_connection()
        cur = conn.cursor()
        close_conn_here = True

    try:
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # fetch all active bids for this tender
        cur.execute("SELECT * FROM Bid WHERE tender_id = ?", (tender_id,))
        bid_rows = cur.fetchall()
        # get column names for Bid to map values
        bid_cols_q = "PRAGMA table_info(Bid)"
        cur.execute(bid_cols_q)
        bid_cols = [r[1] for r in cur.fetchall()]  # names in order
        # map column positions for known fields we'll copy
        # We'll use column names explicitly to avoid schema-order dependence
        cur.execute("""
            SELECT vendor_id, tender_id, submission_date, technical_spec, financial_spec,
                   status, opened_at, technical_score, financial_score, final_score, remarks
            FROM Bid WHERE tender_id = ?
        """, (tender_id,))
        detailed_bids = cur.fetchall()

        # set bid status to withdrawn
        for row in detailed_bids:
            vendor_id = row[0]
            tid = row[1]
            submission_date = row[2]
            technical_spec = row[3]
            financial_spec = row[4]
            _status = 'Withdrawn'
            opened_at = row[6]
            technical_score = row[7]
            financial_score = row[8]
            final_score = row[9]
            remarks = row[10]

            cur.execute("""
                INSERT INTO BidLog (
                    vendor_id, tender_id, submission_date, technical_spec, financial_spec,
                    status, opened_at, technical_score, financial_score, final_score,
                    remarks, closed_timestamp, is_winner
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor_id,
                tid,
                submission_date,
                technical_spec,
                financial_spec,
                _status,
                opened_at,
                technical_score,
                financial_score,
                final_score,
                remarks,
                now_ts,
                'No'
            ))

            try:
                cur.execute(
                    "INSERT INTO Notification (vendor_id, title, message) VALUES (?, ?, ?)",
                    (vendor_id, "Tender Withdrawn", f"Tender {tender_ref_no} has been withdrawn by the organisation. Your bid has been archived.")
                )
            except Exception:
                pass

        # remove active bids
        cur.execute("DELETE FROM Bid WHERE tender_id = ?", (tender_id,))

        # close tender and clear winner
        cur.execute("UPDATE Tender SET status = 'Closed', winner_vendor_id = NULL WHERE tender_id = ?", (tender_id,))

        conn.commit()
        st.success(f"Tender {tender_ref_no} withdrawn. Active bids archived and bidders notified.")

    except Exception as e:
        conn.rollback()
        st.error(f"Error while withdrawing tender: {e}")
    finally:
        if close_conn_here:
            conn.close()

# -----------------------------------------------------

def edit(org_id):
    conn = get_connection()
    cur = conn.cursor()

    # Fetch all tenders
    cur.execute("""
            SELECT tender_id, tender_ref_no, title, description, location, status,
                   opening_date, closing_date, publishing_date
            FROM Tender WHERE status = 'Open' AND org_id = ?
        """, (org_id,))
    tenders = cur.fetchall()

    df = pd.DataFrame(
        tenders,
        columns=[
            "Tender ID", "Reference No", "Title", "Description", "Location", "Status",
            "Opening Date", "Closing Date", "Publishing Date"
        ]
    )

    if df.empty:
        st.warning("No tenders found that are available for deletion")
        conn.close()
        return

    st.markdown("### Open Tenders")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

    options = []

    for _, row in df.iterrows():
        s = f"{row['Reference No']} - {row['Title']}"
        options.append(s)

    selectedd = st.selectbox("Select a Tender to Delete", options)
    selected = selectedd.strip("-")[0]

    field_trip = ["Title", "Description", "Location", "Department", "Status", "Deadline"]
    selected2 = st.selectbox("Select Field to Update", field_trip)

    the_edit = st.text_input(f"Enter new value for {selected2}")

    if st.button("Update Tender"):
        if the_edit.strip() == "":
            st.error("New value cannot be empty.")
        else:
            query = f"UPDATE tenders SET {selected2.lower()} = ? WHERE tender_id = ?"
            cur.execute(f"UPDATE Tender SET {selected2.lower()} = ? WHERE tender_id = ?", (the_edit, selected))
            conn.commit()
            st.success(f"Tender Ref Number {selected} edited successfully!")

    conn.close()


# -------------------------------------

def vievaluate_bids(org_id):

# -------- PART 1 -> 1: View Open Tenders and submitted bids
    st.subheader("View Bids for Open Tenders")

    conn = get_connection()


    tenders = pd.read_sql_query(
        "SELECT tender_id, tender_ref_no, title FROM Tender WHERE status = 'Open' AND org_id = ?",
        conn,
        params=(org_id,)
    )


    if tenders.empty:
        st.warning("No open tenders available.")
        return


    selected_tender = st.selectbox(
        "Select an open tender:",
        tenders['tender_ref_no'],
        format_func=lambda ref: f"{ref} — {tenders.loc[tenders['tender_ref_no'] == ref, 'title'].values[0]}"
    )


    bids = pd.read_sql_query(
        """
        SELECT vendor_id, submission_date, technical_spec, financial_spec, status,
               technical_score, financial_score, final_score, remarks
        FROM Bid
        WHERE tender_id = (SELECT tender_id FROM Tender WHERE tender_ref_no = ?)
        """,
        conn,
        params=(selected_tender,)
    )

    if bids.empty:
        st.info("No bids submitted for this tender yet.")
    else:
        st.dataframe(bids, use_container_width=True)



    selected_vendor = st.selectbox("Select a vendor to evaluate:", bids['vendor_id'])

# ----- PART 2 -> evaluation phase ---------
    st.subheader("Evaluation Form")
    col1, col2 = st.columns(2)
    with col1:
        tech_score = st.number_input("Technical Score", min_value=0.0, max_value=100.0, step=0.5)
    with col2:
        fin_score = st.number_input("Financial Score", min_value=0.0, max_value=100.0, step=0.5)
    remarks = st.text_area("Remarks")


    if st.button("Evaluate and Save"):
        final_score = tech_score + fin_score
        conn.execute(
            """
            UPDATE Bid
            SET technical_score = ?, financial_score = ?, final_score = ?, remarks = ?, status = 'Under Review'
            WHERE vendor_id = ? AND tender_id = (SELECT tender_id FROM Tender WHERE tender_ref_no = ?)
            """,
            (tech_score, fin_score, final_score, remarks, selected_vendor, selected_tender)
        )
        cur = conn.cursor()
        cur.execute("SELECT name FROM Vendor WHERE vendor_id = ?", (selected_vendor,))

        vendor = cur.fetchone()[0]

        conn.commit()
        st.success(f"Awarded {final_score} / 200 to {vendor} for Tender Ref: {selected_tender}")
        #st.rerun()

    conn.close()


# ---------------------------------------------------------------------------------------------------------------------------------------

def get_vendor_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT vendor_id, name, email, phone, address FROM Vendor WHERE email = ?", (email,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"vendor_id": row[0], "name": row[1], "email": row[2], "phone": row[3], "address": row[4]}



def get_admin_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT org_id, name, email, phone, address FROM Organisation WHERE email = ?", (email,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"admin_id": row[0], "name": row[1], "email": row[2], "phone": row[3], "address": row[4]}


# -------------------------------------------------------------------------

def get_open_tenders(location=None, search=None, org_id=None):
    conn = get_connection()
    query = """
        SELECT
            t.tender_id,
            t.tender_ref_no,
            t.title,
            t.description,
            t.location,
            t.opening_date,
            t.closing_date,
            t.publishing_date,
            t.org_id,
            o.name AS org_name
        FROM Tender t
        LEFT JOIN Organisation o ON t.org_id = o.org_id
        WHERE t.status = 'Open'
    """
    params = []
    if org_id:
        query += " AND t.org_id = ?"
        params.append(org_id)
    if location:
        query += " AND t.location = ?"
        params.append(location)
    if search:
        query += " AND (t.title LIKE ? OR t.description LIKE ? OR t.tender_ref_no LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    query += " ORDER BY t.publishing_date DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_tenders_locations(org_id=None):
    conn = get_connection()
    cur = conn.cursor()
    if org_id:
        cur.execute("SELECT DISTINCT location FROM Tender WHERE location IS NOT NULL AND location != '' AND org_id = ?", (org_id,))
    else:
        cur.execute("SELECT DISTINCT location FROM Tender WHERE location IS NOT NULL AND location != ''")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def get_tender_by_ref(ref):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.tender_id, t.tender_ref_no, t.title, t.description, t.location,
               t.opening_date, t.closing_date, t.publishing_date, t.org_id, o.name
        FROM Tender t
        LEFT JOIN Organisation o ON t.org_id = o.org_id
        WHERE t.tender_ref_no = ?
    """, (ref,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    cols = ["tender_id", "tender_ref_no", "title", "description", "location",
            "opening_date", "closing_date", "publishing_date", "org_id", "org_name"]
    return dict(zip(cols, row))


def submit_bid(vendor_id, tender_ref_no, technical_spec, financial_spec):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT tender_id, status FROM Tender WHERE tender_ref_no = ?", (tender_ref_no,))
        r = cur.fetchone()
        if not r:
            return False, "Tender not found."
        tender_id, status = r
        if status != "Open":
            return False, "Tender is not open for bidding."

        # duplicate check
        cur.execute("SELECT 1 FROM Bid WHERE vendor_id = ? AND tender_id = ?", (vendor_id, tender_id))
        if cur.fetchone():
            return False, "You have already submitted a bid for this tender."

        submission_date = datetime.now().strftime("%Y-%m-%d")
        cur.execute("""
            INSERT INTO Bid (vendor_id, tender_id, submission_date, technical_spec, financial_spec, status, opened_at)
            VALUES (?, ?, ?, ?, ?, 'Submitted', datetime('now'))
        """, (vendor_id, tender_id, submission_date, technical_spec, financial_spec))
        conn.commit()
        return True, "Bid submitted successfully."
    except Exception as e:
        return False, f"DB error: {e}"
    finally:
        conn.close()


def delete_bid(tender_id, vendor_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM Bid
        WHERE tender_id = ? AND vendor_id = ? AND status = 'Submitted'
    """, (tender_id, vendor_id))
    conn.commit()
    conn.close()


def update_bid(vendor_id, tender_id, new_tech, new_fin):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE Bid
        SET technical_spec = ?, financial_spec = ?, submission_date = DATE('now')
        WHERE vendor_id = ? AND tender_id = ? AND status = 'Submitted'
    """, (new_tech, new_fin, vendor_id, tender_id))
    conn.commit()
    conn.close()

## Get active and closed bids
def get_bids_for_vendor(email):
    conn = get_connection()
    try:
        active_sql = """
        SELECT 
            b.tender_id,
            t.tender_ref_no,
            t.title,
            t.location,
            t.org_id,
            o.name AS org_name,
            b.submission_date,
            b.technical_spec,
            b.financial_spec,
            b.status,
            b.remarks,
            t.status AS tender_status,
            NULL AS is_winner,
            v.name AS vendor_name
        FROM Bid b
        JOIN Tender t ON b.tender_id = t.tender_id
        LEFT JOIN Organisation o ON t.org_id = o.org_id
        JOIN Vendor v ON b.vendor_id = v.vendor_id
        WHERE v.email = ?
        """

        closed_sql = """
        SELECT
            l.tender_id,
            t.tender_ref_no,
            t.title,
            t.location,
            t.org_id,
            o.name AS org_name,
            l.submission_date,
            l.technical_spec,
            l.financial_spec,
            l.status,
            l.remarks,
            t.status AS tender_status,
            l.is_winner,
            v.name AS vendor_name
        FROM BidLog l
        JOIN Tender t ON l.tender_id = t.tender_id
        LEFT JOIN Organisation o ON t.org_id = o.org_id
        JOIN Vendor v ON l.vendor_id = v.vendor_id
        WHERE v.email = ?
        """

        df_active = pd.read_sql_query(active_sql, conn, params=(email,))
        df_closed = pd.read_sql_query(closed_sql, conn, params=(email,))

        if not df_active.empty:
            df_active["record_type"] = "Active"
        if not df_closed.empty:
            df_closed["record_type"] = "Log"

        cols = [
            "tender_id", "tender_ref_no", "title", "location", "org_id", "org_name",
            "submission_date", "technical_spec", "financial_spec", "status", "remarks",
            "tender_status", "is_winner", "vendor_name", "record_type"
        ]

        # ensure all columns exist in both frames
        for df in (df_active, df_closed):
            for c in cols:
                if c not in df.columns:
                    df[c] = None

        combined = pd.concat([df_active[cols], df_closed[cols]], ignore_index=True)
        if combined.empty:
            return pd.DataFrame(columns=cols)

        combined["submission_date"] = pd.to_datetime(combined["submission_date"], errors="coerce")
        combined.sort_values(by="submission_date", ascending=False, inplace=True)

        # normalize winner flag to Yes/No strings
        combined["is_winner"] = combined["is_winner"].fillna("No")
        combined["is_winner"] = combined["is_winner"].replace({1: "Yes", 0: "No", "1": "Yes", "0": "No", "Yes":"Yes","No":"No"})

        # reset index and return
        return combined.reset_index(drop=True)
    finally:
        conn.close()


def create_notification(vendor_id, title, message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Notification (vendor_id, title, message) VALUES (?, ?, ?)
    """, (vendor_id, title, message))
    conn.commit()
    conn.close()


def get_notifications(vendor_email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT n.notification_id, n.title, n.message, n.timestamp, n.is_read
        FROM Notification n
        JOIN Vendor v ON v.vendor_id = n.vendor_id
        WHERE v.email = ?
        ORDER BY n.timestamp DESC
    """, (vendor_email,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_unread_notifications_count(vendor_email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM Notification n
        JOIN Vendor v ON v.vendor_id = n.vendor_id
        WHERE v.email = ? AND n.is_read = 0
    """, (vendor_email,))
    c = cur.fetchone()[0]
    conn.close()
    return c


def mark_notifications_read(vendor_email, ids=None):
    conn = get_connection()
    cur = conn.cursor()
    if ids:
        q = "UPDATE Notification SET is_read = 1 WHERE notification_id IN ({seq})".format(
            seq=",".join(["?"] * len(ids))
        )
        cur.execute(q, ids)
    else:
        cur.execute("""
            UPDATE Notification SET is_read = 1
            WHERE vendor_id = (SELECT vendor_id FROM Vendor WHERE email = ?)
        """, (vendor_email,))
    conn.commit()
    conn.close()

# --------------------------------------


def view_logs():
    st.header("View Awarded Tender Logs")

    conn = get_connection()

    logs_query = """
        SELECT 
            l.tender_id,
            t.tender_ref_no,
            t.title AS tender_title,
            l.vendor_id,
            v.name AS vendor_name,
            l.technical_score,
            l.financial_score,
            l.final_score,
            l.remarks,
            l.closed_timestamp,
            l.is_winner
        FROM BidLog l
        JOIN Tender t ON l.tender_id = t.tender_id
        LEFT JOIN Vendor v ON l.vendor_id = v.vendor_id
        ORDER BY l.tender_id, l.final_score DESC
    """

    logs = pd.read_sql_query(logs_query, conn)
    conn.close()

    if logs.empty:
        st.info("No logs available.")
        return


    tender_groups = logs.groupby(['tender_id', 'tender_ref_no', 'tender_title'])

    for (tender_id, ref, title), group in tender_groups:
        st.subheader(f"Tender {ref} — {title}")

        group_display = group.copy()
        group_display['Winner'] = group_display['is_winner'].apply(lambda x: "Winner" if x == 'Yes' else "No")
        st.dataframe(group_display[['vendor_id', 'vendor_name', 'technical_score',
                                    'financial_score', 'final_score', 'remarks', 'closed_timestamp', 'Winner']],
                     use_container_width=True)


# --------------------------

def award():
    st.header("Award Tender")

    conn = get_connection()
    cur = conn.cursor()

    org_id = st.session_state.get("org_id")

    if org_id:
        tenders = pd.read_sql_query(
            "SELECT tender_id, tender_ref_no, title FROM Tender WHERE status = 'Open' AND org_id = ?",
            conn,
            params=(org_id,)
        )
    else:
        # fallback (admin) sees all open tenders
        tenders = pd.read_sql_query(
            "SELECT tender_id, tender_ref_no, title FROM Tender WHERE status = 'Open'",
            conn
        )

    if tenders.empty:
        st.warning("No open tenders available.")
        conn.close()
        return

    selected_ref = st.selectbox(
        "Select an open tender:",
        tenders['tender_ref_no'],
        format_func=lambda ref: f"{ref} — {tenders.loc[tenders['tender_ref_no'] == ref, 'title'].values[0]}"
    )
    tender_id = int(tenders.loc[tenders['tender_ref_no'] == selected_ref, 'tender_id'].values[0])

    bids = pd.read_sql_query(
        "SELECT * FROM Bid WHERE tender_id = ?",
        conn,
        params=(tender_id,)
    )
    if bids.empty:
        st.info("No bids submitted for this tender yet.")
        conn.close()
        return

    st.subheader("Bids for this tender")
    st.dataframe(bids, use_container_width=True)

    if bids['final_score'].isnull().any():
        st.warning("Cannot award this tender. Some bids have not been evaluated yet.")
        conn.close()
        return

    st.success("All bids have been evaluated. You can now select a winner.")
    vendor_options = []
    for _, row in bids.iterrows():
        cur.execute("SELECT name FROM Vendor WHERE vendor_id = ?", (row['vendor_id'],))
        result = cur.fetchone()
        name = result[0] if result else "Unknown"
        vendor_options.append(f"{row['vendor_id']} — {name}")

    selected_vendor_str = st.selectbox("Select winner:", vendor_options)
    winner_id = int(selected_vendor_str.split(" — ")[0])

    if st.button("Award Tender"):
        try:
            closed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # copy to BidLog with accepted / rejected status
            for _, row in bids.iterrows():
                vid = int(row['vendor_id'])
                is_winner_flag = 'Yes' if vid == winner_id else 'No'
                status_to_write = 'Accepted' if vid == winner_id else 'Rejected'

                cur.execute("""
                    INSERT INTO BidLog (
                        vendor_id, tender_id, submission_date, technical_spec, financial_spec,
                        status, opened_at, technical_score, financial_score, final_score,
                        remarks, closed_timestamp, is_winner
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['vendor_id'],
                    row['tender_id'],
                    row.get('submission_date'),
                    row.get('technical_spec'),
                    row.get('financial_spec'),
                    status_to_write,
                    row.get('opened_at'),
                    row.get('technical_score'),
                    row.get('financial_score'),
                    row.get('final_score'),
                    row.get('remarks'),
                    closed_time,
                    is_winner_flag
                ))

            # remove active bids
            cur.execute("DELETE FROM Bid WHERE tender_id = ?", (tender_id,))

            # update tender to Closed and set winner
            cur.execute("UPDATE Tender SET status = 'Closed', winner_vendor_id = ? WHERE tender_id = ?", (winner_id, tender_id))

            # notifications
            try:
                cur.execute(
                    "INSERT INTO Notification (vendor_id, title, message) VALUES (?, ?, ?)",
                    (winner_id, ":green[TENDER AWARDED]", f"Congratulations! Tender {selected_ref} has awarded to your bid.")
                )
                for _, row in bids.iterrows():
                    vid = int(row['vendor_id'])
                    if vid != winner_id:
                        cur.execute(
                            "INSERT INTO Notification (vendor_id, title, message) VALUES (?, ?, ?)",
                            (vid, ":red[TENDER RESULT]", f"Your bid for the tender {selected_ref} was not selected. Thank you for participating.")
                        )
            except Exception:
                pass

            conn.commit()
            st.success(f"Tender {selected_ref} awarded successfully and moved to BidLog (tender closed).")

        except Exception as e:
            conn.rollback()
            st.error(f"Error while awarding tender: {e}")

        finally:
            conn.close()


# ---------------------------------------------------------


def get_all_orgs():
    conn = get_connection()
    query = "SELECT org_id, name, email, phone, address FROM Organisation"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def delete_org_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Organisation WHERE email=?", (email,))
    conn.commit()
    conn.close()
