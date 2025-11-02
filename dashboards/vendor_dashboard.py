import streamlit as st
import sqlite3
import pandas as pd
from database.db_utils import *


def vendor_login():
    if "vendor_logged_in" not in st.session_state:
        st.session_state.vendor_logged_in = False
    if "vendor_email" not in st.session_state:
        st.session_state.vendor_email = None

    # Show dashboard once logged in
    if st.session_state.vendor_logged_in:
        show_vendor_dashboard()

    # Show login and signup tabs if not logged in
    else: 
        tab1, tab2 = st.tabs(["Login", "Signup"])

        # LOGIN TAB
        with tab1:
            st.subheader("Vendor Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login"):
                vendor = get_vendor_by_email(email)
                if vendor:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT password FROM Vendor WHERE email=?", (email,))
                    row = cur.fetchone()
                    conn.close()

                    if row and password == row[0]:
                        st.success(f"Welcome back, {vendor['name']}!")
                        st.session_state.vendor_logged_in = True
                        st.session_state.vendor_email = email
                        # clear small keys
                        if "login_password" in st.session_state:
                            del st.session_state["login_password"]
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                else:
                    st.error("Invalid credentials.")

        # SIGNUP TAB
        with tab2:
            st.subheader("Vendor Signup")
            name = st.text_input("Full Name", key="su_name")
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
                    cur.execute("SELECT 1 FROM Vendor WHERE email=?", (email_signup,))
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



######################
### Main Dashboard ###
######################

def show_vendor_dashboard():

    if st.session_state.get("page") == "tender_details":
        show_tender_details()
        return
    elif st.session_state.get("page") == "view_bid":
        view_bid_page()
        return
    elif st.session_state.get("page") == "edit_bid":
        edit_bid_page()
        return

    
    vendor = get_vendor_by_email(st.session_state.vendor_email)
    unread = get_unread_notifications_count(st.session_state.vendor_email)

    st.success(f"Logged in as: {vendor['email']}")
    st.title("Vendor Dashboard")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"Open Tenders",
        f"Submit a Bid",
        f"Submitted Bids",
        f"Inbox ({unread})",
        f"Logout"
    ])

    with tab1:
        show_open_tenders()
    with tab2:
        submit_bid_tab(vendor)
    with tab3:
        submitted_bids_tab(vendor)
    with tab4:
        inbox_tab(vendor)
    with tab5:
        if st.button("Log Out"):
            st.session_state.vendor_logged_in = False
            st.session_state.vendor_email = None
            st.session_state.page = None
            st.success("Logged out.")
            st.rerun()




########################
### Open Tenders tab ###
########################

def show_open_tenders():
    st.header("Open Tenders")
    # filters
    locations = get_tenders_locations()
    loc_options = ["All"] + sorted([l for l in locations if l])
    col_f1, col_f2 = st.columns([2, 4])
    with col_f1:
        loc = st.selectbox("Location", loc_options, key="filter_location")
    with col_f2:
        search = st.text_input("Search title / ref", key="filter_search")

    df = get_open_tenders(location=None if loc == "All" else loc, search=search or None)
    if df.empty:
        st.info("No open tenders")
        return

    st.markdown("""
        <style>
            div[data-testid="stVerticalBlock"] > div:has(div.tender-row) {
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }
            .tender-row {
                border: 1px solid #e6e6e6;
            }
            .tender-title {
                margin-top: 15px;
            }
            .tender-meta {
                font-size: 1rem;
                margin-bottom: 10px;
            }
            .stButton > button {
                padding: 3px 10px;
                font-size: 0.85rem;
            }
        </style>
    """, unsafe_allow_html=True)

    for _, row in df.iterrows():
        ref = row["tender_ref_no"]
        title = row["title"] or "Untitled"
        opening = row.get("opening_date", "")
        closing = row.get("closing_date", "")
        location = row.get("location", "-")

        st.markdown(f'<div class="tender-row">', unsafe_allow_html=True)
        st.markdown(f"<div class='tender-title'>Title: <b>{title}</b> </div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='tender-meta'>Reference No.: <b>{ref}</b> <br> Location: <b>{location}</b> <br> Opens: <b> {opening} </b> | Closes: <b> {closing} </b></div>",
            unsafe_allow_html=True,
        )
        if st.button("View Details", key=f"view_{row['tender_id']}"):
            st.session_state["selected_tender_ref"] = ref
            st.session_state["page"] = "tender_details"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


        
###########################
### Tender details page ###
###########################

def show_tender_details():
    ref = st.session_state.get("selected_tender_ref") or st.session_state.get("prefill_tender_ref")
    tender = get_tender_by_ref(ref)
    if not tender:
        st.warning("Tender not selected.")
        st.session_state["page"] = None
        st.rerun()
    st.header(f"Tender Details — {tender['title']}")
    st.markdown("### Basic Details")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Reference No:** {tender['tender_ref_no']}")
        st.write(f"**Location:** {tender['location']}")
        st.write(f"**Tender ID:** {tender['tender_id']}")
    with c2:
        st.write(f"**Opening Date:** {tender['opening_date']}")
        st.write(f"**Closing Date:** {tender['closing_date']}")
        st.write(f"**Published On:** {tender['publishing_date']}")
    st.markdown("---")
    st.markdown("### Description")
    st.write(tender.get("description") or "_No description_")

    st.markdown("---")
    st.markdown("### Place a Bid")
    tech = st.text_area("Technical Specification", key="detail_tech")
    fin = st.text_area("Financial Specification / Quote", key="detail_fin")

    col1, col2, col3 = st.columns([1, 7, 1])
    with col1:
        if st.button("Submit Bid"):
            if not tech.strip() or not fin.strip():
                st.warning("Please fill in both Technical and Financial specifications before submitting.")
            else:
                vendor = get_vendor_by_email(st.session_state.vendor_email)
                ok, msg = submit_bid(vendor["vendor_id"], tender["tender_ref_no"], tech.strip(), fin.strip())
                if ok:
                    create_notification(
                        vendor["vendor_id"],
                        "Bid Submitted",
                        f"Your bid for {tender['tender_ref_no']} was submitted successfully."
                    )
                    st.success(msg)
                    st.session_state["page"] = None
                    st.rerun()
                else:
                    st.error(msg)
    with col2:
        ...
    with col3:
        if st.button("Back to List"):
            st.session_state["page"] = None
            st.rerun()    



######################
### Submit bid tab ###
######################

def submit_bid_tab(vendor):
    st.header("Submit a Bid")
    # prefill if selected
    pre = st.session_state.get("prefill_tender_ref")
    df = get_open_tenders()
    if df.empty:
        st.info("No open tenders.")
        return

    locations = ["All"] + sorted([l for l in get_tenders_locations() if l])
    col1, col2 = st.columns(2)
    with col1:
        loc = st.selectbox("Filter Location", locations, key="submit_loc")
    with col2:
        s = st.text_input("Search", key="submit_search")

    filtered = df.copy()
    if loc != "All":
        filtered = filtered[filtered["location"] == loc]
    if s:
        filtered = filtered[filtered["title"].str.contains(s, case=False, na=False) |
                            filtered["tender_ref_no"].str.contains(s, case=False, na=False)]

    opts = filtered["tender_ref_no"].tolist()
    if pre and pre in opts:
        selected_ref = st.selectbox("Select Tender", opts, index=opts.index(pre))
    else:
        selected_ref = st.selectbox("Select Tender", opts)

    tender = get_tender_by_ref(selected_ref)
    st.write(f"**Title:** {tender['title']}")
    st.write(f"**Closing Date:** {tender['closing_date']}")

    tech = st.text_area("Technical Specification", key="submit_tech")
    fin = st.text_area("Financial Specification / Quote", key="submit_fin")

    if st.button("Submit Bid Now"):
        vendor_obj = get_vendor_by_email(st.session_state.vendor_email)
        ok, msg = submit_bid(vendor_obj["vendor_id"], selected_ref, tech, fin)
        if ok:
            create_notification(vendor_obj["vendor_id"], "Bid Submitted", f"Your bid for {selected_ref} was submitted.")
            st.success(msg)
            # clear prefill
            if "prefill_tender_ref" in st.session_state:
                del st.session_state["prefill_tender_ref"]
            st.rerun()
        else:
            st.error(msg)



##########################
### Submitted Bids tab ###
##########################

def submitted_bids_tab(vendor):
    st.header("Your Submitted Bids")

    df = get_bids_for_vendor(vendor["email"])
    if df.empty:
        st.info("No bids submitted yet.")
        return

    # ---- Filters ----
    locs = ["All"] + sorted(df["location"].dropna().unique().tolist())
    stats = ["All"] + sorted(df["status"].dropna().unique().tolist())

    c1, c2 = st.columns(2)
    with c1:
        loc = st.selectbox("Filter by Location", locs, key="sb_loc")
    with c2:
        status = st.selectbox("Filter by Status", stats, key="sb_status")

    filtered = df.copy()
    if loc != "All":
        filtered = filtered[filtered["location"] == loc]
    if status != "All":
        filtered = filtered[filtered["status"] == status]

    if filtered.empty:
        st.info("No bids found for selected filters.")
        return

    # ---- Display each bid as a block ----
    st.markdown("""
        <style>
            .bid-card {
                border: 1px solid #e6e6e6;
                padding: 0px 0px;
                margin-bottom: 15px;
            } 
            .bid-title {
                margin-top: 15px; 
            }
            .bid-meta {
                margin-bottom: 20px;
            }
            .stButton > button {
                padding: 4px 10px;
                font-size: 0.85rem;
            }
        </style>
    """, unsafe_allow_html=True)

    for i, row in filtered.iterrows():
        tender_ref = row["tender_ref_no"]
        title = row["title"]
        status = row["status"]
        loc = row["location"]
        submitted_on = row["submission_date"]

        st.markdown("<div class='bid-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='bid-title'>Title: <b>{title}</b> </div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='bid-meta'>Tender Reference No.: <b>{tender_ref}</b> <br> Location: {loc} <br> Submitted on: {submitted_on} <br> Status: <b>{status}</b></div>",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([3, 3, 1])

        # Create a unique suffix
        unique_id = f"{row['tender_id']}_{i}"

        with col1:
            if st.button("View Details", key=f"view_{unique_id}"):
                st.session_state["selected_bid"] = row.to_dict()
                st.session_state["page"] = "view_bid"
                st.rerun()

        if status == "Submitted":
            with col2:
                if st.button("Edit Bid", key=f"edit_{unique_id}"):
                    st.session_state["selected_bid"] = row.to_dict()
                    st.session_state["page"] = "edit_bid"
                    st.rerun()
            with col3:
                if st.button("Withdraw Bid", key=f"del_{unique_id}"):
                    vendor_obj = get_vendor_by_email(st.session_state.vendor_email)
                    delete_bid(row["tender_id"], vendor_obj["vendor_id"])
                    create_notification(vendor_obj["vendor_id"], "Bid Withdrawn", f"Your bid for Tender {tender_ref} was withdrawn.")
                    st.success(f"Bid for {tender_ref} withdrawn.")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)



def view_bid_page():
    bid = st.session_state.get("selected_bid")
    if not bid:
        st.warning("No bid selected.")
        st.session_state["page"] = None
        st.rerun()

    st.header(f"Bid Details — {bid['title']}")
    st.write(f"**Tender Ref:** {bid['tender_ref_no']}")
    st.write(f"**Submitted On:** {bid['submission_date']}")
    st.write(f"**Status:** {bid['status']}")
    st.markdown("---")
    st.subheader("Technical Specification")
    st.text(bid["technical_spec"])
    st.subheader("Financial Specification")
    st.text(bid["financial_spec"])

    if st.button("Back"):
        st.session_state["page"] = None
        st.rerun()


def edit_bid_page():
    bid = st.session_state.get("selected_bid")
    if not bid:
        st.warning("No bid selected.")
        st.session_state["page"] = None
        st.rerun()

    st.header(f"Edit Bid — {bid['title']}")
    st.caption("You can edit only while the tender is still open.")

    new_tech = st.text_area("Technical Specification", value=bid["technical_spec"])
    new_fin = st.text_area("Financial Specification / Quote", value=bid["financial_spec"])

    col1, col2, col3 = st.columns([2, 9, 1])
    with col1:
        if st.button("Save Changes"):
            if not new_tech.strip() or not new_fin.strip():
                st.warning("Both fields are required.")
            else:
                vendor_obj = get_vendor_by_email(st.session_state.vendor_email)
                update_bid(vendor_obj["vendor_id"], bid["tender_id"], new_tech.strip(), new_fin.strip())
                create_notification(vendor_obj["vendor_id"], "Bid Updated", f"Your bid for Tender {bid['tender_ref_no']} was updated.")
                st.success("Bid updated successfully.")
                st.session_state["page"] = None
                st.rerun()
    with col2:
        ...
    with col3:
        if st.button("Cancel"):
            st.session_state["page"] = None
            st.rerun()



##########################
### notifications tab  ###
##########################

def inbox_tab(vendor):
    st.header("Inbox")

    rows = get_notifications(vendor["email"])
    if not rows:
        st.info("No notifications.")
        return

    for nid, title, message, ts, is_read in rows:
        with st.container(border=True):
            if not is_read:
                st.markdown(f"**{title}**  | _[Unread Notification]_")
            else:
                st.markdown(f"**{title}**")

            st.caption(f"{ts}")
            st.write(message)

    st.markdown("---")
    if st.button("Mark All as Read"):
        mark_notifications_read(vendor["email"])
        st.rerun()