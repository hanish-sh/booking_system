import pandas as pd
import streamlit as st
from datetime import datetime, date as dt_date, timedelta


def end_booking(CSV_FILE):
    df = pd.read_csv(CSV_FILE)

    st.subheader("🏁 End Booking")

    if df.empty:
        st.warning("No bookings available.")
        return

    # Only running bookings
    running_df = df[df["end_time"] == "Running..."]
    if running_df.empty:
        st.info("✅ No active (running) bookings to end.")
        return

    # -----------------------
    # 1. Filter by Date
    # -----------------------
    unique_dates = sorted(
        pd.to_datetime(running_df["date"]).dt.date.unique(),
        reverse=True
    )

    filter_date = st.selectbox(
        "📅 Step 1: Pick a Date",
        unique_dates,
        key="endb_filter_date"
    )

    filtered_df = running_df[running_df["date"] == str(filter_date)]

    if filtered_df.empty:
        st.info("No active bookings found for this date.")
        return

    st.write(f"### Active Bookings on {filter_date}")

    st.dataframe(
        filtered_df[[
            "booking_id", "table_type", "mode",
            "player1", "player2", "player3", "player4",
            "date", "start_time", "end_time"
        ]],
        use_container_width=True,
        hide_index=True
    )

    # -----------------------
    # 2. Select Booking ID
    # -----------------------
    selected_id = st.selectbox(
        "🆔 Step 2: Choose Booking to End",
        filtered_df["booking_id"].tolist(),
        key="endb_selected_id"
    )

    selected_row = df[df["booking_id"] == selected_id].iloc[0]

    st.divider()
    st.write(f"### End Session for ID: `{selected_id[:8]}`")

    # -----------------------
    # Booking Summary
    # -----------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Table", selected_row["table_type"])
    col2.metric("Mode", selected_row["mode"])
    col3.metric("Start Time", selected_row["start_time"])

    st.write(
        f"**Players:** {selected_row['player1']} & {selected_row['player2']}" +
        (
            f" vs {selected_row['player3']} & {selected_row['player4']}"
            if selected_row["mode"] == "Team" else ""
        )
    )

    st.divider()

    # -----------------------
    # 3. End Time (RESTRICTED)
    # -----------------------
    start_dt = datetime.strptime(selected_row["start_time"], "%I:%M %p")

    allowed_times = []
    current_time = start_dt
    end_of_day = start_dt.replace(hour=23, minute=59)

    while current_time <= end_of_day:
        allowed_times.append(current_time.strftime("%I:%M %p"))
        current_time += timedelta(minutes=1)  # 5‑min steps

    end_time_str = st.selectbox(
        "🕐 End Time",
        allowed_times,
        key=f"endb_end_time_{selected_id}"
    )

    st.caption(f"Selected End: {end_time_str}")

    # -----------------------
    # 4. Calculate Duration
    # -----------------------
    end_dt = datetime.strptime(end_time_str, "%I:%M %p")

    d_start = datetime.combine(dt_date.today(), start_dt.time())
    d_end = datetime.combine(dt_date.today(), end_dt.time())

    duration = d_end - d_start

    hours, remainder = divmod(int(duration.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    final_duration = f"{hours:02}:{minutes:02}"
    final_end_time_str = end_time_str

    st.success(f"⏱ Duration: **{final_duration}**")

    # -----------------------
    # 5. Amount
    # -----------------------
    existing_amount = (
        float(selected_row["amount"])
        if pd.notna(selected_row["amount"])
        else 0.0
    )

    amount = st.number_input(
        "💰 Amount (₹)",
        value=existing_amount,
        min_value=0.0,
        step=50.0,
        key="endb_amount"
    )

    # -----------------------
    # 6. Remarks
    # -----------------------
    remarks = st.text_area(
        "Remarks",
        selected_row["remarks"] if pd.notna(selected_row["remarks"]) else "",
        key="endb_remarks"
    )

    st.divider()

    # -----------------------
    # 7. End Session Button
    # -----------------------
    if st.session_state.get("session_ended"):
        st.success("✅ Session Ended Successfully!")
        st.info("Do you want to add payment details for this booking?")

        if st.button("➡️ Go to Payment Page", key="endb_goto_payment"):
            st.session_state["session_ended"] = False
            st.session_state["nav_page"] = "Payments"
            st.session_state["selected_payment_booking_id"] = (
                st.session_state["last_ended_booking_id"]
            )
            st.rerun()

    if st.button("🏁 End Session", type="primary", key="endb_end_btn"):
        idx = df.index[df["booking_id"] == selected_id]

        df.at[idx[0], "end_time"] = final_end_time_str
        df.at[idx[0], "duration"] = final_duration
        df.at[idx[0], "amount"] = amount
        df.at[idx[0], "remarks"] = str(remarks)

        df.to_csv(CSV_FILE, index=False)

        st.session_state["session_ended"] = True
        st.session_state["last_ended_booking_id"] = selected_id
        st.rerun()