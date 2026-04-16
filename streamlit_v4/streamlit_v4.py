import streamlit as st
import pandas as pd
import os

from new_booking import add_booking
from edit_booking import edit_bookings
from view_booking import view_bookings
from view_payments import view_payments
from dashboard import dashboard_page
from payments import payment_section
# end_booking import no longer needed — end-session is embedded in dashboard


st.set_page_config(
    page_title="Snooker Club Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ====================================================
# CUSTOM CSS FOR ACTIVE TAB HIGHLIGHT
# ====================================================
st.markdown("""
    <style>

    /* ----- top level tabs ----- */
    div[data-baseweb="tab"] > button[aria-selected="true"] {
        border-bottom: 3px solid #00FFFF !important;
        background-color: #0A0A0A !important;
        color: #00FFFF !important;
        font-weight: 700 !important;
    }

    div[data-baseweb="tab"] > button[aria-selected="false"] {
        color: #CCCCCC !important;
        background-color: black !important;
    }

    /* ----- sub tabs (inside Booking / View Report) ----- */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom: 3px solid #00FFFF !important;
        color: #00FFFF !important;
        font-weight: bold !important;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="false"] {
        color: #AAAAAA !important;
    }

    </style>
""", unsafe_allow_html=True)

CSV_FILE = "table_bookings.csv"

# -----------------------------------------------------
# Initialize CSV
# -----------------------------------------------------
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=[
        "booking_id",
        "table_type", "mode",
        "player1", "player2", "player3", "player4",
        "date", "start_time", "end_time", "duration",
        "amount", "remarks"
    ])
    df.to_csv(CSV_FILE, index=False)

# -----------------------------------------------------
# Auto Navigate (Go to Payments / Dashboard)
# -----------------------------------------------------
nav_page = st.session_state.get("nav_page")

if nav_page == "Payments":
    booking_id = st.session_state.get("selected_payment_booking_id")
    st.title("Payments")
    payment_section(CSV_FILE, booking_id)
    st.stop()

if nav_page == "Dashboard":
    dashboard_page(CSV_FILE)
    st.stop()

# -----------------------------------------------------
# MAIN TOP TABS
# -----------------------------------------------------
tabs = st.tabs(["Dashboard", "Booking", "Payments"])

# -----------------------------
# TAB 1: Dashboard
# (End Session is embedded inside each live table card)
# -----------------------------
with tabs[0]:
    dashboard_page(CSV_FILE)

# -----------------------------
# TAB 2: BOOKING (SUB-TABS)
# End Booking tab removed — use the Dashboard cards instead
# -----------------------------
with tabs[1]:
    st.subheader("Booking Section")

    book_tab1, book_tab2, book_tab3 = st.tabs([
        "Add Booking",
        "Edit Booking",
        "View Booking",
    ])

    with book_tab1:
        add_booking(CSV_FILE)

    with book_tab2:
        edit_bookings(CSV_FILE)

    with book_tab3:
        view_bookings(CSV_FILE)

# -----------------------------
# TAB 3: PAYMENTS
# -----------------------------
with tabs[2]:
    st.subheader("Payments")
    pay_tab1, pay_tab2 = st.tabs(["Make Payment", "View Payments"])

    with pay_tab1:
        payment_section(CSV_FILE)

    with pay_tab2:
        view_payments()
