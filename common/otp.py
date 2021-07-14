import streamlit as st
import config
import pandas as pd


@st.cache(ttl=3600)
def get_data(query: str, ttl=60) -> pd.DataFrame:
    conn = config.get_rest_connector()
    df = pd.DataFrame(conn.jobs.create(query, cache_ttl=ttl, tws=0, twf=0).dataset.load())
    if "_time" in df.columns:
        df["dt"] = pd.to_datetime(df["_time"], unit="s")
    return df
