# Push to branch MASTER, not MAIN

import streamlit as st
from dashboards.admin_dashboard import admin_login
from dashboards.vendor_dashboard import vendor_login  # i have added it
from setup_db import setup_database

def main():
    st.sidebar.title("Tender Management System")
    role = st.sidebar.radio("Login as:", ["Admin", "Vendor"])

    if 'db_initialized' not in st.session_state:
        setup_database()
        st.session_state.db_initialized = True

    if role == "Admin":
        admin_login()
    else:
        vendor_login()  # we’ll build this soon

if __name__ == "__main__":
    main()
