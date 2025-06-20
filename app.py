import streamlit as st
import pandas as pd
from config_import import Config
from model import model, Logger
import matplotlib.pyplot as plt
from typing import Any, Dict, cast


st.title("Capybara Go Inspired Simulator")

config = Config.initialize()

# Display the config to allow editing
st.subheader("Config Editor")
edited_player_config = st.data_editor(config.get_player_config())
edited_enemies_config = st.data_editor(config.get_enemies_config())
edited_chapters_config = st.data_editor(config.get_all_chapters_config())

# Execute the simulation
if st.button("Run Simulation"):
    result = model(config)

    # Display the resultdef print_logs(logs: List[dict]):
    for log in result:
        #type_str = log.get("type", "")
        #subtype_str = log.get("subtype", "")
        payload_str = log.get("payload", {}).get("str", "")
        #st.write(f"[{type_str.upper()} - {subtype_str}] {payload_str}")
        st.write(payload_str)