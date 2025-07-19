import streamlit as st
import pandas as pd
from config_import import Config, ConfigKeys
from model import model, Logger, Timer
import matplotlib.pyplot as plt
from typing import Any, Dict, cast
from logger import Logger, Log_Action

def plot_chapter_wins(log_df: pd.DataFrame) -> None:
    

    # Keep only win or loss chapter events
    mask = log_df["action"].isin([Log_Action.WIN_CHAPTER.value, Log_Action.LOSE_CHAPTER.value])
    result_df = log_df.loc[mask].copy()

    if result_df.empty:
        st.info("No chapter win/lose events to display.")
        return

    # Aggregate counts per day and result
    counts = (
        result_df.groupby(["current_day", "action"])
        .size()
        .unstack(fill_value=0)
        .rename(
            columns={
                Log_Action.WIN_CHAPTER.value: "wins",
                Log_Action.LOSE_CHAPTER.value: "losses",
            }
        )
        .sort_index()
    )

    # Ensure both columns exist to stabilise chart when one is missing
    for col in ("wins", "losses"):
        if col not in counts.columns:
            counts[col] = 0

    st.subheader("Chapter Results per Day")
    st.bar_chart(counts)

# ------------------------------------------------------------------
# Manual cache refresh: clears st.cache_data and reruns the script
# ------------------------------------------------------------------
if st.button("Reload config from Google Sheets ↻"):
    st.cache_data.clear()
    st.rerun() 

st.title("Cup Heroes Gear and Chapters Simulator")

config = Config.initialize()

# Display the config to allow editing
st.subheader("Config Editor")
edited_gear_levels_config = st.data_editor(config.gear_levels_df)
edited_gear_merge_config = st.data_editor(config.gear_merge_df)
edited_chapters_config = st.data_editor(config.chapters_df)
edited_gacha_config = st.data_editor(config.gacha_df)
edited_offers_config = st.data_editor(config.offers_df)
edited_players_config = st.data_editor(config.players_df)

# Simulation
if "simulation_done" not in st.session_state:
    st.session_state.simulation_done = False

if st.button("Run Simulation"):

    config.reasign_config(
    new_gear_levels_config=edited_gear_levels_config,
    new_gear_merge_config=edited_gear_merge_config,
    new_chapters_config=edited_chapters_config,
    new_gacha_config=edited_gacha_config,
    new_offers_config=edited_offers_config,
    new_players_config=edited_players_config
    )

    Logger.clear_logs()
    model_instance = model.initialize(config)
    model_instance.simulate()
    st.session_state.simulation_done = True


# Show results
if st.session_state.simulation_done:
    log_df = Logger.get_logs_as_dataframe()

        # Expand the 'time' dict column into separate columns
    if 'time' in log_df.columns:
        time_cols = log_df['time'].apply(pd.Series)
        log_df = pd.concat([log_df.drop(columns=['time']), time_cols], axis=1)

    # ---------- Action filter -------------
    actions_available = sorted(log_df["action"].unique())
    selected_actions = st.multiselect(
        "Filter by action", options=actions_available, default=actions_available
    )
    filtered_df = log_df[log_df["action"].isin(selected_actions)]

    st.dataframe(filtered_df)

    if st.button("Show Graphs"):
        st.subheader("Simulation Logs")
        plot_chapter_wins(log_df)

    
    
    