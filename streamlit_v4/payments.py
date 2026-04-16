import streamlit as st
import pandas as pd

PAY_FILE = "payment_details.csv"


def _load_pay_df():
    """Return payment CSV as DataFrame, or empty frame if missing."""
    try:
        if pd.io.common.file_exists(PAY_FILE):
            return pd.read_csv(PAY_FILE)
    except Exception:
        pass
    return pd.DataFrame(columns=[
        "booking_id", "player_name", "player_key",
        "expected_amount", "paid_amount",
        "remaining_amount", "status"
    ])


def _prefill_from_saved(booking_id, p_key, pay_df):
    """
    Pre-populate session_state widget values from a previously saved record.
    Matches on (booking_id, player_key) — NOT player_name — so two players
    with the same name (e.g. 'unknown') are always treated as separate rows.
    """
    if pay_df.empty or "player_key" not in pay_df.columns:
        return

    row = pay_df[
        (pay_df["booking_id"] == booking_id) &
        (pay_df["player_key"] == p_key)          # ✅ position-based match
    ]
    if row.empty:
        return

    row = row.iloc[0]

    # Only set if the key isn't already live (avoids overwriting in-progress edits)
    for sk, col in [
        (f"exp_{p_key}",    "expected_amount"),
        (f"paid_{p_key}",   "paid_amount"),
        (f"rem_{p_key}",    "remaining_amount"),
        (f"status_{p_key}", "status"),
    ]:
        if sk not in st.session_state:
            st.session_state[sk] = row[col]

    # Auto-tick the checkbox so the row is included on re-save
    chk_key = f"chk_{p_key}"
    if chk_key not in st.session_state:
        st.session_state[chk_key] = True


def payment_section(CSV_FILE, booking_id=None):
    st.subheader("💰 Payment Section")
    df = pd.read_csv(CSV_FILE)

    # -----------------------
    # 1️⃣ Determine Booking ID
    # -----------------------
    passed_booking_id = st.session_state.get("selected_payment_booking_id")
    if passed_booking_id:
        st.info(f"🔄 Loaded booking from Edit Booking page: {passed_booking_id}")
        booking_id = passed_booking_id
    else:
        completed_df = df[df["end_time"] != "Running..."]
        if completed_df.empty:
            st.warning("No completed bookings available for payment.")
            return

        booking_id = st.selectbox(
            "Select Booking ID",
            completed_df["booking_id"].tolist(),
            key="payment_booking_id_select"
        )

    # -----------------------
    # 2️⃣ Load booking details
    # -----------------------
    booking_rows = df[df["booking_id"] == booking_id]
    if booking_rows.empty:
        st.error("Booking not found.")
        return

    booking = booking_rows.iloc[0]
    st.write("### Booking Info")
    st.write(f"**Table:** {booking['table_type']}")
    st.write(f"**Mode:** {booking['mode']}")
    st.write(f"**Duration:** {booking['duration']}")
    #st.write(f"**Total Amount:** {booking['amount']}")

    total_amount = st.number_input(
        "💵 Total Session Amount (₹)",
        min_value=0.0,
        step=50.0,
        value=float(booking["amount"]) if pd.notna(booking["amount"]) else 0.0,
        key="payment_total_amount"
    )

    mode = booking["mode"]

    # -----------------------
    # 3️⃣ Build team-wise players
    # -----------------------
    players_team_a = [booking["player1"], booking["player2"]]
    players_team_b = (
        [booking["player3"], booking["player4"]] if mode == "Team" else []
    )

    st.divider()

    # Load existing payment data once (for pre-filling on edit)
    pay_df = _load_pay_df()

    # Check whether any saved record exists for this booking
    already_saved = not pay_df[pay_df["booking_id"] == booking_id].empty
    if already_saved:
        st.info("✏️ Previously saved payment found — you can update and re-save.")

    # -----------------------
    # 4️⃣ Sync callback
    # -----------------------
    def sync_payment(p_key):
        exp  = st.session_state.get(f"exp_{p_key}",  0.0)
        paid = st.session_state.get(f"paid_{p_key}", 0.0)

        st.session_state[f"rem_{p_key}"] = max(exp - paid, 0.0)

        if paid == 0:
            st.session_state[f"status_{p_key}"] = "Due"
        elif paid >= exp:
            st.session_state[f"status_{p_key}"] = "Paid"
        else:
            st.session_state[f"status_{p_key}"] = "Partial"

    # -----------------------
    # 5️⃣ Render player row
    # -----------------------
    def render_player_row(player_name, p_key):
        # ✅ Match by p_key (position), never by player_name
        _prefill_from_saved(booking_id, p_key, pay_df)

        col0, col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2, 2])

        with col0:
            selected = st.checkbox("", key=f"chk_{p_key}")

        with col1:
            st.write(player_name)

        with col2:
            expected = st.number_input(
                "Expected",
                min_value=0.0,
                step=10.0,
                key=f"exp_{p_key}",
                on_change=sync_payment,
                args=(p_key,)
            )

        with col3:
            paid = st.number_input(
                "Paid",
                min_value=0.0,
                step=10.0,
                key=f"paid_{p_key}",
                on_change=sync_payment,
                args=(p_key,)
            )

        with col4:
            remaining = st.number_input(
                "Remain",
                min_value=0.0,
                step=10.0,
                key=f"rem_{p_key}"
            )

        with col5:
            status_options = ["Paid", "Due", "Partial"]
            current_status = st.session_state.get(f"status_{p_key}", "Due")
            safe_index = (
                status_options.index(current_status)
                if current_status in status_options
                else 1
            )
            status = st.selectbox(
                "Status",
                status_options,
                index=safe_index,
                key=f"status_{p_key}"
            )

        return selected, expected, paid, remaining, status

    # -----------------------
    # 6️⃣ UI – Team A & B
    # -----------------------
    st.write("### Select Players & Enter Payment Details")

    player_selected = {}
    expected_data   = {}
    paid_data       = {}
    remaining_data  = {}
    status_data     = {}

    st.write("#### 🟦 Team‑A")
    for idx, p in enumerate(players_team_a):
        p_key = f"{booking_id}_A_{idx}"
        sel, exp, paid, rem, status = render_player_row(p, p_key)
        player_selected[p_key] = (p, sel)
        expected_data[p_key]   = exp
        paid_data[p_key]       = paid
        remaining_data[p_key]  = rem
        status_data[p_key]     = status

    if mode == "Team":
        st.write("#### 🟥 Team‑B")
        for idx, p in enumerate(players_team_b):
            p_key = f"{booking_id}_B_{idx}"
            sel, exp, paid, rem, status = render_player_row(p, p_key)
            player_selected[p_key] = (p, sel)
            expected_data[p_key]   = exp
            paid_data[p_key]       = paid
            remaining_data[p_key]  = rem
            status_data[p_key]     = status

    st.divider()

    # -----------------------
    # 7️⃣ Save / Update Payment
    # -----------------------
    btn_label = "💾 Update Payment Details" if already_saved else "💾 Save Payment Details"

    col_save, col_reset = st.columns([3, 1])

    with col_save:
        if st.button(btn_label, key=f"save_payment_{booking_id}", use_container_width=True):
            fresh_pay_df = _load_pay_df()

            # Remove old records for this booking (upsert behaviour)
            fresh_pay_df = fresh_pay_df[fresh_pay_df["booking_id"] != booking_id]

            new_rows = []
            for p_key, (player_name, selected) in player_selected.items():
                if selected:
                    new_rows.append({
                        "booking_id":       booking_id,
                        "player_name":      player_name,
                        "player_key":       p_key,
                        "expected_amount":  expected_data[p_key],
                        "paid_amount":      paid_data[p_key],
                        "remaining_amount": remaining_data[p_key],
                        "status":           status_data[p_key],
                    })

            if not new_rows:
                st.error("❌ No player selected!")
                return

            final_df = pd.concat(
                [fresh_pay_df, pd.DataFrame(new_rows)],
                ignore_index=True
            )
            final_df.to_csv(PAY_FILE, index=False),

            df.loc[df["booking_id"] == booking_id, "amount"] = total_amount
            df.to_csv(CSV_FILE, index=False)

            st.success("✅ Payment details saved successfully!")

            # Clear the cross-page handoff key
            st.session_state.pop("selected_payment_booking_id", None)
            st.session_state.pop("nav_page", None)
            # Clear pre-fill cache so next open re-reads fresh from disk
            for p_key in player_selected:
                for prefix in ("exp_", "paid_", "rem_", "status_", "chk_"):
                    st.session_state.pop(f"{prefix}{p_key}", None)

    # with col_reset:
    #     if st.button("🔄 Reset", key=f"reset_payment_{booking_id}", use_container_width=True, type="secondary"):
    #         # Clear all widget session state for this booking
    #         for p_key in player_selected:
    #             for prefix in ("exp_", "paid_", "rem_", "status_", "chk_"):
    #                 st.session_state.pop(f"{prefix}{p_key}", None)
    #
    #         # Also delete saved records from CSV for this booking
    #         fresh_pay_df = _load_pay_df()
    #         if not fresh_pay_df.empty:
    #             fresh_pay_df = fresh_pay_df[fresh_pay_df["booking_id"] != booking_id]
    #             fresh_pay_df.to_csv(PAY_FILE, index=False)
    #
    #         st.session_state.pop("selected_payment_booking_id", None)
    #         st.success("🔄 Payment data reset successfully!")
    #         st.rerun()

    with col_reset:
        if st.button(
                "🔄 Reset",
                key=f"reset_payment_{booking_id}",
                use_container_width=True,
                type="secondary",
        ):
            # 1️⃣ Remove all widget-related session state
            keys_to_clear = []

            for p_key in player_selected:
                keys_to_clear.extend([
                    f"exp_{p_key}",
                    f"paid_{p_key}",
                    f"rem_{p_key}",
                    f"status_{p_key}",
                    f"chk_{p_key}",
                ])

            for k in keys_to_clear:
                st.session_state.pop(k, None)

            # 2️⃣ Remove saved payment records for this booking
            fresh_pay_df = _load_pay_df()
            if not fresh_pay_df.empty:
                fresh_pay_df = fresh_pay_df[
                    fresh_pay_df["booking_id"] != booking_id
                    ]
                fresh_pay_df.to_csv(PAY_FILE, index=False)

            # 3️⃣ Clear cross‑page booking selection
            st.session_state.pop("selected_payment_booking_id", None)
            st.session_state.pop("nav_page", None)

            st.success("🔄 Payment data reset successfully!")

            # ✅ 4️⃣ HARD REFRESH → this clears the boxes visually
            st.rerun()