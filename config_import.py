import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
from typing import Optional
from enum import Enum

config_df: Optional[pd.DataFrame] = None

class ConfigKeys(Enum):
    SS_NAME  = "capybara_sim_data"
    SS_WORKSHEET = "Config"
    CHAPTER_DAILY_EVENT = "chapter_daily_event"
    CHAPTER_DAILY_EVENT_PARAM = "chapter_daily_event_param"
    CHAPTER_GOLD_REWARD = "chapter_gold_reward"
    ENEMY_TYPE = "enemy_type"
    ENEMY_ATK = "enemy_atk"
    ENEMY_DEF = "enemy_def"
    ENEMY_MAX_HP = "enemy_max_hp"
    PLAYER_KEY = "key"
    PLAYER_VALUE = "value"
    STAT_NAME = "stat_name"
    STAT_INITIAL_VALUE = "stat_initial_value"
    STAT_META_BONUS_BASE = "stat_meta_bonus_base"
    STAT_META_BONUS_EXP = "stat_meta_bonus_exp"
    STAT_META_COST_BASE = "stat_meta_cost_base"
    STAT_META_COST_EXP = "stat_meta_cost_exp"
    STAT_ATK = "atk"
    STAT_DEF = "def"
    STAT_MAX_HP = "max_hp"

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
    config_df = pd.DataFrame(worksheet.get_all_records())
    return config_df

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
    global config_df
    if config_df is None:
        config_df = read_sheet(ConfigKeys.SS_NAME.value, ConfigKeys.SS_WORKSHEET.value)
    return config_df


def get_chapter_config(chapter_number: int) -> pd.DataFrame:

    global config_df
    if config_df is None:
        config_df = initialize_config()

    chapter_daily_config_id = "ch" + str(chapter_number) + "_daily_event"
    chapter_param_config_id = "ch" + str(chapter_number) + "_daily_event_param"
    chapter_gold_config_id = "ch" + str(chapter_number) + "_daily_gold_reward"

    columns_to_keep = [chapter_daily_config_id, chapter_param_config_id, chapter_gold_config_id]
    return config_df[columns_to_keep].copy()

def get_enemy_config() -> pd.DataFrame:
    global config_df
    if config_df is None:
        config_df = initialize_config()

    columns_to_keep = [ConfigKeys.ENEMY_TYPE.value, ConfigKeys.ENEMY_ATK.value, ConfigKeys.ENEMY_DEF.value, ConfigKeys.ENEMY_MAX_HP.value]
    return config_df[columns_to_keep].copy()

def get_player_config() -> pd.DataFrame:
    global config_df
    if config_df is None:
        config_df = initialize_config()

    columns_to_keep = [ConfigKeys.STAT_NAME.value, ConfigKeys.STAT_INITIAL_VALUE.value, ConfigKeys.STAT_META_BONUS_BASE.value, ConfigKeys.STAT_META_BONUS_EXP.value, ConfigKeys.STAT_META_COST_BASE.value, ConfigKeys.STAT_META_COST_EXP.value]
    st.dataframe(config_df[columns_to_keep])
    return config_df[columns_to_keep].copy()