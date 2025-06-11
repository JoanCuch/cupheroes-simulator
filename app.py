import streamlit as st
from spreadsheets import read_sheet, read_value, test_connection


st.subheader("Text des del Google Sheet")

try:

    df_debug = test_connection("capybara_sim_data", "Config")
    st.write(df_debug)
    st.write("DEBUG DF", df_debug)
    welcome_text = read_value("capybara_sim_data", "Config", "welcome")
    st.info(welcome_text)
except Exception as e:
    st.error(f"No s'ha pogut llegir el text: {e}")
    st.write("TIPUS:", type(e))
    st.write("OBJECTE:", e)
    st.error("Error llegint el text")