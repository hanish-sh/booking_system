import streamlit as st
import pandas as pd


def view_payments():

    PAY_FILE  = "payment_details.csv"
    BOOK_FILE = "table_bookings.csv"

    # -------------------------------------------------
    # Load Payment File
    # -------------------------------------------------
    try:
        pay_df = pd.read_csv(PAY_FILE)
    except FileNotFoundError:
        st.warning("⚠ No payments recorded yet.")
        return

    if pay_df.empty:
        st.warning("⚠ No payment entries found.")
        return

    # Load booking data for date + table info
    df_book = pd.read_csv(BOOK_FILE)

    # -------------------------------------------------
    # Merge booking info into payments (date, table, mode)
    # -------------------------------------------------
    merged = pay_df.merge(
        df_book[["booking_id", "date", "table_type", "mode"]],
        on="booking_id",
        how="left"
    )

    # Drop internal column not meant for display
    if "player_key" in merged.columns:
        merged = merged.drop(columns=["player_key"])

    # Reorder columns for clean display
    display_cols = [
        "date", "booking_id", "table_type", "mode",
        "player_name", "expected_amount", "paid_amount",
        "remaining_amount", "status"
    ]
    display_cols = [c for c in display_cols if c in merged.columns]
    merged = merged[display_cols]

    # -------------------------------------------------
    # DATE FILTER
    # -------------------------------------------------
    st.write("### Filter Payments")

    pay_date_filter = st.radio(
        "Select Date Filter",
        ["Date Range", "All Dates"],
        horizontal=True,
        key="vp_date_filter_type"
    )

    if pay_date_filter == "Date Range":
        col1, col2 = st.columns(2)
        pay_from = col1.date_input("From Date", key="vp_date_from")
        pay_to   = col2.date_input("To Date",   key="vp_date_to")
    else:
        pay_from, pay_to = None, None

    if pay_date_filter == "Date Range" and pay_from and pay_to:
        merged = merged[
            (merged["date"] >= str(pay_from)) &
            (merged["date"] <= str(pay_to))
        ]

    # -------------------------------------------------
    # PLAYER SEARCH
    # -------------------------------------------------
    pay_search = st.text_input("Search by Player Name", key="vp_search_name")

    if pay_search:
        merged = merged[
            merged["player_name"].str.contains(pay_search, case=False, na=False)
        ]

    # -------------------------------------------------
    # PAYMENT TABLE
    # -------------------------------------------------
    st.write("### Payment Entries")

    if merged.empty:
        st.info("No payment records found for the selected filter.")
    else:
        st.dataframe(merged, use_container_width=True, hide_index=True)

    # -------------------------------------------------
    # SUMMARY CARDS
    # -------------------------------------------------
    if len(merged) > 0:
        st.write("### Summary")
        total_expected = merged["expected_amount"].sum()
        total_paid     = merged["paid_amount"].sum()
        total_due      = merged["remaining_amount"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Expected", f"₹ {total_expected:,.2f}")
        col2.metric("Total Paid",     f"₹ {total_paid:,.2f}")
        col3.metric("Total Due",      f"₹ {total_due:,.2f}")

    # -------------------------------------------------
    # DOWNLOAD
    # -------------------------------------------------
    pay_csv = merged.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download Payment CSV",
        pay_csv,
        "payment_report.csv",
        "text/csv",
        key="vp_download_btn"
    )
