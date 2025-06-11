import streamlit as st
import logging
from spreadsheets import read_sheet, read_value, test_connection


st.subheader("Text des del Google Sheet")
logging.basicConfig(level=logging.DEBUG)
logging.debug("Connexió a Google Sheets iniciada")

try:
    df_debug = test_connection("capybara_sim_data", "Config")
    st.dataframe(df_debug)
except Exception as e:
    st.error(f"No s'ha pogut llegir el text: {e}")
    st.exception(e)