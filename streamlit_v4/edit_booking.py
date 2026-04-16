import pandas as pd
import streamlit as st
from datetime import datetime

# Keys used for the edit form widgets
_EDIT_KEYS = [
    "eb_hour", "eb_minute", "eb_ampm",
    "eb_table_type", "eb_mode",
    "eb_p1", "eb_p2", "eb_p3", "eb_p4",
    "eb_booking_date", "eb_remarks",
]


def _clear_edit_widgets():
    """Wipe all edit-form widget values."""
    for k in _EDIT_KEYS:
        st.session_state.pop(k, None)


def edit_bookings(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        st.error("CSV file not found.")
        return

    st.subheader("✏️ Edit Booking")

    if df.empty:
        st.warning("No bookings available")
        return

    # ── Step 1: Filter by Date ───────────────────────────────────────
    unique_dates = sorted(pd.to_datetime(df["date"]).dt.date.unique(), reverse=True)
    filter_date = st.selectbox("📅 Step 1: Pick a Date", unique_dates, key="eb_filter_date")
    filtered_df = df[df["date"] == str(filter_date)]

    if filtered_df.empty:
        st.info("No bookings found for this date.")
        return

    st.write(f"### Bookings on {filter_date}")
    st.dataframe(
        filtered_df[[
            "booking_id", "table_type", "mode",
            "player1", "player2", "player3", "player4",
            "date", "start_time", "end_time",
            "duration", "amount", "remarks"
        ]],
        use_container_width=True,
        hide_index=True,
    )

    # ── Step 2: Select Booking ID ────────────────────────────────────
    selected_id = st.selectbox(
        "🆔 Step 2: Choose Booking ID",
        filtered_df["booking_id"].tolist(),
        key="eb_selected_id",
    )

    # ── LOGIC FIX: Sync Session State with Data ──────────────────────
    # If the ID changed, we manually push the CSV values into session_state.
    # This ensures the widgets (which use these keys) show the correct data.
    if st.session_state.get("eb_last_selected_id") != selected_id:
        row = df[df["booking_id"] == selected_id].iloc[0]

        # 1. Basic Fields
        st.session_state["eb_table_type"] = row["table_type"]
        st.session_state["eb_mode"] = row["mode"]
        st.session_state["eb_p1"] = row["player1"]
        st.session_state["eb_p2"] = row["player2"]
        st.session_state["eb_p3"] = row["player3"] if pd.notna(row["player3"]) else ""
        st.session_state["eb_p4"] = row["player4"] if pd.notna(row["player4"]) else ""
        st.session_state["eb_booking_date"] = pd.to_datetime(row["date"]).date()
        st.session_state["eb_remarks"] = row["remarks"] if pd.notna(row["remarks"]) else ""

        # 2. Time Parsing
        try:
            saved_time = datetime.strptime(row["start_time"].strip(), "%I:%M %p")
            st.session_state["eb_hour"] = saved_time.strftime("%I")
            st.session_state["eb_minute"] = saved_time.strftime("%M")
            st.session_state["eb_ampm"] = saved_time.strftime("%p")
        except:
            # Fallback if time format is corrupted
            st.session_state["eb_hour"], st.session_state["eb_minute"], st.session_state["eb_ampm"] = "12", "00", "PM"

        st.session_state["eb_last_selected_id"] = selected_id
        st.rerun()

    st.divider()
    st.write(f"### Edit Details for ID: `{selected_id[:8]}`")

    # ── Widgets (Note: We only pass 'key', no 'value' or 'index') ───
    table_options = ["Pool-1", "Pool-2", "Snooker-1", "Snooker-2"]
    st.selectbox("Table", table_options, key="eb_table_type")

    mode = st.radio("Mode", ["Solo", "Team"], key="eb_mode")

    if mode == "Solo":
        st.text_input("Player 1", key="eb_p1")
        st.text_input("Player 2", key="eb_p2")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Team A - Player 1", key="eb_p1")
            st.text_input("Team A - Player 2", key="eb_p2")
        with col2:
            st.text_input("Team B - Player 1", key="eb_p3")
            st.text_input("Team B - Player 2", key="eb_p4")

    st.date_input("Date", key="eb_booking_date")

    st.write("### Start Time")
    colH, colM, colAP = st.columns(3)
    with colH:
        st.selectbox("Hour", [f"{h:02d}" for h in range(1, 13)], key="eb_hour")
    with colM:
        st.selectbox("Minute", [f"{m:02d}" for m in range(0, 60)], key="eb_minute")
    with colAP:
        st.selectbox("AM/PM", ["AM", "PM"], key="eb_ampm")

    st.text_area("Remarks", key="eb_remarks")

    # ── Success feedback ──
    if st.session_state.get("booking_updated"):
        st.success("✅ Booking Updated!")
        st.session_state["booking_updated"] = False

    # ── Update Button ──
    if st.button("💾 Update Booking", key="eb_update_btn"):
        idx = df.index[df["booking_id"] == selected_id][0]

        # Pull values directly from session_state
        df.at[idx, "table_type"] = st.session_state["eb_table_type"]
        df.at[idx, "mode"] = st.session_state["eb_mode"]
        df.at[idx, "player1"] = st.session_state["eb_p1"]
        df.at[idx, "player2"] = st.session_state["eb_p2"]
        df.at[idx, "player3"] = st.session_state["eb_p3"] if st.session_state["eb_mode"] == "Team" else ""
        df.at[idx, "player4"] = st.session_state["eb_p4"] if st.session_state["eb_mode"] == "Team" else ""
        df.at[idx, "date"] = str(st.session_state["eb_booking_date"])
        df.at[
            idx, "start_time"] = f"{st.session_state['eb_hour']}:{st.session_state['eb_minute']} {st.session_state['eb_ampm']}"
        df.at[idx, "remarks"] = st.session_state["eb_remarks"]

        df.to_csv(CSV_FILE, index=False)
        st.session_state["booking_updated"] = True
        st.rerun()

    # ── Danger Zone ──
    with st.expander("🗑️ Danger Zone"):
        confirm = st.checkbox(f"Confirm delete ID: {selected_id[:8]}", key="eb_delete_confirm")
        if st.button("Delete This Booking", type="primary", disabled=not confirm):
            df = df[df["booking_id"] != selected_id]
            df.to_csv(CSV_FILE, index=False)
            _clear_edit_widgets()
            st.session_state.pop("eb_last_selected_id", None)
            st.rerun()
