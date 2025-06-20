import streamlit as st
import pandas as pd
from config_import import Config
from model import model, Chapter_Log
import matplotlib.pyplot as plt

st.title("Capybara Go Inspired Simulator")

config = Config.initialize()

# Display the config to allow editing
st.subheader("Config Editor")
edited_player_config = st.data_editor(config.get_player_config())
edited_enemies_config = st.data_editor(config.get_enemies_config())
edited_chapters_config = st.data_editor(config.get_all_chapters_config())

# Execute the simulation
if st.button("Run Simulation"):
    config.reasign_config(edited_player_config, edited_enemies_config, edited_chapters_config)
    result = model(config)
    st.write(result)