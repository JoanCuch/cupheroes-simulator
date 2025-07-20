import streamlit as st
import pandas as pd
from config_import import Config, ConfigKeys
from model import model, Logger, Timer
from typing import Any, Dict, cast
from logger import Logger, Log_Action



def filtered_log(log_df: pd.DataFrame) -> None:

    #filters by action tag
    st.subheader("Simulation Logs")
    st.text("This is a log of all the simulation. You can filter the log by action tag. May take a pair of seconds to load.")

    actions_available = sorted(log_df["action"].unique())
    selected_actions = st.multiselect(
        "Filter by action", options=actions_available, default=actions_available
    )
    filtered_df = log_df[log_df["action"].isin(selected_actions)]

    # show the log
    
    st.dataframe(filtered_df)

    return

def plots(log_df: pd.DataFrame) -> None:

    st.header("Simulation Plots")


    st.subheader("Simulation Plots")


    # -------------------
    # Combat & Cahpter Plots
    # -------------------

    mask = log_df["action"].isin([Log_Action.WIN_CHAPTER.value])
    results_df = log_df.loc[mask].copy()

    if "payload" in results_df.columns:
        payload_cols = results_df["payload"].apply(pd.Series)
        results_df = pd.concat([results_df.drop(columns=["payload"]), payload_cols], axis=1)

    st.dataframe(results_df)

    counts = (
        results_df.groupby(["current_day", "action"])
        .size()
        .unstack(fill_value=0)
        .rename_axis(None, axis=1)  # cleaner column labels
        .sort_index()
    )

    st.line_chart(counts)


    ### Show the log of combats per session

    st.subheader("Combat Results Log")
    st.text("This is a log of all the combats. Here is information about player proximity to winning every chapter.")
    mask = log_df["action"].isin([Log_Action.LOSE_CHAPTER.value, Log_Action.WIN_CHAPTER.value])
    combats_df = log_df.loc[mask].copy()

    if "payload" in combats_df.columns:
        payload_cols = combats_df["payload"].apply(pd.Series).add_prefix("combat_")
        combats_df = pd.concat([combats_df.drop(columns=["payload"]), payload_cols], axis=1)

    st.dataframe(combats_df)



    # -------------------
    # Resources Plots
    # -------------------

    mask = log_df["action"].isin([Log_Action.SESSION_END.value])
    resources_df = log_df.loc[mask].copy()

    if "payload" in resources_df.columns:
        payload_cols = resources_df["payload"].apply(pd.Series).add_prefix("session_")
        resources_df = pd.concat([resources_df.drop(columns=["payload"]), payload_cols], axis=1)

    
    graph_data = resources_df.set_index("current_day").sort_index().copy()

    st.line_chart(graph_data["session_chapter_level"])

    graph_data = resources_df.set_index("session_current_session").sort_index().copy()
    st.dataframe(graph_data)


    st.line_chart(graph_data["session_current_coins"])
    st.line_chart(graph_data["session_chapter_level"])
    st.line_chart(graph_data[["session_weapon_gear_level", "session_ring_gear_level", "session_gloves_gear_level", "session_helmet_gear_level", "session_armor_gear_level", "session_boots_gear_level"]])
    st.bar_chart(graph_data[["session_weapon_gear_rarity", "session_ring_gear_rarity", "session_gloves_gear_rarity", "session_helmet_gear_rarity", "session_armor_gear_rarity", "session_boots_gear_rarity"]])


    if "session_designs" in graph_data.columns:
        designs_df = pd.DataFrame(graph_data["session_designs"].tolist(), index=graph_data.index).fillna(0)
        st.line_chart(designs_df)



    return




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

if st.button("Run Simulation & Graphs"):

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

        filtered_log(log_df)
        plots(log_df)
        


    
    
    