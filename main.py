# Push to branch MASTER, not MAIN

import streamlit as st
from dashboards.org_dashboard import org_login
from dashboards.vendor_dashboard import vendor_login # i have added it
from dashboards.admin_dashboard import admin_login
from setup_db import setup_database
import urllib.parse

# use wide layout by default
st.set_page_config(
    layout="wide",
    page_title="Tender Management System",
    initial_sidebar_state="expanded"    
) 

def main():
    st.sidebar.title("Tender Management System")
    role = st.sidebar.radio("Login as:", ["Admin", "Organisation", "Vendor"])

    if 'db_initialized' not in st.session_state:
        setup_database()
        st.session_state.db_initialized = True

    if role == "Organisation":
        org_login()

    elif role == "Vendor":
        vendor_login()

    else:
        admin_login()

if __name__ == "__main__":
    main()
