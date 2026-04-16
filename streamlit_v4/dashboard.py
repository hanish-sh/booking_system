import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import uuid

st.set_page_config(layout="wide", page_title="Snooker Club")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&display=swap');
section.main > div { background: #080c12 !important; }
.stApp { background: #080c12 !important; }
@keyframes pulse-ring {
    0%,100% { box-shadow: 0 0 0 0 rgba(0,255,179,.5); }
    50%      { box-shadow: 0 0 0 5px rgba(0,255,179,.0); }
}
.live-badge { animation: pulse-ring 2s infinite; }
</style>
""", unsafe_allow_html=True)

TABLES = ["Pool-1", "Pool-2", "Snooker-1", "Snooker-2"]


def ini(name: str) -> str:
    parts = str(name).strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return str(name)[:2].upper() if name else "?"


def avatar_row(av, name):
    return (
        "<div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;'>"
        f"<div style='width:26px;height:26px;border-radius:50%;"
        f"background:rgba(0,255,179,.1);border:1px solid rgba(0,255,179,.3);"
        f"display:inline-flex;align-items:center;justify-content:center;"
        f"font-size:10px;font-weight:700;color:#00ffb3;flex-shrink:0;'>{av}</div>"
        f"<span style='font-size:13px;color:#cbd5e1;font-weight:500;'>{name}</span>"
        "</div>"
    )


def vs_bar():
    return (
        "<div style='text-align:center;font-size:10px;color:#2a3550;"
        "letter-spacing:2px;margin:4px 0;font-weight:700;'>— VS —</div>"
    )


def team_label(text):
    return (
        f"<div style='font-size:9px;color:#4a5c78;letter-spacing:1px;"
        f"text-transform:uppercase;margin-bottom:4px;'>{text}</div>"
    )


def time_chip(t):
    return (
        f"<div style='display:inline-flex;align-items:center;gap:5px;"
        f"background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.2);"
        f"border-radius:6px;padding:3px 8px;font-size:11px;color:#f59e0b;"
        f"margin-top:6px;'>&#9201; Since {t}</div>"
    )


def _build_time_options(start_str: str, step_minutes: int = 1):
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


def _calc_duration(start_str: str, end_str: str, booking_date: str):
    try:
        fmt = "%I:%M %p"
        s = datetime.strptime(start_str.strip(), fmt)
        e = datetime.strptime(end_str.strip(), fmt)
        bdate = pd.to_datetime(booking_date).date()
        d_start = datetime.combine(bdate, s.time())
        d_end   = datetime.combine(bdate, e.time())
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


def render_table_card(table, active_row, CSV_FILE):
    is_active = not active_row.empty
    icon      = "🎱" if "Snooker" in table else "🎯"
    safe_key  = table.replace("-", "_").lower()

    bdr   = "#00ffb3" if is_active else "#1e2535"
    shad  = "0 0 22px rgba(0,255,179,.18)" if is_active else "none"

    # Header badge
    if is_active:
        badge = ("<span class='live-badge' style='font-size:9px;font-weight:700;"
                 "letter-spacing:1.2px;padding:3px 9px;border-radius:20px;"
                 "background:rgba(0,255,179,.12);color:#00ffb3;"
                 "border:1px solid #00ffb3;'>&#9679; LIVE</span>")
    else:
        badge = ("<span style='font-size:9px;font-weight:700;letter-spacing:1.2px;"
                 "padding:3px 9px;border-radius:20px;background:rgba(100,116,139,.1);"
                 "color:#64748b;border:1px solid #1e2535;'>FREE</span>")

    header = (
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"padding:10px 14px 8px;'>"
        f"<span style='font-family:Rajdhani,sans-serif;font-size:17px;font-weight:700;"
        f"color:#e2e8f0;letter-spacing:.5px;'>{icon} {table}</span>"
        f"{badge}</div>"
    )

    if is_active:
        img = (
            "<div style='margin:0 12px 8px;border-radius:8px;height:68px;"
            "background:linear-gradient(135deg,#0d3b2e,#0a2a1e);"
            "display:flex;align-items:center;justify-content:center;'>"
            "<span style='font-size:26px;'>🎱</span></div>"
        )
    else:
        img = (
            "<div style='margin:0 12px 8px;border-radius:8px;height:68px;"
            "background:#0b1018;display:flex;align-items:center;justify-content:center;"
            "border:1px dashed #1e2535;'>"
            "<span style='font-family:Rajdhani,sans-serif;font-size:15px;"
            "font-weight:700;color:#1e2d44;letter-spacing:3px;'>IDLE</span></div>"
        )

    body = ""
    if is_active:
        r = active_row.iloc[0]
        av1 = ini(r["player1"])
        av2 = ini(r["player2"])

        if str(r["mode"]) == "Solo":
            players = (
                avatar_row(av1, r["player1"])
                + vs_bar()
                + avatar_row(av2, r["player2"])
            )
        else:
            av3 = ini(r["player3"])
            av4 = ini(r["player4"])
            players = (
                team_label("Team A")
                + avatar_row(av1, r["player1"])
                + avatar_row(av2, r["player2"])
                + vs_bar()
                + team_label("Team B")
                + avatar_row(av3, r["player3"])
                + avatar_row(av4, r["player4"])
            )

        body = (
            "<div style='padding:8px 14px 14px;border-top:1px solid #1a2236;'>"
            + players
            + time_chip(r["start_time"])
            + "</div>"
        )

    card_html = (
        f"<div style='border-radius:14px;overflow:hidden;margin-bottom:6px;"
        f"border:1px solid {bdr};background:#10151f;box-shadow:{shad};'>"
        + header + img + body +
        "</div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # ── End Session inline panel (only for active / LIVE tables) ─────
    if is_active:
        r          = active_row.iloc[0]
        booking_id = r["booking_id"]
        expand_key = f"end_expand_{safe_key}"

        # Toggle button
        col_btn, _ = st.columns([1, 2])
        with col_btn:
            if st.button(
                "🏁 End Session",
                key=f"end_btn_{safe_key}",
                use_container_width=True,
            ):
                st.session_state[expand_key] = not st.session_state.get(expand_key, False)
                st.rerun()

        # Expanded end-session form
        if st.session_state.get(expand_key, False):
            st.markdown(
                "<div style='background:#0d1220;border:1px solid rgba(239,68,68,.35);"
                "border-radius:12px;padding:14px 16px;margin-bottom:10px;'>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='font-size:10px;font-weight:700;color:#f87171;"
                f"letter-spacing:1.4px;text-transform:uppercase;margin-bottom:8px;'>"
                f"&#9888; Ending Session: {table}</p>",
                unsafe_allow_html=True,
            )

            time_options = _build_time_options(str(r["start_time"]), step_minutes=1)
            now_rounded  = datetime.now()
            now_rounded  = now_rounded - timedelta(
                minutes=now_rounded.minute % 5,
                seconds=now_rounded.second,
                microseconds=now_rounded.microsecond,
            )
            suggested   = now_rounded.strftime("%I:%M %p")
            default_idx = time_options.index(suggested) if suggested in time_options else 0

            end_time_str = st.selectbox(
                "End Time",
                time_options,
                index=default_idx,
                key=f"end_time_{safe_key}",
            )

            h, m, _, valid, err_msg = _calc_duration(
                str(r["start_time"]), end_time_str, str(r["date"])
            )

            if not valid:
                st.error(err_msg)
            else:
                hrs_label = f"{h}h {m}m" if h > 0 else f"{m} min"
                st.markdown(
                    f"<div style='background:#0d1a0f;border:1px solid rgba(0,255,179,.2);"
                    f"border-radius:8px;padding:8px 14px;margin:6px 0;"
                    f"display:flex;align-items:center;gap:12px;'>"
                    f"<span style='font-size:18px;'>&#9201;</span>"
                    f"<div style='font-family:Rajdhani,sans-serif;font-size:18px;"
                    f"font-weight:700;color:#00ffb3;'>{hrs_label}</div>"
                    f"<div style='margin-left:auto;font-size:11px;color:#64748b;'>"
                    f"{r['start_time']} &#8594; {end_time_str}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                remarks_val = st.text_input(
                    "Remarks (optional)",
                    key=f"end_remarks_{safe_key}",
                    placeholder="Any notes about this session…",
                )

                dur_str = f"{h:02d}:{m:02d}"

                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button(
                        "✅ Confirm End",
                        key=f"end_confirm_{safe_key}",
                        type="primary",
                        use_container_width=True,
                    ):
                        df_write = pd.read_csv(CSV_FILE)
                        idx = df_write.index[df_write["booking_id"] == booking_id]
                        if len(idx):
                            df_write.at[idx[0], "end_time"] = end_time_str
                            df_write.at[idx[0], "duration"] = dur_str
                            df_write.at[idx[0], "remarks"]  = remarks_val.strip()
                            df_write.to_csv(CSV_FILE, index=False)

                        # Collapse the form, store info for post-end prompt
                        st.session_state[expand_key]                    = False
                        st.session_state["_after_end_booking_id"]       = booking_id
                        st.session_state["_after_end_table"]            = table
                        st.rerun()

                with col_cancel:
                    if st.button(
                        "✖ Cancel",
                        key=f"end_cancel_{safe_key}",
                        use_container_width=True,
                    ):
                        st.session_state[expand_key] = False
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── Post-end: success banner + jump-to-payments offer ────────────
    after_id    = st.session_state.get("_after_end_booking_id")
    after_table = st.session_state.get("_after_end_table")
    if after_id and after_table == table:
        st.success(f"✅ Session ended for **{table}**!")
        col_pay, col_dismiss = st.columns(2)
        with col_pay:
            if st.button("➡️ Go to Payments", key=f"goto_pay_{safe_key}", use_container_width=True):
                st.session_state["nav_page"]                    = "Payments"
                st.session_state["selected_payment_booking_id"] = after_id
                st.session_state.pop("_after_end_booking_id", None)
                st.session_state.pop("_after_end_table", None)
                st.rerun()
        with col_dismiss:
            if st.button("✖ Dismiss", key=f"dismiss_pay_{safe_key}", use_container_width=True):
                st.session_state.pop("_after_end_booking_id", None)
                st.session_state.pop("_after_end_table", None)
                st.rerun()


def section_label(text):
    st.markdown(
        f"<p style='font-size:10px;font-weight:600;color:#4a5c78;"
        f"letter-spacing:1.4px;text-transform:uppercase;margin:10px 0 2px;'>{text}</p>",
        unsafe_allow_html=True
    )


@st.fragment(run_every=10)
def dashboard_page(CSV_FILE):
    df         = pd.read_csv(CSV_FILE)
    df["date"] = pd.to_datetime(df["date"], format="mixed").dt.date
    today      = date.today()

    running_df       = df[(df["date"] == today) & (df["end_time"] == "Running...")]
    active_tables    = running_df["table_type"].unique().tolist()
    available_tables = [t for t in TABLES if t not in active_tables]

    st.markdown(
        "<h2 style='font-family:Rajdhani,sans-serif;color:#e2e8f0;"
        "font-size:28px;margin-bottom:8px;'>🎱 8 Ball Arena</h2>",
        unsafe_allow_html=True
    )

    left, right = st.columns([3, 1], gap="large")

    # ── LEFT: Table Status ───────────────────────────────────
    with left:
        st.markdown(
            "<h3 style='font-family:Rajdhani,sans-serif;color:#94a3b8;"
            "font-size:18px;margin-bottom:12px;'>📊 Table Status</h3>",
            unsafe_allow_html=True
        )
        col_a, col_b = st.columns(2)
        for idx, table in enumerate(TABLES):
            with (col_a if idx % 2 == 0 else col_b):
                render_table_card(
                    table,
                    running_df[running_df["table_type"] == table],
                    CSV_FILE,
                )

    # ── RIGHT: Quick Booking ─────────────────────────────────
    with right:
        st.markdown(
            "<div style='background:#0d1220;border:1px solid #00ffb3;border-radius:16px;"
            "padding:14px 18px 4px;"
            "box-shadow:0 0 30px rgba(0,255,179,.15),inset 0 0 50px rgba(0,255,179,.03);'>"
            "<div style='font-family:Rajdhani,sans-serif;font-size:20px;font-weight:700;"
            "color:#00ffb3;letter-spacing:.6px;margin-bottom:2px;'>&#9889; Quick Booking</div>"
            "</div>",
            unsafe_allow_html=True
        )

        section_label("Date")
        qb_date = st.date_input("", value=date.today(), key="qb_date", label_visibility="collapsed")

        section_label("Start Time")
        colH, colM, colAP = st.columns(3)
        hour   = colH.selectbox("Hr", [f"{h:02d}" for h in range(1, 13)], key="qb_hour", label_visibility="collapsed")
        minute = colM.selectbox("Mn", [f"{m:02d}" for m in range(0, 60)], key="qb_min",  label_visibility="collapsed")
        ampm   = colAP.selectbox("AP", ["AM", "PM"],                       key="qb_ampm", label_visibility="collapsed")
        start_time = f"{hour}:{minute} {ampm}"

        # Table pills
        section_label("Table")
        pills = ""
        for t in TABLES:
            if t in available_tables:
                pills += (
                    f"<span style='padding:5px 12px;border-radius:20px;font-size:11px;"
                    f"font-weight:700;font-family:Rajdhani,sans-serif;"
                    f"background:rgba(0,255,179,.1);border:1px solid rgba(0,255,179,.4);"
                    f"color:#00ffb3;'>&#10003; {t}</span> "
                )
            else:
                pills += (
                    f"<span style='padding:5px 12px;border-radius:20px;font-size:11px;"
                    f"font-weight:700;font-family:Rajdhani,sans-serif;"
                    f"background:rgba(255,77,106,.07);border:1px solid rgba(255,77,106,.3);"
                    f"color:#f87171;opacity:.7;'>&#128308; {t}</span> "
                )
        st.markdown(
            f"<div style='display:flex;flex-wrap:wrap;gap:7px;margin-bottom:6px;'>{pills}</div>",
            unsafe_allow_html=True
        )

        if not available_tables:
            st.warning("⚠️ All tables occupied.")
            table_type = None
        else:
            table_type = st.selectbox("Select Table", available_tables, key="qb_table", label_visibility="collapsed")

        section_label("Mode")
        mode = st.radio("", ["Solo", "Team"], horizontal=True, key="qb_mode", label_visibility="collapsed")

        section_label("Players")
        if mode == "Solo":
            p1 = st.text_input("Player 1", placeholder="Player 1 name", key="qb_p1")
            p2 = st.text_input("Player 2", placeholder="Player 2 name", key="qb_p2")
            p3 = p4 = ""
        else:
            st.markdown("<p style='font-size:11px;color:#4a5c78;margin:2px 0;'>Team A</p>", unsafe_allow_html=True)
            ca1, ca2 = st.columns(2)
            p1 = ca1.text_input("A-P1", placeholder="P1", key="qb_p1")
            p2 = ca2.text_input("A-P2", placeholder="P2", key="qb_p2")
            st.markdown("<p style='font-size:11px;color:#4a5c78;margin:4px 0 2px;'>Team B</p>", unsafe_allow_html=True)
            cb1, cb2 = st.columns(2)
            p3 = cb1.text_input("B-P1", placeholder="P3", key="qb_p3")
            p4 = cb2.text_input("B-P2", placeholder="P4", key="qb_p4")

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("✅ Confirm Booking", use_container_width=True, key="qb_confirm"):
            err = None
            if table_type is None:
                err = "No tables available right now."
            elif mode == "Solo" and (not p1.strip() or not p2.strip()):
                err = "Enter both player names."
            elif mode == "Team" and not all(x.strip() for x in [p1, p2, p3, p4]):
                err = "Enter all four player names."

            if err:
                st.error(err)
            else:
                new_row = {
                    "booking_id": str(uuid.uuid4()),
                    "table_type": table_type,
                    "mode":       mode,
                    "player1":    p1.strip(),
                    "player2":    p2.strip(),
                    "player3":    p3.strip(),
                    "player4":    p4.strip(),
                    "date":       str(qb_date),
                    "start_time": start_time,
                    "end_time":   "Running...",
                    "duration":   None,
                    "amount":     None,
                    "remarks":    None,
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.success("✅ Booking confirmed!")
                st.rerun()
