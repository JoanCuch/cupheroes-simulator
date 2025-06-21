import streamlit as st
import pandas as pd
from config_import import Config
from model import model, Logger
import matplotlib.pyplot as plt
from typing import Any, Dict, cast
from logger import Logger


st.title("Capybara Go Inspired Simulator")

config = Config.initialize()

# Display the config to allow editing
st.subheader("Config Editor")
edited_player_config = st.data_editor(config.get_player_config())
edited_enemies_config = st.data_editor(config.get_enemies_config())
edited_chapters_config = st.data_editor(config.get_all_chapters_config())

# Execute the simulation
if st.button("Run Simulation"):
    
    model(config)

    # Display the resultdef print_logs(logs: List[dict]):
    st.dataframe(Logger.get_logs())