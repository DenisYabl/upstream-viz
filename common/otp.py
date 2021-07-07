import streamlit as st
import config
import pandas as pd


@st.cache
def get_data(query):
    conn = config.get_rest_connector()
    df = pd.DataFrame(conn.jobs.create(query, cache_ttl=60, tws=0, twf=0).dataset.load())
    if "_time" in df.columns:
        df["dt"] = pd.to_datetime(df["_time"], unit="s")
    return df