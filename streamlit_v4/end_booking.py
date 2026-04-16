import pandas as pd
import streamlit as st
from datetime import datetime, date as dt_date, timedelta


# ── helpers ──────────────────────────────────────────────────────────────────

def _card(html: str):
    """Render a dark neon card via markdown (single-quote safe)."""
    st.markdown(html, unsafe_allow_html=True)


def _section(text: str):
    st.markdown(
        f"<p style='font-size:10px;font-weight:700;color:#4a5c78;"
        f"letter-spacing:1.4px;text-transform:uppercase;margin:14px 0 4px;'>{text}</p>",
        unsafe_allow_html=True,
    )


def _stat_box(label: str, value: str, accent: str = "#00ffb3"):
    return (
        f"<div style='flex:1;background:#10151f;border:1px solid #1e2535;"
        f"border-radius:10px;padding:10px 14px;min-width:80px;'>"
        f"<div style='font-size:9px;font-weight:700;color:#4a5c78;"
        f"letter-spacing:1.2px;text-transform:uppercase;margin-bottom:4px;'>{label}</div>"
        f"<div style='font-size:16px;font-weight:700;font-family:Rajdhani,sans-serif;"
        f"color:{accent};'>{value}</div>"
        f"</div>"
    )


def _player_chip(name: str):
    av = (name[0].upper() + name.split()[-1][0].upper()) if len(name.split()) > 1 else name[:2].upper()
    return (
        f"<span style='display:inline-flex;align-items:center;gap:6px;"
        f"background:rgba(0,255,179,.07);border:1px solid rgba(0,255,179,.25);"
        f"border-radius:20px;padding:4px 10px 4px 6px;margin:3px;'>"
        f"<span style='width:20px;height:20px;border-radius:50%;"
        f"background:rgba(0,255,179,.15);border:1px solid rgba(0,255,179,.4);"
        f"display:inline-flex;align-items:center;justify-content:center;"
        f"font-size:8px;font-weight:700;color:#00ffb3;'>{av}</span>"
        f"<span style='font-size:12px;color:#cbd5e1;font-weight:500;'>{name}</span>"
        f"</span>"
    )


def _calc_duration(start_str: str, end_str: str, booking_date: str):
    """
    Safely calculate duration handling overnight sessions.
    Returns (hours, minutes, total_minutes, is_valid, error_msg).
    """
    try:
        fmt = "%I:%M %p"
        s = datetime.strptime(start_str.strip(), fmt)
        e = datetime.strptime(end_str.strip(), fmt)

        bdate = pd.to_datetime(booking_date).date()
        d_start = datetime.combine(bdate, s.time())
        d_end   = datetime.combine(bdate, e.time())

        # Handle overnight: if end <= start, assume next day
        if d_end <= d_start:
            d_end += timedelta(days=1)

        total_secs = int((d_end - d_start).total_seconds())
        if total_secs <= 0:
            return 0, 0, 0, False, "End time must be after start time."

        hours, rem = divmod(total_secs, 3600)
        mins, _    = divmod(rem, 60)
        return hours, mins, total_secs // 60, True, ""

    except Exception as ex:
        return 0, 0, 0, False, str(ex)


def _build_time_options(start_str: str, step_minutes: int = 5):
    """
    Return list of time strings starting from start_time + step
    up to 24 hours ahead, in step_minutes increments.
    """
    fmt = "%I:%M %p"
    try:
        base = datetime.strptime(start_str.strip(), fmt)
    except Exception:
        base = datetime.now().replace(second=0, microsecond=0)

    options = []
    t = base + timedelta(minutes=step_minutes)
    for _ in range((24 * 60) // step_minutes):
        options.append(t.strftime(fmt))
        t += timedelta(minutes=step_minutes)
    return options


def _friendly_label(row) -> str:
    """Human-readable label for a booking row shown in selectbox."""
    players = f"{row['player1']} & {row['player2']}"
    if str(row.get("mode", "")) == "Team":
        players += f" vs {row['player3']} & {row['player4']}"
    return f"{row['table_type']} — {players} @ {row['start_time']}"


# ── main function ─────────────────────────────────────────────────────────────

def end_booking(CSV_FILE: str):

    # ── global styles (injected once) ────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&display=swap');
    @keyframes pulse-ring {
        0%,100%{box-shadow:0 0 0 0 rgba(0,255,179,.5);}
        50%{box-shadow:0 0 0 6px rgba(0,255,179,0);}
    }
    .live-dot { animation: pulse-ring 2s infinite; }
    </style>
    """, unsafe_allow_html=True)

    # ── page title ────────────────────────────────────────────
    st.markdown(
        "<h2 style='font-family:Rajdhani,sans-serif;color:#e2e8f0;"
        "font-size:26px;margin-bottom:4px;'>🏁 End Booking</h2>",
        unsafe_allow_html=True,
    )

    # ── load data ─────────────────────────────────────────────
    df = pd.read_csv(CSV_FILE)

    if df.empty:
        st.warning("No bookings found.")
        return

    running_df = df[df["end_time"] == "Running..."].copy()
    if running_df.empty:
        _card(
            "<div style='background:#0d1a0f;border:1px solid #1a4028;"
            "border-radius:12px;padding:16px 20px;color:#4ade80;"
            "font-family:Rajdhani,sans-serif;font-size:16px;font-weight:700;'>"
            "&#10003; All tables are free — no active sessions running.</div>"
        )
        return

    # ── STEP 1 — pick date ────────────────────────────────────
    _section("Step 1 — Filter by Date")

    unique_dates = sorted(
        pd.to_datetime(running_df["date"]).dt.date.unique(),
        reverse=True,
    )
    filter_date = st.selectbox(
        "Date",
        unique_dates,
        format_func=lambda d: d.strftime("%d %b %Y  (%A)"),
        key="endb_date",
        label_visibility="collapsed",
    )

    day_df = running_df[
        pd.to_datetime(running_df["date"]).dt.date == filter_date
    ].copy()

    if day_df.empty:
        st.info("No active sessions on this date.")
        return

    # Active sessions summary bar
    count = len(day_df)
    tables_live = ", ".join(day_df["table_type"].tolist())
    _card(
        f"<div style='background:#0d1220;border:1px solid #1e2535;"
        f"border-radius:10px;padding:10px 16px;margin:6px 0 2px;"
        f"display:flex;align-items:center;gap:12px;'>"
        f"<span class='live-dot' style='width:10px;height:10px;border-radius:50%;"
        f"background:#00ffb3;display:inline-block;'></span>"
        f"<span style='font-size:13px;color:#94a3b8;'>"
        f"<b style='color:#e2e8f0;'>{count}</b> active session{'s' if count>1 else ''} — "
        f"<span style='color:#00ffb3;'>{tables_live}</span></span></div>"
    )

    # ── STEP 2 — pick booking ─────────────────────────────────
    _section("Step 2 — Select Session to End")

    label_map = {row["booking_id"]: _friendly_label(row) for _, row in day_df.iterrows()}
    ids       = list(label_map.keys())

    selected_id = st.selectbox(
        "Session",
        ids,
        format_func=lambda bid: label_map[bid],
        key="endb_booking_id",
        label_visibility="collapsed",
    )

    row = df[df["booking_id"] == selected_id].iloc[0]

    # Session summary card
    icon = "🎱" if "Snooker" in str(row["table_type"]) else "🎯"
    stats_html = (
        "<div style='display:flex;gap:10px;flex-wrap:wrap;margin:10px 0;'>"
        + _stat_box("Table", f"{icon} {row['table_type']}")
        + _stat_box("Mode", str(row["mode"]), "#818cf8")
        + _stat_box("Started", str(row["start_time"]), "#f59e0b")
        + "</div>"
    )

    players_html = "".join(
        _player_chip(str(row[f"player{i}"]))
        for i in range(1, 5)
        if pd.notna(row.get(f"player{i}")) and str(row.get(f"player{i}", "")).strip()
    )

    _card(
        "<div style='background:#0d1220;border:1px solid #1e2535;"
        "border-radius:12px;padding:14px 18px;margin:6px 0;'>"
        + stats_html
        + "<div style='margin-top:2px;'>" + players_html + "</div>"
        + "</div>"
    )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── STEP 3 — end time (5-min steps + live duration) ──────
    _section("Step 3 — Set End Time")

    time_options = _build_time_options(str(row["start_time"]), step_minutes=1)

    # Suggest current time rounded to nearest 5 min
    now_rounded = datetime.now()
    now_rounded = now_rounded - timedelta(
        minutes=now_rounded.minute % 5,
        seconds=now_rounded.second,
        microseconds=now_rounded.microsecond,
    )
    suggested = now_rounded.strftime("%I:%M %p")
    default_idx = time_options.index(suggested) if suggested in time_options else 0

    end_time_str = st.selectbox(
        "End Time",
        time_options,
        index=default_idx,
        key=f"endb_end_{selected_id}",
        label_visibility="collapsed",
    )

    # Live duration preview
    h, m, total_mins, valid, err_msg = _calc_duration(
        str(row["start_time"]), end_time_str, str(row["date"])
    )

    if not valid:
        _card(
            f"<div style='background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.3);"
            f"border-radius:8px;padding:10px 14px;color:#f87171;font-size:13px;'>"
            f"&#9888; {err_msg}</div>"
        )
        return
    else:
        dur_str = f"{h:02d}:{m:02d}"
        hrs_label = f"{h}h {m}m" if h > 0 else f"{m} min"
        _card(
            f"<div style='background:#0d1a0f;border:1px solid rgba(0,255,179,.2);"
            f"border-radius:8px;padding:10px 16px;display:flex;align-items:center;gap:14px;'>"
            f"<span style='font-size:22px;'>&#9201;</span>"
            f"<div>"
            f"<div style='font-size:9px;color:#4a5c78;letter-spacing:1.2px;"
            f"text-transform:uppercase;margin-bottom:2px;'>Session Duration</div>"
            f"<div style='font-family:Rajdhani,sans-serif;font-size:22px;"
            f"font-weight:700;color:#00ffb3;'>{hrs_label}</div>"
            f"</div>"
            f"<div style='margin-left:auto;font-size:12px;color:#64748b;'>"
            f"{row['start_time']} &#8594; {end_time_str}</div>"
            f"</div>"
        )

    # ── STEP 4 — remarks (Amount Removed) ─────────────────────────────
    _section("Step 4 — Final Remarks")

    existing_rem = str(row["remarks"]) if pd.notna(row.get("remarks")) else ""
    remarks = st.text_area(
        "Remarks (optional)",
        value=existing_rem,
        height=80,
        key="endb_remarks",
        placeholder="Any notes about this session...",
        label_visibility="collapsed"
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── STEP 5 — confirmation gate ────────────────────────────
    confirm_key = f"endb_confirmed_{selected_id}"
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    if not st.session_state[confirm_key]:
        # Show preview summary before final action
        _card(
            "<div style='background:#12100a;border:1px solid rgba(245,158,11,.25);"
            "border-radius:10px;padding:12px 16px;margin-bottom:10px;'>"
            "<div style='font-size:10px;font-weight:700;color:#f59e0b;"
            "letter-spacing:1.2px;text-transform:uppercase;margin-bottom:8px;'>"
            "&#9888; Confirm Before Ending</div>"
            f"<div style='font-size:13px;color:#94a3b8;line-height:1.8;'>"
            f"Table: <b style='color:#e2e8f0;'>{row['table_type']}</b> &nbsp;|&nbsp; "
            f"Duration: <b style='color:#00ffb3;'>{hrs_label}</b>"
            f"</div></div>"
        )

        col_cancel, col_confirm = st.columns(2)
        with col_confirm:
            if st.button(
                "🏁 End Session", type="primary",
                use_container_width=True, key="endb_confirm_btn"
            ):
                st.session_state[confirm_key] = True
                # Set the ID early to ensure it survives the rerun
                st.session_state["selected_payment_booking_id"] = selected_id
                st.rerun()
        with col_cancel:
            st.button(
                "✖ Cancel", use_container_width=True,
                key="endb_cancel_btn"
            )

    else:
        # ── FINAL WRITE ───────────────────────────────────────
        idx = df.index[df["booking_id"] == selected_id]
        if len(idx) == 0:
            st.error("Booking not found. Please refresh.")
            st.session_state[confirm_key] = False
            return

        df.at[idx[0], "end_time"]  = end_time_str
        df.at[idx[0], "duration"]  = dur_str
        df.at[idx[0], "remarks"]   = remarks.strip()

        df.to_csv(CSV_FILE, index=False)

        # Clear confirmation state
        st.session_state[confirm_key] = False

        # Success banner
        _card(
            "<div style='background:#0d1a0f;border:1px solid #00ffb3;"
            "border-radius:12px;padding:16px 20px;margin-bottom:12px;'>"
            "<div style='font-family:Rajdhani,sans-serif;font-size:18px;"
            "font-weight:700;color:#00ffb3;margin-bottom:4px;'>"
            "&#10003; Session Ended Successfully!</div>"
            f"<div style='font-size:13px;color:#94a3b8;'>"
            f"{row['table_type']} &mdash; {hrs_label}</div>"
            "</div>"
        )

        # Offer jump to payment page
        st.info("Record payment details for this booking?")
        if st.button("➡️ Go to Payments", key="endb_goto_pay"):
            st.session_state["nav_page"]                    = "Payments"
            st.session_state["selected_payment_booking_id"] = selected_id
            st.rerun()