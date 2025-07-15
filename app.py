import streamlit as st
import pandas as pd
from config_import import Config, ConfigKeys
from model import model, Logger
import matplotlib.pyplot as plt
from typing import Any, Dict, cast
from logger import Logger, Log_Action, Log_Actor, Log_Granularity


def show_log_table(log_df: pd.DataFrame):
    # Augmentar amplada de taula
    st.markdown("""
        <style>
        .stDataFrame div[data-testid="stHorizontalBlock"] {
            overflow-x: auto;
        }
        .stDataFrame table {
            width: 100% !important;
        }
        .stDataFrame td {
            white-space: pre-wrap;
            max-width: 400px;
        }
        .stDataFrame th {
            position: sticky;
            top: 0;
            background-color: #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)

    # Filtres dinàmics
    actor_options = log_df["actor"].unique().tolist()
    granularity_options = log_df["granularity"].unique().tolist()
    action_options = log_df["action"].unique().tolist()

    selected_actor = st.multiselect("Filter by Actor", actor_options,default=[])
    selected_granularity = st.multiselect("Filter by Granularity", granularity_options, default=[])
    default_actions = [a for a in action_options if a != "initialize"]
    selected_action = st.multiselect("Filter by Action", action_options, default=default_actions)

    filtered_df = log_df.copy()
    if selected_actor:
        filtered_df = filtered_df[filtered_df["actor"].isin(selected_actor)]
    if selected_granularity:
        filtered_df = filtered_df[filtered_df["granularity"].isin(selected_granularity)]
    if selected_action:
        filtered_df = filtered_df[filtered_df["action"].isin(selected_action)]

    # Mostrar taula final
    st.dataframe(filtered_df[["actor", "granularity","action","message"]], hide_index=True, use_container_width=True ,height=700)

    daily_graph_df = filtered_df[
        (filtered_df["granularity"] == "day") & (filtered_df["action"] == "simulate")
    ]
    st.dataframe(daily_graph_df)

def plot_test():
    log_df = Logger.get_logs_as_dataframe()
    #log_df = Logger.get_flattened_logs_df()
    log_df = log_df[log_df["granularity"] == Log_Granularity.DAY.value]
    log_df = pd.json_normalize(log_df.to_dict(orient="records"), sep=".")

    st.dataframe(log_df)
    st.write(log_df.columns)

def plot_turn_stats():
    st.subheader("Player Stats Per Turn")

    # Filter logs
    log_df = Logger.get_logs_as_dataframe()
    log_df = log_df[log_df["granularity"] == Log_Granularity.DAY.value]
    day_logs_df = pd.json_normalize(log_df.to_dict(orient="records"), sep=".")

    # Create a graph for each chapter
    chapter_ids = sorted(day_logs_df["payload.day.chapter_num"].unique().tolist())

    for chapter_id in chapter_ids:
        chapter_df = day_logs_df[day_logs_df["payload.day.chapter_num"] == chapter_id]
        st.markdown(f"### Chapter {chapter_id}")

        for stat in ["payload.player_character.stat_hp", "payload.player_character.stat_atk", "payload.player_character.stat_def", "payload.player_character.stat_max_hp"]:
            if stat in chapter_df:
                st.line_chart(
                    chapter_df.set_index("payload.day.day_num")[stat],
                    use_container_width=True,
                )

st.title("Capybara Go Inspired Simulator")

config = Config.initialize()

# Display the config to allow editing
st.subheader("Config Editor")
edited_gear_levels_config = st.data_editor(config.gear_levels_df)
edited_gear_merge_config = st.data_editor(config.gear_merge_df)
edited_chapters_config = st.data_editor(config.chapters_df)

# Simulation
if "simulation_done" not in st.session_state:
    st.session_state.simulation_done = False

if st.button("Run Simulation"):
    Logger.clear_logs()
    model(config)
    st.session_state.simulation_done = True


# Show results
if st.session_state.simulation_done:
    log_df = Logger.get_logs_as_dataframe()
    #show_log_table(log_df)
    #st.write(log_df)
    #plot_test()
    ##plot_turn_stats()
    st.dataframe(log_df)