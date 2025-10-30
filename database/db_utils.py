import sqlite3
import pandas as pd
import os
import streamlit as st

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)
DB_PATH = os.path.join(BASE_DIR, "tendermanagement.db")


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
        st.dataframe(df, use_container_width=True)
        return

    # filter for locations
    elif group_by == "Location":
        for location, group_df in df.groupby("Location", dropna=False):

            st.write(f" **Location:** {location}" if location else "Not Applicable")
            st.dataframe(group_df.reset_index(drop=True), use_container_width=True)



    # filter for status
    elif group_by == "Status":
        for status, group_df in df.groupby("Status", dropna=False):

            st.write(f" **Status:** {status}" if status else "Not Applicable")
            st.dataframe(group_df.reset_index(drop=True), use_container_width=True)

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


