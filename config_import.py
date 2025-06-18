import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field

class ConfigSheets(Enum):
    SPREADSHEET_NAME = "capybara_sim_data"
    PLAYER_SHEET_NAME = "PLAYER"
    ENEMIES_SHEET_NAME = "ENEMIES"
    CHAPTERS_SHEET_NAME = "CHAPTERS"

class ConfigKeys(Enum):
    STAT_NAME = "stat_name"
    STAT_INITIAL_VALUE = "stat_initial_value"
    STAT_META_BONUS_BASE = "stat_meta_bonus_base"
    STAT_META_BONUS_EXP = "stat_meta_bonus_exp"
    STAT_META_COST_BASE = "stat_meta_cost_base"
    STAT_META_COST_EXP = "stat_meta_cost_exp"
    STAT_ATK = "atk"
    STAT_DEF = "def"
    STAT_MAX_HP = "max_hp"
    ENEMY_TYPE = "enemy_type"
    ENEMY_ATK = "enemy_atk"
    ENEMY_DEF = "enemy_def"
    ENEMY_MAX_HP = "enemy_max_hp"
    CHAPTER_NUM = "chapter_num"
    CHAPTER_DAY_NUM = "day_num"
    CHAPTER_DAILY_EVENT = "daily_event"
    CHAPTER_DAILY_EVENT_PARAM = "daily_event_param"
    CHAPTER_DAILY_GOLD_REWARD = "gold_reward"

@dataclass
class Config:
    player_config_df: pd.DataFrame
    enemies_config_df: pd.DataFrame
    chapters_config_df: pd.DataFrame

    @staticmethod
    def initialize() -> 'Config':
        # Connect to Google Sheets
        client = connect_to_API()

        # Get the spreadsheet and turn into DataFrames
        sheet = client.open(ConfigSheets.SPREADSHEET_NAME.value)
  
        player_config_df = pd.DataFrame(sheet.worksheet(ConfigSheets.PLAYER_SHEET_NAME.value).get_all_records())
        enemies_config_df = pd.DataFrame(sheet.worksheet(ConfigSheets.ENEMIES_SHEET_NAME.value).get_all_records())
        chapters_config_df = pd.DataFrame(sheet.worksheet(ConfigSheets.CHAPTERS_SHEET_NAME.value).get_all_records())

        return Config(
            player_config_df=player_config_df,
            enemies_config_df=enemies_config_df,
            chapters_config_df=chapters_config_df
        )
        
    def get_total_chapters(self) -> int:
        return self.chapters_config_df['chapter_num'].max()

    def get_chapter_config(self, chapter_number: int) -> pd.DataFrame:
        return self.chapters_config_df[self.chapters_config_df['chapter_num'] == chapter_number].copy()
        """
        chapter_daily_config_id = "ch" + str(chapter_number) + "_daily_event"
        chapter_param_config_id = "ch" + str(chapter_number) + "_daily_event_param"
        chapter_gold_config_id = "ch" + str(chapter_number) + "_daily_gold_reward"

        columns_to_keep = [chapter_daily_config_id, chapter_param_config_id, chapter_gold_config_id]
        return self.chapters_config_df[columns_to_keep].copy()
        """

    def get_all_chapters_config(self) -> pd.DataFrame:
        return self.chapters_config_df

    def get_player_config(self) -> pd.DataFrame:
        return self.player_config_df
    
    def get_enemies_config(self) -> pd.DataFrame:
        return self.enemies_config_df
    
    def reasign_config(self, new_player_config, new_enemies_config, new_chapters_config):
        self.player_config_df = new_player_config
        self.enemies_config_df = new_enemies_config
        self.chapters_config_df = new_chapters_config


def connect_to_API() -> gspread.Client:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = st.secrets["gcp"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client



"""
def get_player_config() -> pd.DataFrame:
    global player_config_df
    if player_config_df is None:
        initialize_config()
    return player_config_df.copy()


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
    """