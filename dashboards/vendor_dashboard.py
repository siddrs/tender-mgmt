import streamlit as st
import sqlite3
from database.db_utils import get_connection


def vendor_login():
    if "vendor_logged_in" not in st.session_state:
        st.session_state.vendor_logged_in = False
    if "vendor_email" not in st.session_state:
        st.session_state.vendor_email = None

    # Tabs for Login and Signup
    tab1, tab2 = st.tabs(["Login", "Signup"])

    # LOGIN TAB
    with tab1:
        st.subheader("🔑 Vendor Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM Vendor WHERE email=? AND password=?", (email, password))
            vendor = cur.fetchone()
            conn.close()

            if vendor:
                st.success(f"Welcome back, {vendor[1]}!")
                st.session_state.vendor_logged_in = True
                st.session_state.vendor_email = email
                st.rerun()
            else:
                st.error("Invalid email or password.")

    # SIGNUP TAB
    with tab2:
        st.subheader("📝 Vendor Signup")
        name = st.text_input("Full Name")
        email_signup = st.text_input("Email", key="signup_email")
        phone = st.text_input("Phone")
        address = st.text_area("Address")
        password_signup = st.text_input("Create Password", type="password", key="signup_password")

        if st.button("Sign Up"):
            if not name or not email_signup or not password_signup:
                st.warning("Please fill all required fields.")
            else:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM Vendor WHERE email=?", (email_signup,))
                existing = cur.fetchone()

                if existing:
                    st.warning("Email already registered. Please log in instead.")
                else:
                    cur.execute(
                        "INSERT INTO Vendor (name, email, phone, address, password) VALUES (?, ?, ?, ?, ?)",
                        (name, email_signup, phone, address, password_signup),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Signup successful! You can now log in.")

    # Show dashboard once logged in
    if st.session_state.vendor_logged_in:
        st.success(f"Logged in as: {st.session_state.vendor_email}")
        st.write("Vendor dashboard will appear here.")
