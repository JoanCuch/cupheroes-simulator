import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field
from logger import Logger, Log_Action

# ---------------------------------------------------------------------------
# Cached Google Sheets fetcher to avoid hitting read‑quota limits
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)  # cache for 5 minutes
def _fetch_worksheet_df(spreadsheet_name: str, worksheet_name: str) -> pd.DataFrame:
    """
    Return the worksheet as DataFrame, caching the result to spare Google API calls.
    Parameters
    ----------
    spreadsheet_name : str
        The Google Sheets file name.
    worksheet_name : str
        The tab to fetch inside that file.
    """
    client = connect_to_API()
    sheet = client.open(spreadsheet_name)
    return pd.DataFrame(sheet.worksheet(worksheet_name).get_all_records())

class ConfigSheets(Enum):
    SPREADSHEET_NAME = "cupheroes_sim_data"
    GEAR_LEVELS_SHEET_NAMEE = "SIM_GEAR_LEVELS"
    GEAR_MERGE_SHEET_NAME = "SIM_GEAR_MERGE"
    CHAPTERS_SHEET_NAME = "SIM_CHAPTERS"
    TIMERS_SHEET_NAME = "SIM_TIMERS"
    CHESTS_SHEET_NAME = "SIM_CHESTS"
    OFFERS_SHEET_NAME = "SIM_OFFERS"
    PLAYERS_SHEET_NAME = "SIM_PLAYERS"

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
    RARE_CHEST_NAME = "rare_chest"
    EPIC_CHEST_NAME = "epic_chest"
    OFFER_NAME = "offer_name"
    OFFER_PRICE_AMOUNT = "price_amount"
    OFFER_PRICE_UNIT = "price_unit"
    OFFER_RARE_CHEST = "rare_chest"
    OFFER_EPIC_CHEST = "epic_chest"
    OFFER_COIN = "coin"
    OFFER_DESIGN = "design"
    OFFER_DIAMOND = "diamond"
    PLAYER_TYPE = "player_type"
    PLAYER_SESSIONS_PER_DAY = "sessions_per_day"
    PLAYER_AVG_SESSION_LENGTH = "avg_session_length"
    PLAYER_PLAY_CHAPTER = "play_chapter_time"
    PLAYER_META_PROGRESSION = "meta_progression_time"
    PLAYER_PURCHASE_FREQUENCY_DAYS = "purchase_frequenzy_days"
    PLAYER_FREE_DAILY_RARE_CHEST = "free_daily_rare_chest"
    PLAYER_FREE_DAILY_EPIC_CHEST = "free_daily_epic_chest"
    PLAYER_SIMULATE = "simulate"



@dataclass
class Config:
    gear_merge_df: pd.DataFrame
    gear_levels_df: pd.DataFrame
    chapters_df: pd.DataFrame
    gacha_df: pd.DataFrame
    offers_df: pd.DataFrame
    players_df: pd.DataFrame

    @staticmethod
    def initialize() -> 'Config':
        # Connect to Google Sheets
        #client = connect_to_API()

        gear_levels_df = _fetch_worksheet_df(
            ConfigSheets.SPREADSHEET_NAME.value,
            ConfigSheets.GEAR_LEVELS_SHEET_NAMEE.value,
        )
        gear_merge_df = _fetch_worksheet_df(
            ConfigSheets.SPREADSHEET_NAME.value,
            ConfigSheets.GEAR_MERGE_SHEET_NAME.value,
        )
        chapters_df = _fetch_worksheet_df(
            ConfigSheets.SPREADSHEET_NAME.value,
            ConfigSheets.CHAPTERS_SHEET_NAME.value,
        )
        gacha_df = _fetch_worksheet_df(
            ConfigSheets.SPREADSHEET_NAME.value,
            ConfigSheets.CHESTS_SHEET_NAME.value,
        )
        offers_df = _fetch_worksheet_df(
            ConfigSheets.SPREADSHEET_NAME.value,
            ConfigSheets.OFFERS_SHEET_NAME.value,
        )
        players_df = _fetch_worksheet_df(
            ConfigSheets.SPREADSHEET_NAME.value,
            ConfigSheets.PLAYERS_SHEET_NAME.value,
        )


        config = Config(
            gear_levels_df=gear_levels_df,
            gear_merge_df=gear_merge_df,
            chapters_df=chapters_df,
            gacha_df=gacha_df,
            offers_df=offers_df,
            players_df=players_df
        )

        return config
    
        
    def get_total_chapters(self) -> int:
        return self.chapters_df['chapter_num'].max()

    def get_chapter_config(self, chapter_number: int) -> pd.DataFrame:
        return self.chapters_df[self.chapters_df['chapter_num'] == chapter_number].copy()

    def get_all_chapters_config(self) -> pd.DataFrame:
        return self.chapters_df

    def reasign_config(self, new_gear_levels_config, new_gear_merge_config, new_chapters_config, new_gacha_config, new_offers_config, new_players_config):
        self.gear_levels_df = new_gear_levels_config
        self.gear_merge_df = new_gear_merge_config
        self.chapters_df = new_chapters_config
        self.gacha_df = new_gacha_config
        self.offers_df = new_offers_config
        self.players_df = new_players_config

def connect_to_API() -> gspread.Client:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = st.secrets["gcp"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client