import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json

def connect():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = json.loads(st.secrets["gcp"].to_json())
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(creds)

def read_sheet(sheet_name: str, worksheet_title: str) -> pd.DataFrame:
    client = connect()
    sheet = client.open(sheet_name)
    worksheet = sheet.worksheet(worksheet_title)
    records = worksheet.get_all_records()
    return pd.DataFrame(records)

def read_value(sheet_name: str, worksheet_title: str, key: str) -> str:
    df = read_sheet(sheet_name, worksheet_title)
    df.columns = [col.strip().lower() for col in df.columns]
    if "clau" not in df.columns or "valor" not in df.columns:
        return "ERROR: Columnes 'Clau' i 'Valor' no trobades"

    match = df[df["clau"] == key]
    if not match.empty:
        return match.iloc[0]["valor"]
    return "No trobat"

def test_connection(sheet_name: str, worksheet_title: str) -> pd.DataFrame:
    """Helper function to test and display full content of a worksheet."""
    return read_sheet(sheet_name, worksheet_title)