import streamlit as st
import pandas as pd
import uuid
from datetime import time


def add_booking(CSV_FILE):
    st.subheader("Add New Booking")

    # 🔄 Show success message after rerun
    if st.session_state.get("booking_saved"):
        st.success("✅ Booking Saved Successfully!")
        st.session_state["booking_saved"] = False

    # key for resetting form
    form_key = st.session_state.get("form_key", 0)

    # TABLE & MODE
    table_type = st.selectbox(
        "Select Table",
        ["Pool-1", "Pool-2", "Snooker-1", "Snooker-2"],
        key=f"table_type_{form_key}"
    )

    mode = st.radio(
        "Mode",
        ["Solo", "Team"],
        key=f"mode_{form_key}"
    )

    # PLAYER DETAILS
    st.write("### Player Details")

    if mode == "Solo":
        player1 = st.text_input("Player 1", key=f"player1_{form_key}")
        player2 = st.text_input("Player 2", key=f"player2_{form_key}")
        player3, player4 = "", ""
    else:
        col1, col2 = st.columns(2)
        with col1:
            player1 = st.text_input("Team A - Player 1", key=f"player1_{form_key}")
            player2 = st.text_input("Team A - Player 2", key=f"player2_{form_key}")
        with col2:
            player3 = st.text_input("Team B - Player 1", key=f"player3_{form_key}")
            player4 = st.text_input("Team B - Player 2", key=f"player4_{form_key}")

    # BOOKING DETAILS
    st.write("### Booking Details")

    date = st.date_input("Select Date", key=f"date_{form_key}")

    # -------------------------------
    # ⭐ CUSTOM START TIME PICKER ⭐
    # -------------------------------
    st.write("### Start Time")

    colH, colM, colAP = st.columns([1, 1, 1])

    with colH:
        hour = st.selectbox(
            "Hour",
            [f"{h:02d}" for h in range(1, 13)],
            key=f"hour_{form_key}"
        )

    with colM:
        minute = st.selectbox(
            "Minute",
            [f"{m:02d}" for m in range(0, 60)],
            key=f"minute_{form_key}"
        )

    with colAP:
        am_pm = st.selectbox(
            "AM/PM",
            ["AM", "PM"],
            key=f"ampm_{form_key}"
        )

    # Format final start time string
    start_time_str = f"{hour}:{minute} {am_pm}"
    st.caption(f"Selected Start: {start_time_str}")

    # -------------------------------
    # SAVE BOOKING
    # -------------------------------
    if st.button("Save Booking"):

        if mode == "Solo" and (not player1 or not player2):
            st.error("Player Name Cannot be empty")
            return

        if mode == "Team" and (not player1 or not player2 or not player3 or not player4):
            st.error("Player Name Cannot be empty")
            return

        df = pd.read_csv(CSV_FILE)

        new_row = {
            "booking_id": str(uuid.uuid4()),
            "table_type": table_type,
            "mode": mode,
            "player1": player1,
            "player2": player2,
            "player3": player3,
            "player4": player4,
            "date": str(date),
            "start_time": start_time_str,
            "end_time": "Running...",
            "duration": None,
            "amount": None,
            "remarks": None
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)

        # finalize + reset
        st.session_state["booking_saved"] = True
        st.session_state["form_key"] = form_key + 1
        st.rerun()