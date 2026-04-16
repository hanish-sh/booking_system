import streamlit as st
import pandas as pd
from datetime import date
import uuid

st.markdown(
    """
    <style>
    /* ── Neon Gaming Quick Booking Container ── */
    .quick-booking-box {
        background: #0f1117;
        border: 1px solid #00ffb3;
        border-radius: 16px;
        padding: 22px 20px;
        box-shadow: 0 0 28px rgba(0,255,179,0.20),
                    inset 0 0 50px rgba(0,255,179,0.03);
    }

    /* Section title inside box */
    .quick-booking-box h3 {
        color: #00ffb3 !important;
        letter-spacing: 0.5px;
        margin-bottom: 16px;
    }

    /* All labels inside the box */
    .quick-booking-box .stDateInput label,
    .quick-booking-box .stSelectbox label,
    .quick-booking-box .stTextInput label,
    .quick-booking-box .stRadio label,
    .quick-booking-box p,
    .quick-booking-box span {
        color: #a0aec0 !important;
        font-size: 13px !important;
    }

    /* Inputs, selects */
    .quick-booking-box input,
    .quick-booking-box select,
    .quick-booking-box textarea {
        background: #181d27 !important;
        border: 1px solid #2a3042 !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
    }
    .quick-booking-box input:focus,
    .quick-booking-box select:focus {
        border-color: #00ffb3 !important;
        box-shadow: 0 0 0 2px rgba(0,255,179,0.15) !important;
    }

    /* Confirm button — neon green */
    .quick-booking-box .stButton > button {
        background: linear-gradient(135deg, #00ffb3, #00c896) !important;
        color: #0a0f14 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        letter-spacing: 0.4px;
        transition: opacity 0.2s, transform 0.1s !important;
    }
    .quick-booking-box .stButton > button:hover {
        opacity: 0.88 !important;
        transform: scale(1.01);
    }
    .quick-booking-box .stButton > button:active {
        transform: scale(0.97) !important;
    }

    /* Available / Occupied tag pills */
    .table-tag-available {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        background: rgba(0,255,179,0.12);
        border: 1px solid #00ffb3;
        color: #00ffb3;
        font-size: 11px;
        font-weight: 600;
        margin-left: 6px;
    }
    .table-tag-occupied {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        background: rgba(255,77,106,0.10);
        border: 1px solid #ff4d6a;
        color: #ff4d6a;
        font-size: 11px;
        font-weight: 600;
        margin-left: 6px;
    }

    /* Radio buttons */
    .quick-booking-box .stRadio > div {
        gap: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

TABLES = ["Pool-1", "Pool-2", "Snooker-1", "Snooker-2"]


@st.fragment(run_every=10)
def dashboard_page(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    df["date"] = pd.to_datetime(df["date"], format="mixed").dt.date

    today = date.today()

    running_df = df[
        (df["date"] == today) &
        (df["end_time"] == "Running...")
    ]
    active_tables = running_df["table_type"].unique().tolist()
    available_tables = [t for t in TABLES if t not in active_tables]

    st.markdown("## 🎱 Snooker Club Dashboard")

    left, right = st.columns([3, 1], gap="large")

    # =====================================================
    # LEFT SIDE — TABLE STATUS
    # =====================================================
    with left:
        st.markdown("### 📊 Table Status")

        cols = st.columns(2)
        for idx, table in enumerate(TABLES):
            col = cols[idx % 2]
            active_row = running_df[running_df["table_type"] == table]

            with col:
                st.image("assets/snooker_table.png", use_container_width=True)

                if not active_row.empty:
                    r = active_row.iloc[0]

                    if r["mode"] == "Solo":
                        players_display = f"{r['player1']} & {r['player2']}"
                    else:
                        players_display = (
                            f"{r['player1']} & {r['player2']}<br>"
                            f"{r['player3']} & {r['player4']}"
                        )

                    st.markdown(
                        f"""
                        <div title="Start Time: {r['start_time']}">
                            🟢 <b>{table}</b><br>
                            <span style="color:lime">ACTIVE</span><br>
                            {players_display}<br>
                            <small>{r['start_time']}</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div title="Available">
                            ⚪ <b>{table}</b><br>
                            <span style="color:#aaa">AVAILABLE</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # =====================================================
    # RIGHT SIDE — QUICK BOOKING  (fixed: outside left block)
    # =====================================================
    with right:
        st.markdown('<div class="quick-booking-box">', unsafe_allow_html=True)

        st.markdown("### ⚡ Quick Booking")

        qb_date = st.date_input("Date", value=date.today(), key="qb_date")

        st.markdown("**Start Time**")
        colH, colM, colAP = st.columns(3)
        hour   = colH.selectbox("Hour",  [f"{h:02d}" for h in range(1, 13)], key="qb_hour")
        minute = colM.selectbox("Minute", [f"{m:02d}" for m in range(0, 60)], key="qb_min")
        ampm   = colAP.selectbox("AM/PM", ["AM", "PM"], key="qb_ampm")
        start_time = f"{hour}:{minute} {ampm}"

        # Table selector with available/occupied tags
        if not available_tables:
            st.markdown(
                '<span class="table-tag-occupied">⚠️ All tables occupied</span>',
                unsafe_allow_html=True
            )
            table_type = None
        else:
            # Show availability legend
            legend_html = ""
            for t in TABLES:
                tag_class = "table-tag-available" if t in available_tables else "table-tag-occupied"
                tag_text  = "Free" if t in available_tables else "Busy"
                legend_html += f'<span class="{tag_class}">{t} {tag_text}</span> '
            st.markdown(legend_html, unsafe_allow_html=True)

            table_type = st.selectbox("Table", available_tables, key="qb_table")

        mode = st.radio("Mode", ["Solo", "Team"], horizontal=True, key="qb_mode")

        if mode == "Solo":
            p1 = st.text_input("Player 1", key="qb_p1")
            p2 = st.text_input("Player 2", key="qb_p2")
            p3, p4 = "", ""
        else:
            col1, col2 = st.columns(2)
            with col1:
                p1 = st.text_input("Team A - P1", key="qb_p1")
                p2 = st.text_input("Team A - P2", key="qb_p2")
            with col2:
                p3 = st.text_input("Team B - P1", key="qb_p3")
                p4 = st.text_input("Team B - P2", key="qb_p4")

        if st.button("✅ Confirm Booking", use_container_width=True):
            if table_type is None:
                st.error("No tables available right now.")
                return
            if mode == "Solo" and (not p1 or not p2):
                st.error("Both player names are required.")
                return
            if mode == "Team" and (not p1 or not p2 or not p3 or not p4):
                st.error("All four player names are required.")
                return

            new_row = {
                "booking_id": str(uuid.uuid4()),
                "table_type": table_type,
                "mode":       mode,
                "player1":    p1,
                "player2":    p2,
                "player3":    p3,
                "player4":    p4,
                "date":       str(qb_date),
                "start_time": start_time,
                "end_time":   "Running...",
                "duration":   None,
                "amount":     None,
                "remarks":    None,
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)

            st.success("✅ Booking Created Successfully!")
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
