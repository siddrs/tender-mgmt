import streamlit as st
import pandas as pd
from database.db_utils import *

def admin_login():
    correct_password = "admin123"  # hardcoded admin password

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # If not logged in, show login form
    if not st.session_state.admin_logged_in:
        st.title(f"**Admin Login**")
        password = st.text_input("Enter Admin Password", type="password")

        if st.button("Login"):
            if password == correct_password:
                st.success("Login successful!")
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")

    # login check, show dashboard now
    else:
        show_admin_dashboard()


def show_admin_dashboard():
    # st.write('checking')
    st.title(f"**Admin Dashboard**")


    tab1, tab2, tab3, tab4 = st.tabs([f"**Manage Organisations**", f"**Manage Vendors**", f"**Manage Bids**", f"**Log Out**"])

    with tab1:
        manage_orgs()
    with tab2:
        manage_vendors()
    with tab3:
        manage_bids()
    with tab4:
        if st.button("Log Out"):
            st.session_state.admin_logged_in = False
            st.success("Logged out successfully.")
            st.rerun()


def manage_orgs():
    option = st.selectbox(
        "Select an action:",
        [
            "— Select —",
            "View All Organisations",
            "Delete Organisation",
        ]
    )

    if option == "View All Organisations":
        orgs = get_all_orgs()
        if not orgs.empty:
            st.subheader("Registered Organisations")
            st.dataframe(orgs, use_container_width=True, hide_index=True)
        else:
            st.info("No organisations found.")
    elif option == "Delete Organisation":
        st.subheader("Delete Organisation")
        email = st.text_input("Enter Organisation Email to Delete")

        if st.button("Delete Vendor"):
            delete_org_by_email(email)
            st.warning(f"Organisation with email '{email}' has been deleted (if existed).")
        # pass

def manage_vendors():
    option = st.selectbox(
        "Select an action:",
        [
            "— Select —",
            "View All Vendors",
            "Add a Vendor",
            "Delete a Vendor",
        ]
    )

    if option == "View All Vendors":
        vendors_df = get_all_vendors()
        if not vendors_df.empty:
            st.subheader("Registered Vendors")
            st.dataframe(vendors_df, use_container_width=True, hide_index=True)
        else:
            st.info("No vendors found.")

    elif option == "Add a Vendor":
        st.subheader("Add a New Vendor")
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_area("Address")
        password = st.text_input("Set Temporary Password", type="password")

        if st.button("Add Vendor"):
            add_vendor(name, email, phone, address, password)
            st.success(f"Vendor '{name}' added successfully!")

    elif option == "Delete a Vendor":
        st.subheader("Delete Vendor")
        email = st.text_input("Enter Vendor Email to Delete")

        if st.button("Delete Vendor"):
            delete_vendor_by_email(email)
            st.warning(f"Vendor with email '{email}' has been deleted (if existed).")


def manage_bids():
    option = st.selectbox(
        "Select an action:",
        [
            "— Select —",
            "View All Bids",
            "View Logs",
        ]
    )

    if option == "View All Bids":
        view_all_bids()
    elif option == "View Logs":
        pass


def view_all_bids():
    st.subheader("View All Bids")

    conn = get_connection()

    # org selector
    orgs = pd.read_sql_query("SELECT org_id, name FROM Organisation ORDER BY name", conn)
    if orgs.empty:
        st.info("No organisations found.")
        conn.close()
        return

    org_options = ["All"] + orgs["name"].tolist()
    selected_org = st.selectbox("Organisation", org_options, key="admin_filter_org")

    org_id = None
    if selected_org != "All":
        org_id = int(orgs.loc[orgs["name"] == selected_org, "org_id"].values[0])

    # tender selector
    if org_id:
        tenders_q = "SELECT tender_id, tender_ref_no, title FROM Tender WHERE org_id = ? ORDER BY publishing_date DESC"
        tenders = pd.read_sql_query(tenders_q, conn, params=(org_id,))
    else:
        tenders = pd.read_sql_query("SELECT tender_id, tender_ref_no, title FROM Tender ORDER BY publishing_date DESC", conn)

    tender_opts = ["All"] + (tenders["tender_ref_no"].tolist() if not tenders.empty else [])
    selected_tender_ref = st.selectbox(
        "Tender",
        tender_opts,
        key="admin_filter_tender",
        format_func=lambda r: r if r == "All" else f"{r} — {tenders.loc[tenders['tender_ref_no']==r,'title'].values[0]}" if r in tenders["tender_ref_no"].values else r
    )

    status_vals = ["All", "Submitted", "Under Review", "Accepted", "Rejected"]
    selected_status = st.selectbox("Bid Status", status_vals, index=0, key="admin_filter_status")

    include_logs = st.checkbox("Include historical bids (BidLog)", value=True)

    params = []
    sql_active = """
        SELECT
            b.vendor_id,
            v.name AS vendor_name,
            v.email AS vendor_email,
            b.tender_id,
            t.tender_ref_no,
            t.title AS tender_title,
            o.org_id,
            o.name AS organisation,
            b.submission_date,
            b.technical_spec,
            b.financial_spec,
            b.status,
            b.technical_score,
            b.financial_score,
            b.final_score,
            b.remarks
        FROM Bid b
        JOIN Vendor v ON b.vendor_id = v.vendor_id
        JOIN Tender t ON b.tender_id = t.tender_id
        LEFT JOIN Organisation o ON t.org_id = o.org_id
        WHERE 1=1
    """

    if org_id:
        sql_active += " AND o.org_id = ?"
        params.append(org_id)

    if selected_tender_ref != "All":
        sql_active += " AND t.tender_ref_no = ?"
        params.append(selected_tender_ref)

    active_params = list(params)
    if selected_status != "All":
        sql_active += " AND b.status = ?"
        active_params.append(selected_status)

    sql_active += " ORDER BY t.tender_ref_no, b.submission_date DESC"
    df_active = pd.read_sql_query(sql_active, conn, params=active_params)

    df_list = []
    if df_active is not None and not df_active.empty:
        df_active["record_source"] = "Active"
        df_active["is_winner"] = None
        df_list.append(df_active)

    if include_logs:
        params_log = []
        sql_log = """
            SELECT
                l.vendor_id,
                v.name AS vendor_name,
                v.email AS vendor_email,
                l.tender_id,
                t.tender_ref_no,
                t.title AS tender_title,
                o.org_id,
                o.name AS organisation,
                l.submission_date,
                l.technical_spec,
                l.financial_spec,
                l.status,
                l.technical_score,
                l.financial_score,
                l.final_score,
                l.remarks,
                l.is_winner
            FROM BidLog l
            JOIN Vendor v ON l.vendor_id = v.vendor_id
            JOIN Tender t ON l.tender_id = t.tender_id
            LEFT JOIN Organisation o ON t.org_id = o.org_id
            WHERE 1=1
        """
        if org_id:
            sql_log += " AND o.org_id = ?"
            params_log.append(org_id)
        if selected_tender_ref != "All":
            sql_log += " AND t.tender_ref_no = ?"
            params_log.append(selected_tender_ref)
        if selected_status != "All":
            sql_log += " AND l.status = ?"
            params_log.append(selected_status)

        sql_log += " ORDER BY t.tender_ref_no, l.submission_date DESC"
        df_log = pd.read_sql_query(sql_log, conn, params=params_log)
        if df_log is not None and not df_log.empty:
            df_log["record_source"] = "Log"
            # normalize is_winner to Yes/No strings
            df_log["is_winner"] = df_log["is_winner"].fillna("No").replace({1: "Yes", 0: "No", "1": "Yes", "0": "No"})
            df_list.append(df_log)

    if not df_list:
        st.info("No bids found for the selected filters.")
        conn.close()
        return

    df = pd.concat(df_list, ignore_index=True, sort=False)

    display_cols = [
        "organisation", "tender_ref_no", "tender_title",
        "vendor_name", "vendor_email", "submission_date",
        "record_source", "status", "is_winner", "technical_score", "financial_score", "final_score",
        "technical_spec", "financial_spec", "remarks"
    ]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols].reset_index(drop=True), use_container_width=True)

    # CSV download
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, file_name="bids_export.csv", mime="text/csv")

    conn.close()



    