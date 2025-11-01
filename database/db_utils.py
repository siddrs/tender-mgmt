import sqlite3
import pandas as pd
import os
import streamlit as st
from datetime import datetime

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)
DB_PATH = os.path.join(BASE_DIR, "tendermanagement.db")


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


def get_all_tenders():

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
        FROM Tender
    """
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
def add_tender(ref_no, title, description, location, opening_date, closing_date):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO Tender (tender_ref_no, title, description, location, status, opening_date, closing_date, publishing_date)
VALUES (?, ?, ?, ?, 'Open', ?, ?, DATE('now'))

        """,
            (ref_no, title, description, location, opening_date, closing_date),
        )

        conn.commit()
        print("Tender created successfully!")

    except sqlite3.Error as e:
        print("Database error while creating tender:", e)

    finally:
        conn.close()



 # ------------------------------------------------------------


def delete_tender():
    conn = get_connection()
    cur = conn.cursor()

    # Fetch all tenders
    cur.execute("""
        SELECT tender_id, tender_ref_no, title, description, location, status,
               opening_date, closing_date, publishing_date
        FROM Tender WHERE status = 'Open'
    """)
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

    selected = st.selectbox("Select a Tender to Delete", options)

    if st.button("Delete Tender"):

        to_extract_reference_id = selected.split(" - ")
        tender_ref_no = to_extract_reference_id[0]

        try:
            cur.execute(
                "DELETE FROM Tender WHERE tender_ref_no = ? AND status = 'Open'",
                (tender_ref_no,)
            )
            conn.commit()

            if cur.rowcount > 0:
                st.success(f"Tender '{tender_ref_no}' deleted successfully.")
            else:
                st.error("Tender could not be deleted. Check if it is open.")

        except sqlite3.Error as e:
            st.error(f"Database error: {e}")
        finally:
            conn.close()

# -----------------------------------------------------

def edit():
    conn = get_connection()
    cur = conn.cursor()

    # Fetch all tenders
    cur.execute("""
            SELECT tender_id, tender_ref_no, title, description, location, status,
                   opening_date, closing_date, publishing_date
            FROM Tender WHERE status = 'Open'
        """)
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

def vievaluate_bids():

# -------- PART 1 -> 1: View Open Tenders and submitted bids
    st.subheader("View Bids for Open Tenders")

    conn = get_connection()


    tenders = pd.read_sql_query(
        "SELECT tender_id, tender_ref_no, title FROM Tender WHERE status = 'Open'",
        conn
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

#def award():
#     # wahi sab upar wala
#     st.header("Award Tender")
#     conn = get_connection()
#
#     tenders = pd.read_sql_query(
#         "SELECT tender_id, tender_ref_no, title FROM Tender WHERE status = 'Open'",
#         conn
#     )
#
#     if tenders.empty:
#         st.warning("No open tenders available.")
#         return
#
#
#     selected = st.selectbox(
#         "Select an open tender to award:",
#         tenders['tender_id'],
#         format_func=lambda ref: f"{ref} — {tenders.loc[tenders['tender_id'] == ref, 'title'].values[0]}"
#     )
#
#     tender_id = tenders.loc[tenders['tender_id'] == selected, 'tender_id'].values[0]
#
#     bids = pd.read_sql_query(
#         """
#         SELECT vendor_id, technical_score, financial_score, final_score, remarks
#         FROM Bid WHERE tender_id = ?
#         """,
#         conn,
#         params=(tender_id,)
#     )
#
#     if bids.empty:
#         st.info("No bids submitted for this tender.")
#         return
#
#
#     if bids['final_score'].isnull().any():
#         st.warning("All bids must be evaluated before awarding this tender.")
#         st.dataframe(bids)
#         return
#
#
#     bids_sorted = bids.sort_values(by='final_score', ascending=False)
#     st.subheader("All Evaluated Bids")
#     st.dataframe(bids_sorted, use_container_width=True)
#
#     winner_id = st.selectbox("Select the winning vendor:", bids_sorted['vendor_id'])
#
# # -------------------- winner ---------------------------------------------------------------
#     if st.button("Award Tender"):
#         try:
#             closed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#             cursor = conn.cursor()
#             cursor.execute("""
#                 INSERT INTO Logs (
#                     vendor_id, tender_id, submission_date, technical_spec, financial_spec,
#                     status, opened_at, technical_score, financial_score, final_score,
#                     remarks, closed_timestamp, is_winner
#                 )
#                 SELECT vendor_id, tender_id, submission_date, technical_spec, financial_spec,
#                        status, opened_at, technical_score, financial_score, final_score,
#                        remarks, ?, CASE WHEN vendor_id = ? THEN 1 ELSE 0 END
#                 FROM Bid WHERE tender_id = ?
#             """, (closed_time, winner_id, tender_id))
#
#             cursor.execute("DELETE FROM Bid WHERE tender_id = ?", (tender_id,))
#
#
#             cursor.execute("UPDATE Tender SET status = 'Closed' WHERE tender_id = ?", (tender_id,))
#
#             conn.commit()
#
#             st.success(f"Tender {selected} has been awarded successfully and moved to Logs")
#             st.rerun()
#
#         except Exception as e:
#             conn.rollback()
#             st.error(f"Error while awarding tender: {e}")
#
#     conn.close()
#

# --------------
# doesn't work yet
def award():
    conn = get_connection()
    cur = conn.cursor()

    # Get open tenders
    tenders = pd.read_sql_query(
        "SELECT tender_id, tender_ref_no, title FROM Tender WHERE status = 'Open'",
        conn
    )

    if tenders.empty:
        st.warning("No open tenders available.")
        return

    # Select tender
    selected_ref = st.selectbox(
        "Select an open tender:",
        tenders['tender_ref_no'],
        format_func=lambda ref: f"{ref} — {tenders.loc[tenders['tender_ref_no'] == ref, 'title'].values[0]}"
    )

    tender_id = tenders.loc[tenders['tender_ref_no'] == selected_ref, 'tender_id'].values[0]

    bids = pd.read_sql_query(
        """
        SELECT vendor_id, submission_date, technical_spec, financial_spec, status,
               technical_score, financial_score, final_score, remarks
        FROM Bid
        WHERE tender_id = ?
        """,
        conn,
        params=(tender_id,)
    )

    if bids.empty:
        st.info("No bids submitted for this tender yet.")
        return
    else:
        st.dataframe(bids, use_container_width=True)

    vendor_list = []
    for _, bid in bids.iterrows():
        cur.execute("SELECT name FROM Vendor WHERE vendor_id = ?", (bid['vendor_id'],))
        vendor_name = cur.fetchone()[0]
        vendor_list.append(f"{bid['vendor_id']} - {vendor_name}")

    selected_vendor= st.selectbox("Select a winner", vendor_list)
    winner_id = int(selected_vendor.split(" - ")[0])

    if st.button("Award Tender"):
        try:
            closed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO BidLog (
                    vendor_id, tender_id, submission_date, technical_spec, financial_spec,
                    status, opened_at, technical_score, financial_score, final_score,
                    remarks, closed_timestamp, is_winner
                )
                SELECT vendor_id, tender_id, submission_date, technical_spec, financial_spec,
                       status, opened_at, technical_score, financial_score, final_score,
                       remarks, ?, CASE WHEN vendor_id = ? THEN 1 ELSE 0 END
                FROM Bid WHERE tender_id = ?
            """, (closed_time, winner_id, tender_id))


            cursor.execute("DELETE FROM Bid WHERE tender_id = ?", (tender_id,))
            cursor.execute("UPDATE Tender SET status = 'Closed' WHERE tender_id = ?", (tender_id,))
            conn.commit()

            st.success(f"Tender {tender_id} has been awarded successfully and moved to Logs")
            #st.rerun()

        except Exception as e:
            conn.rollback()
            st.error(f"Error while awarding tender: {e}")

    conn.close()


### VENDOR HELPER FUNCTIONS ###

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


def get_open_tenders(location=None, search=None):
    conn = get_connection()
    query = """
        SELECT tender_id, tender_ref_no, title, description, location,
               opening_date, closing_date, publishing_date
        FROM Tender
        WHERE status = 'Open'
    """
    params = []
    if location:
        query += " AND location = ?"
        params.append(location)
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR tender_ref_no LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    query += " ORDER BY publishing_date DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_tenders_locations():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT location FROM Tender WHERE location IS NOT NULL AND location != ''")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def get_tender_by_ref(ref):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT tender_id, tender_ref_no, title, description, location,
               opening_date, closing_date, publishing_date
        FROM Tender WHERE tender_ref_no = ?
    """, (ref,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    cols = ["tender_id", "tender_ref_no", "title", "description", "location",
            "opening_date", "closing_date", "publishing_date"]
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


def get_bids_for_vendor(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            b.tender_id,
            t.tender_ref_no,
            t.title,
            t.location,
            b.submission_date,
            b.technical_spec,
            b.financial_spec,
            b.status,
            b.remarks
        FROM Bid b
        JOIN Tender t ON b.tender_id = t.tender_id
        JOIN Vendor v ON b.vendor_id = v.vendor_id
        WHERE v.email = ?
        ORDER BY b.submission_date DESC
    """, (email,))
    rows = cur.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "tender_id",
        "tender_ref_no",
        "title",
        "location",
        "submission_date",
        "technical_spec",
        "financial_spec",
        "status",
        "remarks"
    ])
    return df

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


