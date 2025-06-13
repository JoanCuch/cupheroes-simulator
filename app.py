import streamlit as st
import pandas as pd
from spreadsheets import  initialize_config
from model import model,  Chapter_Log, Daily_Log
import matplotlib.pyplot as plt

st.title("Capybara Go Simulator")

try:
    config_df = initialize_config()

    #st.write(config_df)

    chapter_log = model(config_df)


    st.dataframe(chapter_log.daily_log.log)

    log_df = chapter_log.daily_log.to_dataframe()
    #st.line_chart(log_df.set_index("day")[["player_atk", "player_def", "player_hp", "player_maxhp"]])
    #st.line_chart(log_df.set_index("day")[["player_delta_atk", "player_delta_def", "player_delta_hp", "player_delta_maxhp"]])

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


except Exception as e:
    st.error(f"Some error happened: {e}")
    st.exception(e)