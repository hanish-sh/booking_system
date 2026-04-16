import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date


def dashboard_page(CSV_FILE):
    st.title("📊 Dashboard")

    df = pd.read_csv(CSV_FILE)
    df["date"] = pd.to_datetime(df["date"])

    # ====================================================
    # DATE FILTER
    # ====================================================
    st.markdown("### 📅 Filter Bookings by Date")

    col1, col2 = st.columns(2)

    start_date = col1.date_input("From:", value=date.today(), key="db_start_date")  # ✅
    end_date   = col2.date_input("To:",   value=date.today(), key="db_end_date")    # ✅

    mask = (
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    )
    filtered_df = df[mask]

    st.divider()

    # ====================================================
    # SECTION 1: Booking Records
    # ====================================================
    st.markdown("### 📘 Booking Records")

    show_df = filtered_df.copy()
    show_df["status"] = show_df["end_time"].apply(
        lambda x: "Running" if x == "Running..." else "Closed"
    )
    show_df = show_df[["date", "table_type", "start_time", "end_time", "status"]]
    st.dataframe(show_df, use_container_width=True)

    # ====================================================
    # SECTION 2: Table Utilization (Pie Chart)
    # ====================================================
    st.markdown("### 🎱 Table Utilization")

    if len(filtered_df) > 0:
        table_counts = filtered_df["table_type"].value_counts().reset_index()
        table_counts.columns = ["table", "count"]

        fig = px.pie(
            table_counts,
            names="table",
            values="count",
            title="Table Utilization",
            color_discrete_sequence=["#00ffff", "#0099cc", "#00cccc", "#33ffff"]
        )
        fig.update_layout(
            paper_bgcolor="black",
            plot_bgcolor="black",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No bookings found!")

    # ====================================================
    # SECTION 3: Total Entries
    # ====================================================
    st.markdown("### 🔢 Total Entries")
    st.metric("Total Bookings", len(filtered_df))

    # ====================================================
    # SECTION 4: Top Player
    # ====================================================
    st.markdown("### 🏆 Top Player")

    players = []
    for _, row in filtered_df.iterrows():
        players.extend([row["player1"], row["player2"]])
        if row["mode"] == "Team":
            players.extend([row["player3"], row["player4"]])

    if len(players) > 0:
        player_counts = pd.Series(players).value_counts()
        top_player    = player_counts.idxmax()
        count         = player_counts.max()
        st.success(f"🏆 **{top_player}** with **{count} matches**")
    else:
        st.info("No player data in selected dates")

    #time.sleep(1)
    #st.rerun()