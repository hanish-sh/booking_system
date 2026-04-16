import streamlit as st
import pandas as pd


def view_bookings(CSV_FILE):

    st.write("### 🔍 Search Bookings")

    df = pd.read_csv(CSV_FILE)

    # -------------------------
    # DATE RANGE FILTER
    # -------------------------
    date_filter_type = st.radio(
        "Select Date Filter",
        ["Date Range", "All Dates"],
        horizontal=True,
        key="vb_date_filter_type"        # ✅ unique key
    )

    if date_filter_type == "Date Range":
        col1, col2 = st.columns(2)
        date_from = col1.date_input("From Date", key="vb_date_from")   # ✅
        date_to   = col2.date_input("To Date",   key="vb_date_to")     # ✅
    else:
        date_from, date_to = None, None

    # -------------------------
    # Table Filter
    # -------------------------
    search_table = st.selectbox(
        "Filter by Table",
        ["All", "Pool-1", "Pool-2", "Snooker-1", "Snooker-2"],
        key="vb_search_table"            # ✅
    )

    # -------------------------
    # Player Search
    # -------------------------
    search_name = st.text_input("Search by Player Name", key="vb_search_name")  # ✅

    # -------------------------
    # Filtering
    # -------------------------
    filtered_df = df.copy()

    if date_filter_type == "Date Range" and date_from and date_to:
        filtered_df = filtered_df[
            (filtered_df["date"] >= str(date_from)) &
            (filtered_df["date"] <= str(date_to))
        ]

    if search_table != "All":
        filtered_df = filtered_df[filtered_df["table_type"] == search_table]

    if search_name:
        filtered_df = filtered_df[
            filtered_df.apply(
                lambda row: search_name.lower() in (
                    str(row["player1"]).lower() +
                    str(row["player2"]).lower() +
                    str(row["player3"]).lower() +
                    str(row["player4"]).lower()
                ),
                axis=1
            )
        ]

    st.write("### 📘 Booking Results")
    st.dataframe(filtered_df, use_container_width=True)

    # Download button
    booking_csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download Booking CSV",
        booking_csv,
        "booking_report.csv",
        "text/csv",
        key="vb_download_btn"            # ✅
    )
