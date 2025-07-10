import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field
from logger import Logger, Log_Actor, Log_Granularity, Log_Action

class ConfigSheets(Enum):
    SPREADSHEET_NAME = "cupheroes_sim_data"
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
    _player_config_df: pd.DataFrame
    _enemies_config_df: pd.DataFrame
    _chapters_config_df: pd.DataFrame

    @staticmethod
    def initialize() -> 'Config':
        # Connect to Google Sheets
        client = connect_to_API()

        # Get the spreadsheet and turn into DataFrames
        sheet = client.open(ConfigSheets.SPREADSHEET_NAME.value)
  
        player_config_df = pd.DataFrame(sheet.worksheet(ConfigSheets.PLAYER_SHEET_NAME.value).get_all_records())
        enemies_config_df = pd.DataFrame(sheet.worksheet(ConfigSheets.ENEMIES_SHEET_NAME.value).get_all_records())
        chapters_config_df = pd.DataFrame(sheet.worksheet(ConfigSheets.CHAPTERS_SHEET_NAME.value).get_all_records())

        config = Config(
            _player_config_df=player_config_df,
            _enemies_config_df=enemies_config_df,
            _chapters_config_df=chapters_config_df
        )

        Logger.add_log(
            Log_Actor.SIMULATION, Log_Granularity.SIMULATION, Log_Action.INITIALIZE,
            "Configuration initialized from Google Sheets.",
            payload={
                "player_config": player_config_df.to_dict(orient='records'),
                "enemies_config": enemies_config_df.to_dict(orient='records'),
                "chapters_config": chapters_config_df.to_dict(orient='records')
            }
        )

        return config
    
        
    def get_total_chapters(self) -> int:
        return self._chapters_config_df['chapter_num'].max()

    def get_chapter_config(self, chapter_number: int) -> pd.DataFrame:
        return self._chapters_config_df[self._chapters_config_df['chapter_num'] == chapter_number].copy()

    def get_all_chapters_config(self) -> pd.DataFrame:
        return self._chapters_config_df

    def get_player_config(self) -> pd.DataFrame:
        return self._player_config_df
    
    def get_enemies_config(self) -> pd.DataFrame:
        return self._enemies_config_df
    
    def reasign_config(self, new_player_config, new_enemies_config, new_chapters_config):
        self._player_config_df = new_player_config
        self._enemies_config_df = new_enemies_config
        self._chapters_config_df = new_chapters_config


def connect_to_API() -> gspread.Client:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = st.secrets["gcp"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client