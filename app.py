import streamlit as st
import pandas as pd
from config_import import Config
from model import model, Chapter_Log
import matplotlib.pyplot as plt

st.title("Capybara Go Simulator")
#st.sidebar.header("Config")
#st.sidebar.button("Reload Page", on_click=st.rerun())


config = Config.initialize()

edited_player_config = st.data_editor(
    config.get_player_config()
    )

edited_enemies_config = st.data_editor(
    config.get_enemies_config()
    )

edited_chapters_config = st.data_editor(
    config.get_all_chapters_config()
    )

if st.button("Run Simulation"):
    config.reasign_config(edited_player_config, edited_enemies_config, edited_chapters_config)
    result = model(config)
    st.write(result)

"""
#st.write(config_df)
st.divider()
st.subheader("Chapter Daily Log")
chapters_log = model(edited_config_df)

st.divider()

for chapter in chapters_log:
    #st.subheader(f"Chapter: {chapter.name}")
    st.dataframe(chapter.daily_log)
"""


"""
log_df = pd.DataFrame(chapters_log[0].chapter_log.daily_log)

st.line_chart(
    log_df[["day", "player_atk", "player_def", "player_hp", "player_maxhp"]],
    x = "day",
    y = ["player_atk", "player_def", "player_hp", "player_maxhp"],
    x_label= "day",
    y_label= "player stats",
    color=["#000000", "#1982C4", "#FF595E", "#FFCA3A"]
)

st.line_chart(
    log_df[["day", "player_delta_atk", "player_delta_def", "player_delta_hp", "player_delta_maxhp"]],
    x = "day",
    y = ["player_delta_atk", "player_delta_def", "player_delta_hp", "player_delta_maxhp"],
    x_label= "day",
    y_label= "player stats",
    color=["#000000", "#1982C4", "#FF595E", "#FFCA3A"]
)
"""
