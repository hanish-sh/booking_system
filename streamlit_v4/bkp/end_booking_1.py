import pandas as pd
import streamlit as st
from datetime import datetime, date as dt_date, timedelta


def end_booking(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    st.subheader("🏁 End Booking")

    if df.empty:
        st.warning("No bookings available.")
        return

    # Only show running (active) bookings
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
    # Booking summary
    # -----------------------
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Table",      selected_row["table_type"])
    col_b.metric("Mode",       selected_row["mode"])
    col_c.metric("Start Time", selected_row["start_time"])

    st.write(f"**Players:** {selected_row['player1']} & {selected_row['player2']}" +
             (f" vs {selected_row['player3']} & {selected_row['player4']}"
              if selected_row["mode"] == "Team" else ""))

    st.divider()

    # -----------------------
    # 3. End Time input
    # -----------------------
    start_time = datetime.strptime(selected_row["start_time"], '%I:%M %p').time()

    colH, colM, colAP = st.columns([1, 1, 1])

    with colH:
        hour = st.selectbox(
            "Hour",
            [f"{h:02d}" for h in range(1, 13)],
            key=f"eb_hour_{selected_id}"  # Added unique ID
        )

    with colM:
        minute = st.selectbox(
            "Minute",
            [f"{m:02d}" for m in range(0, 60)],
            key=f"eb_minute_{selected_id}" # Added unique ID
        )

    with colAP:
        am_pm = st.selectbox(
            "AM/PM",
            ["AM", "PM"],
            key=f"eb_ampm_{selected_id}"  # Added unique ID
        )

    end_time = f"{hour}:{minute} {am_pm}"
    st.caption(f"Selected Start: {end_time}")

    # -----------------------
    # 4. Calculate Duration
    # -----------------------
    # Construct the time string and then convert it to a datetime object for math
    end_time_str = f"{hour}:{minute} {am_pm}"
    # Convert the selected dropdown values into a datetime object
    d_end_time_obj = datetime.strptime(end_time_str, '%I:%M %p').time()

    d_start = datetime.combine(dt_date.today(), start_time)
    d_end = datetime.combine(dt_date.today(), d_end_time_obj)

    # Handle overnight sessions
    if d_end <= d_start:
        d_end += timedelta(days=1)

    duration = d_end - d_start
    hours, remainder = divmod(int(duration.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    final_duration = f"{hours:02}:{minutes:02}"
    final_end_time_str = end_time_str  # It's already a string from your dropdowns

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
            st.session_state["session_ended"]  = False
            st.session_state["nav_page"]       = "Payments"
            st.session_state["selected_payment_booking_id"] = (
                st.session_state["last_ended_booking_id"]
            )
            st.rerun()

    if st.button("🏁 End Session", type="primary", key="endb_end_btn"):
        if end_time == start_time:
            st.error("❌ End time cannot be the same as start time.")
            return

        if final_duration == "N/A":
            st.error("❌ Invalid duration. Check end time.")
            return

        idx = df.index[df["booking_id"] == selected_id]
        df.at[idx[0], "end_time"]  = final_end_time_str
        df.at[idx[0], "duration"]  = final_duration
        df.at[idx[0], "amount"]    = amount
        df.at[idx[0], "remarks"]   = str(remarks)

        df.to_csv(CSV_FILE, index=False)
        st.session_state["session_ended"]        = True
        st.session_state["last_ended_booking_id"] = selected_id
        st.rerun()
