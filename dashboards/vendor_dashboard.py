import streamlit as st
import sqlite3
import pandas as pd
from database.db_utils import *

for key, default in {
    "vendor_logged_in": False,
    "vendor_email": None,
    "page": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def vendor_login():
    if "vendor_logged_in" not in st.session_state:
        st.session_state.vendor_logged_in = False
    if "vendor_email" not in st.session_state:
        st.session_state.vendor_email = None

    # Show dashboard once logged in
    if st.session_state.vendor_logged_in:
        show_vendor_dashboard()

    # Shoe login and signup tabs if not logged in
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

    if not st.session_state.get("vendor_logged_in"):
        st.warning("Please log in as a vendor to continue.")
        st.stop()

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
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        loc = st.selectbox("Location", loc_options, key="filter_location")
    with col_f2:
        search = st.text_input("Search title / ref", key="filter_search")

    df = get_open_tenders(location=None if loc == "All" else loc, search=search or None)
    if df.empty:
        st.info("No open tenders")
        return

    tenders = df.to_dict(orient="records")

    for idx in range(0, len(tenders), 2):
        left = tenders[idx]
        right = tenders[idx + 1] if idx + 1 < len(tenders) else None

        cols = st.columns([1, 1], gap="small")  # two equal columns

        # LEFT card
        with cols[0]:
            with st.container(border=True):
                st.markdown(f"Title: **{left['title']}**")
                st.markdown(f"Tender Ref: **{left['tender_ref_no']}**")
                st.markdown(f"Location: {left.get('location','-')}")
                st.markdown(f"Opens: **{left.get('opening_date','-')}** • Closes: **{left.get('closing_date','-')}**")
                if st.button("View Details", key=f"view_{left['tender_id']}"):
                    st.session_state["selected_tender_ref"] = left["tender_ref_no"]
                    st.session_state["page"] = "tender_details"
                    st.rerun()

        # RIGHT card (only if exists)
        if right:
            with cols[1]:
                with st.container(border=True):
                    st.markdown(f"Title: **{right['title']}**")
                    st.markdown(f"Ref: **{right['tender_ref_no']}**")
                    st.markdown(f"Location: {right.get('location','-')}")
                    st.markdown(f"Opens: **{right.get('opening_date','-')}** • Closes: **{right.get('closing_date','-')}**")
                    if st.button("View Details", key=f"view_{right['tender_id']}"):
                        st.session_state["selected_tender_ref"] = right["tender_ref_no"]
                        st.session_state["page"] = "tender_details"
                        st.rerun()

        
###########################
### Tender details page ###
###########################

def show_tender_details():
    vendor = get_vendor_by_email(st.session_state.get("vendor_email"))
    if not vendor or not st.session_state.get("vendor_logged_in"):
        st.warning("Please log in as a vendor to continue.")
        st.session_state["page"] = None
        st.rerun()

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
        st.write(f"**Opening Date:** {tender.get('opening_date','-')}")
        st.write(f"**Closing Date:** {tender.get('closing_date','-')}")
        st.write(f"**Published On:** {tender.get('publishing_date','-')}")
    st.markdown("---")
    st.markdown("### Description")
    st.write(tender.get("description") or "_No description_")
    st.markdown("---")

    col1, col2 = st.columns([8, 1])
    with col1:
        st.subheader("Place a Bid")
    with col2:
        if st.button("Back to List", key=f"back_{tender['tender_ref_no']}"):
            st.session_state["page"] = None
            st.rerun()

    ref_key = tender["tender_ref_no"]
    submitted_flag_key = f"bid_submitted_{vendor['vendor_id']}_{ref_key}"

    if st.session_state.get(submitted_flag_key, False):
        st.success("Your bid was submitted successfully.")
        return

    with st.form(key=f"form_bid_{ref_key}"):
        tech = st.text_area("Technical Specification", key=f"detail_tech_{ref_key}")
        fin = st.text_input("Financial Specification / Quote", key=f"detail_fin_{ref_key}")
        submitted = st.form_submit_button("Submit Bid")

    if submitted:
        if not (tech and tech.strip()) or not (fin and fin.strip()):
            st.warning("Please fill in both Technical and Financial specifications before submitting.")
            return

        ok, msg = submit_bid(vendor["vendor_id"], ref_key, tech.strip(), fin.strip())
        if ok:
            st.session_state[submitted_flag_key] = True

            create_notification(
                vendor["vendor_id"],
                "Bid Submitted",
                f"Your bid for {ref_key} was submitted successfully."
            )

            st.success(msg)
            if "prefill_tender_ref" in st.session_state:
                try:
                    del st.session_state["prefill_tender_ref"]
                except KeyError:
                    pass
            st.rerun()
        else:
            st.error(msg)



######################
### Submit bid tab ###
######################

def submit_bid_tab(vendor):
    st.header("Submit a Bid")

    vendor_obj = get_vendor_by_email(st.session_state.get("vendor_email"))
    if not vendor_obj:
        st.warning("Please log in as a vendor to continue.")
        return

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
        filtered = filtered[
            filtered["title"].str.contains(s, case=False, na=False) |
            filtered["tender_ref_no"].str.contains(s, case=False, na=False)
        ]

    opts = filtered["tender_ref_no"].tolist()
    if not opts:
        st.info("No tenders match the filters.")
        return

    if pre and pre in opts:
        selected_ref = st.selectbox("Select Tender", opts, index=opts.index(pre))
    else:
        selected_ref = st.selectbox("Select Tender", opts)

    flag_key = f"bid_submitted_{vendor_obj['vendor_id']}_{selected_ref}"
    if st.session_state.get(flag_key, False):
        st.success("Your bid was submitted successfully.")
        if st.button("OK", key=f"ok_{flag_key}"):
            del st.session_state[flag_key]
            st.rerun()
        return

    tender = get_tender_by_ref(selected_ref)
    st.write(f"**Title:** {tender['title']}")
    st.write(f"**Closing Date:** {tender.get('closing_date','-')}")

    with st.form(key=f"submit_form_{selected_ref}"):
        tech = st.text_area("Technical Specification", key="submit_tech")
        fin = st.text_area("Financial Specification / Quote", key="submit_fin")
        submit_now = st.form_submit_button("Submit Bid Now")

    if not submit_now:
        return

    if not tech or not tech.strip() or not fin or not fin.strip():
        st.warning("Please provide both technical and financial specifications before submitting.")
        return

    ok, msg = submit_bid(vendor_obj["vendor_id"], selected_ref, tech.strip(), fin.strip())
    if ok:
        st.session_state[flag_key] = True

        try:
            create_notification(vendor_obj["vendor_id"], "Bid Submitted", f"Your bid for {selected_ref} was submitted.")
        except Exception:
            pass

        st.rerun()
    else:
        st.error(msg)



##########################
### Submitted Bids tab ###
##########################

def submitted_bids_tab(vendor):
    st.header("Your Submitted Bids")

    df = get_bids_for_vendor(vendor["email"])

    if (df is None) or df.empty:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT l.tender_id, t.tender_ref_no, t.title, t.location,
                       l.submission_date, l.technical_spec, l.financial_spec,
                       l.status, l.remarks, t.status as tender_status, l.is_winner
                FROM BidLog l
                JOIN Tender t ON l.tender_id = t.tender_id
                JOIN Vendor v ON l.vendor_id = v.vendor_id
                WHERE v.email = ?
                ORDER BY l.submission_date DESC
            """, (vendor["email"],))
            rows = cur.fetchall()
            if rows:
                cols = ["tender_id","tender_ref_no","title","location","submission_date",
                        "technical_spec","financial_spec","status","remarks","tender_status","is_winner"]
                df = pd.DataFrame(rows, columns=cols)
                df["record_type"] = "Log"
        finally:
            conn.close()

    if df is None or df.empty:
        st.info("No bids submitted yet.")
        return

    if "record_type" not in df.columns:
        df["record_type"] = "Active"

    active_df = df[df["record_type"] == "Active"].copy()
    closed_df = df[df["record_type"] == "Log"].copy()

    def render_active_cards(source_df):
        if source_df.empty:
            st.info("No active bids.")
            return

        cols = st.columns(2)
        for i, row in source_df.reset_index(drop=True).iterrows():
            c = cols[i % 2]
            with c.container(border=True):
                st.markdown(f"**{row.get('title','-')}**")
                st.caption(f"Ref: {row.get('tender_ref_no','-')}")
                st.caption(f"Location: {row.get('location','-')}")
                sub_date = row.get("submission_date")
                if pd.notna(sub_date):
                    sub_date = str(sub_date).split(" ")[0]  # keep only YYYY-MM-DD
                else:
                    sub_date = "-"
                st.caption(f"Submitted on: {sub_date}")
                st.caption(f"**Bid Status:** {row.get('status','-')}")
                st.caption(f"**Tender Status:** {row.get('tender_status','-')}")
                b1, b2, b3 = st.columns([1.9, 1.8, 1])
                uid = f"{row.get('tender_id')}_{i}"
                with b1:
                    if st.button("View", key=f"view_{uid}"):
                        st.session_state["selected_bid"] = row.to_dict()
                        st.session_state["page"] = "view_bid"
                        st.rerun()
                with b2:
                    if row.get("status") == "Submitted" and st.button("Edit", key=f"edit_{uid}"):
                        st.session_state["selected_bid"] = row.to_dict()
                        st.session_state["page"] = "edit_bid"
                        st.rerun()
                with b3:
                    if row.get("status") == "Submitted" and st.button("Withdraw", key=f"del_{uid}"):
                        vendor_obj = get_vendor_by_email(st.session_state.vendor_email)
                        delete_bid(row["tender_id"], vendor_obj["vendor_id"])
                        create_notification(
                            vendor_obj["vendor_id"],
                            "Bid Withdrawn",
                            f"Your bid for Tender {row.get('tender_ref_no')} was withdrawn."
                        )
                        st.success(f"Bid for {row.get('tender_ref_no')} withdrawn.")
                        st.rerun()
            if (i + 1) % 2 == 0:
                cols = st.columns(2)

    def render_closed_cards(source_df):
        if source_df.empty:
            st.info("No closed/historical bids.")
            return

        cols = st.columns(2)
        for i, row in source_df.reset_index(drop=True).iterrows():
            c = cols[i % 2]
            with c.container(border=True):
                st.markdown(f"**{row.get('title','-')}**")
                st.caption(f"Ref: {row.get('tender_ref_no','-')}")
                st.caption(f"Location: {row.get('location','-')}")
                st.caption(f"Submitted on: {row.get('submission_date','-')}")
                st.caption(f"**Bid Status:** {row.get('status','-')}")
                st.caption(f"**Tender Status:** {row.get('tender_status','-')}")
                iw = str(row.get("is_winner", "No"))
                if iw.lower() in ("yes", "1", "true"):
                    st.markdown(f":green[**You won this tender**]")
                else:
                    st.markdown(f":red[**You did not win this tender**]")
                if st.button("View", key=f"view_closed_{row.get('tender_id')}_{i}"):
                    st.session_state["selected_bid"] = row.to_dict()
                    st.session_state["page"] = "view_bid"
                    st.rerun()
            if (i + 1) % 2 == 0:
                cols = st.columns(2)

    st.subheader("Open / Active Bids")
    render_active_cards(active_df)

    st.markdown("---")
    st.subheader("Closed / Historical Bids")
    render_closed_cards(closed_df)



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
                st.markdown(f"**{title}**   _[Unread Notification]_")
            else:
                st.markdown(f"**{title}**")

            st.caption(f"{ts}")
            st.write(message)

    st.markdown("---")
    if st.button("Mark All as Read"):
        mark_notifications_read(vendor["email"])
        st.rerun()