import streamlit as st
import pandas as pd
from database.db_utils import *

def org_login():

    if "org_logged_in" not in st.session_state:
        st.session_state.org_logged_in = False
    if "org_email" not in st.session_state:
        st.session_state.org_email = None

    if st.session_state.org_logged_in:
        show_org_dashboard()
        return

    tab1, tab2 = st.tabs(["Login", "Signup"])

    # LOGIN TAB
    with tab1:
        st.subheader("Organization Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT org_id, name, password FROM Organisation WHERE email=?",
                (email,)
            )
            org = cur.fetchone()
            conn.close()

            if org and password == org[2]:
                st.session_state.org_logged_in = True
                st.session_state.org_email = email
                st.session_state['org_id'] = org[0]
                st.session_state['org_name'] = org[1]
                st.success(f"Showing dashboard for {org[1]}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    # SIGNUP TAB
    with tab2:
        st.subheader("Organization Signup")
        name = st.text_input("Organization Name", key="su_name")
        email_signup = st.text_input("Email", key="su_email")
        phone = st.text_input("Phone", key="su_phone")
        address = st.text_area("Address", key="su_address")
        password_signup = st.text_input("Create Password", type="password", key="su_password")

        if st.button("Sign Up"):
            if not name or not email_signup or not password_signup:
                st.warning("Please fill all required fields.")
            else:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM Organisation WHERE email=?", (email_signup,))
                existing = cur.fetchone()

                if existing:
                    st.warning("Email already registered. Please log in instead.")
                else:
                    cur.execute(
                        "INSERT INTO Organisation (name, email, phone, address, password) VALUES (?, ?, ?, ?, ?)",
                        (name, email_signup, phone, address, password_signup),
                    )
                    conn.commit()
                    st.success("Signup successful! You can now log in.")
                conn.close()




def show_org_dashboard():
    # st.write('checking')
    st.title(f"**Organisation Dashboard**")
    # st.sidebar.title(f"**Admin Dashboard**")
    # fxn = st.sidebar.radio("Select:", ["Manage Tenders", "Manage Vendors", "Manage Bids", "Log Out"])

    org_name = st.session_state.get("org_name")
    org_email = st.session_state.get("org_email")
    st.success(f"Logged in as: {org_email}")

    tab1, tab2, tab3 = st.tabs([f"**Manage Tenders**", f"**Manage Bids**", f"**Log Out**"])

    with tab1:
        manage_tenders()
    with tab2:
        manage_bids()
    with tab3:
        if st.button("Log Out"):
            st.session_state.org_logged_in = False
            st.success("Logged out successfully.")
            st.rerun()


def manage_bids():
    option = st.selectbox(
        "Select an action:",
        [
            "— Select —",
            "View and Evaluate a Bid",
            "Award Bids",
        ]
    )


    if option == "View and Evaluate a Bid":
        if 'org_id' not in st.session_state:
            st.error("Session expired. Please log in again.")
            st.stop()
        org_id = st.session_state.get('org_id')
        vievaluate_bids(org_id)

    elif option == "Award Bids":
        award()

# def manage_vendors():
#     option = st.selectbox(
#         "Select an action:",
#         [
#             "— Select —",
#             "View All Vendors",
#             "Add a Vendor",
#             "Delete a Vendor",
#         ]
#     )
#
#     if option == "View All Vendors":
#         vendors_df = get_all_vendors()
#         if not vendors_df.empty:
#             st.subheader("Registered Vendors")
#             st.dataframe(vendors_df, use_container_width=True, hide_index=True)
#         else:
#             st.info("No vendors found.")
#
#     elif option == "Add a Vendor":
#         st.subheader("Add a New Vendor")
#         name = st.text_input("Name")
#         email = st.text_input("Email")
#         phone = st.text_input("Phone")
#         address = st.text_area("Address")
#         password = st.text_input("Set Temporary Password", type="password")
#
#         if st.button("Add Vendor"):
#             add_vendor(name, email, phone, address, password)
#             st.success(f"Vendor '{name}' added successfully!")
#
#     elif option == "Delete a Vendor":
#         st.subheader("Delete Vendor")
#         email = st.text_input("Enter Vendor Email to Delete")
#
#         if st.button("Delete Vendor"):
#             delete_vendor_by_email(email)
#             st.warning(f"Vendor with email '{email}' has been deleted (if existed).")
#


def manage_tenders():
    option = st.selectbox(
        "Select an action:",
        [
            "— Select —",
            "Create Tender",
            "View All Tenders",
            "Delete Tenders",
            "Edit Tenders",
        ]
    )

    if option == "Create Tender":
        create_tender()

    elif option == "View All Tenders":
        if 'org_id' not in st.session_state:
            st.error("Session expired. Please log in again.")
            st.stop()
        org_id = st.session_state.get('org_id')
        get_all_tenders(org_id)

    elif option == "Delete Tenders":
        st.subheader("Delete Tender")
        if 'org_id' not in st.session_state:
            st.error("Session expired. Please log in again.")
            st.stop()
        org_id = st.session_state.get('org_id')
        delete_tender(org_id)

    elif option == "Edit Tenders":
        st.subheader("Update Tender Details")
        if 'org_id' not in st.session_state:
            st.error("Session expired. Please log in again.")
            st.stop()
        org_id = st.session_state.get('org_id')
        edit(org_id)









    # checking purposes only
    #conn = get_connection()
    # cur = conn.cursor()
    # cur.execute("""
    # SELECT * FROM Bid
    # """)
    # rows = cur.fetchall()
    # conn.close()
    #
    # if not rows:
    #     st.warning("Oops!")
    #     return
    #
    # df = pd.DataFrame(
    #     rows
    # )
    # st.dataframe(df, use_container_width=True)






def create_tender():
    st.subheader("Create New Tender")

    tender_ref_no = st.text_input("Tender Reference Number")
    title = st.text_input("Title")
    description = st.text_area("Description")
    location = st.text_input("Location")


    opening_date = st.date_input("Opening Date")
    closing_date = st.date_input("Closing Date")

    if st.button("Create Tender"):
        opening_date_str = opening_date.strftime("%Y-%m-%d")
        closing_date_str = closing_date.strftime("%Y-%m-%d")

        if 'org_id' not in st.session_state:
            st.error("Session expired. Please log in again.")
            st.stop()
        org_id = st.session_state.get('org_id')

        add_tender(
            tender_ref_no,
            org_id,
            title,
            description,
            location,
            opening_date_str,
            closing_date_str
        )

        st.success("Tender created successfully!")






 # # select box for all functionalities ek chhat ke neeche
 #    option = st.selectbox(
 #        "Select an action:",
 #        [
 #            "— Select —",
 #            "View All Vendors",
 #            "Add New Vendor",
 #            "Delete a Vendor",
 #            "Create Tender",
 #            "View All Tenders",
 #            "Delete Tenders",
 #            "Edit Tenders",
 #            "Logout"
 #        ]
 #    )
