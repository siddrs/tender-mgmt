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
        pass
    if option == "View Logs":
        pass