import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field
from logger import Logger, Log_Action

class ConfigSheets(Enum):
    SPREADSHEET_NAME = "cupheroes_sim_data"
    GEAR_LEVELS_SHEET_NAMEE = "GEAR_LEVELS"
    GEAR_MERGE_SHEET_NAME = "GEAR_MERGE"
    CHAPTERS_SHEET_NAME = "CHAPTERS"

class ConfigKeys(Enum):
    STAT_NAME = "stat_name"
    LEVEL = "level"
    GOLD_COST = "gold_cost"
    DESIGN_COST = "design_cost"
    REQUIRED_RARITY = "required_rarity"
    TARGET_RARITY = "target_rarity"
    REQ1_RARITY = "req1_rarity"
    REQ1_PIECE = "req1_piece"
    REQ1_SET = "req1_set"
    REQ2_RARITY = "req2_rarity"
    REQ2_PIECE = "req2_piece"
    REQ2_SET = "req2_set"
    REQ3_RARITY = "req3_rarity"
    REQ3_PIECE = "req3_piece"
    REQ3_SET = "req3_set"
    CHAPTER_NUM = "chapter_num"
    AVG_GEAR_LEVEL_REQUIRED = "avg_gear_level_required"
    UNIQUE_GEAR_PIECES_REQUIRED = "unique_gear_pieces_required"
    CHEST_NAME = "chest_name"
    FREE_DAILY = "free_daily"
    WIN_REWARD_GOLD = "win_reward_gold"
    WIN_REWARD_DESIGNS = "win_reward_designs"
    WIN_REWARD_GACHA = "win_reward_gacha"
    LOSE_REWARD_GOLD = "lose_reward_gold"
    LOSE_REWARD_DESIGNS = "lose_reward_designs" 
    LOSE_REWARD_GACHA = "lose_reward_gacha"
    TIMER_AMOUNT = "timer_amount"
    TIMER_ACTION = "timer_action"
    SESSIONS_PER_DAY = "sessions_per_day"
    AVG_SESSION_LENGTH = "avg_session_length"
    PLAY_CHAPTER = "play_chapter"
    META_PROGRESSION = "meta_progression"

@dataclass
class Config:
    gear_merge_df: pd.DataFrame
    gear_levels_df: pd.DataFrame
    chapters_df: pd.DataFrame
    gacha_df: pd.DataFrame
    timers_df: pd.DataFrame

    @staticmethod
    def initialize() -> 'Config':
        # Connect to Google Sheets
        client = connect_to_API()

        # Get the spreadsheet and turn into DataFrames
        sheet = client.open(ConfigSheets.SPREADSHEET_NAME.value)

        gear_levels_df = pd.DataFrame(sheet.worksheet(ConfigSheets.GEAR_LEVELS_SHEET_NAMEE.value).get_all_records())
        gear_merge_df = pd.DataFrame(sheet.worksheet(ConfigSheets.GEAR_MERGE_SHEET_NAME.value).get_all_records())
        chapters_df = pd.DataFrame(sheet.worksheet(ConfigSheets.CHAPTERS_SHEET_NAME.value).get_all_records())
        gacha_df = pd.DataFrame(sheet.worksheet("GACHA").get_all_records())
        timers_df = pd.DataFrame(sheet.worksheet("TIMERS").get_all_records())

        config = Config(
            gear_levels_df=gear_levels_df,
            gear_merge_df=gear_merge_df,
            chapters_df=chapters_df,
            gacha_df=gacha_df,
            timers_df=timers_df
        )

        return config
    
        
    def get_total_chapters(self) -> int:
        return self.chapters_df['chapter_num'].max()

    def get_chapter_config(self, chapter_number: int) -> pd.DataFrame:
        return self.chapters_df[self.chapters_df['chapter_num'] == chapter_number].copy()

    def get_all_chapters_config(self) -> pd.DataFrame:
        return self.chapters_df

    def reasign_config(self, new_gear_levels_config, new_gear_merge_config, new_chapters_config):
        self.gear_levels_df = new_gear_levels_config
        self.gear_merge_df = new_gear_merge_config
        self.chapters_df = new_chapters_config

def connect_to_API() -> gspread.Client:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = st.secrets["gcp"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client