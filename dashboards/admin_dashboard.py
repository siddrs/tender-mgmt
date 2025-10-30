import streamlit as st
import pandas as pd
from database.db_utils import *

# admin login fuction
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

    # select box for all functionalities ek chhat ke neeche
    option = st.selectbox(
        "Select an action:",
        [
            "— Select —",
            "View All Vendors",
            "Add New Vendor",
            "Delete a Vendor",
            "Create Tender",
            "View All Tenders",
            "Delete Tenders",
            "Edit Tenders",
            "Logout"
        ]
    )

    # yaha pr i've tried to abstract away all SQL queries
    # they are present in the db_utils file WARNING: which is in a different subdirectory
    # check file structure
    # use 'black' for reformatting again and again so it doesn't look dreary
    # whenever table involved, pls use pandas dataframes (if you aren't able to, then only go for md)

    if option == "View All Vendors":
        vendors_df = get_all_vendors()
        if not vendors_df.empty:
            st.subheader("Registered Vendors")
            st.dataframe(vendors_df, use_container_width=True)
        else:
            st.info("No vendors found.")

    elif option == "Add New Vendor":
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

    elif option == "Logout":
        st.session_state.admin_logged_in = False
        st.success("Logged out successfully.")
        st.rerun()

    elif option == "Create Tender":
        create_tender()

    elif option == "View All Tenders":
        get_all_tenders()

    elif option == "Delete Tenders":
        st.subheader("Delete Tender")
        delete_tender()

    elif option == "Edit Tenders":
        st.subheader("Update Tender Details")
        edit()

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

        add_tender(
            tender_ref_no,
            title,
            description,
            location,
            opening_date_str,
            closing_date_str
        )

        st.success("Tender created successfully!")

