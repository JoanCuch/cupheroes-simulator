import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
from typing import Optional

#config_df: Optional[pd.DataFrame] = None

# Connect to Google API
def connect():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = st.secrets["gcp"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(creds)

# Read all the required sheet
def read_sheet(sheet_name: str, worksheet_title: str) -> pd.DataFrame:
    client = connect()
    sheet = client.open(sheet_name)
    worksheet = sheet.worksheet(worksheet_title)
    return pd.DataFrame(worksheet.get_all_records())

"""
def read_value(key: str) -> str:
    global config_df
    if config_df is None:
        return "ERROR: config_df not initialized"
    
    df = config_df.copy()
    df.columns = [col.strip().lower() for col in df.columns]

    if "key" not in df.columns or "value" not in df.columns:
        return "ERROR: key or Value columns not found"

    match = df[df["key"] == key]
    if not match.empty:
        return match.iloc[0]["valor"]
    return "ERROR: value not found"
"""

def initialize_config() -> pd.DataFrame:
    config_df = read_sheet("capybara_sim_data", "Config")
    return config_df