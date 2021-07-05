import time
import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode, GridUpdateMode

from upstream.potentials.InFlowCorrelation import Vogel_megion_K_prod

from upstream.potentials.Optimization_1_well import optimize_freq, optimize_freq_df
from ot_simple_connector.connector import Connector


start_time = time.time()

QUERY_POTENTIALS = """
| readFile format=parquet path=ermilov/omds/potential_rate 
| where potential_oil_rate_technical_limit > Q
| where P_plast > 0
| where regime="Постоянный режим"
"""


@st.cache(allow_output_mutation=True)
def get_data(query):
    conn = Connector(host="192.168.4.65", port="80", user="admin", password="12345678")
    result = conn.session.authorized
    print("Ot_simple_connector is authenticated")
    job = conn.jobs.create(query_text=query, cache_ttl=10, tws=0, twf=0, blocking=True)
    result = job.dataset.load()
    df = pd.DataFrame(result)
    df["padNum"] = df["address"].apply(lambda x: x.split("_")[7])
    df["wellNum"] = df["address"].apply(lambda x: x.split("_")[10])
    return df


def df_styler(df):
    cols = [
        "padNum",
        "wellNum",
        "Q",
        "pump_model",
        "P_bottom_hole_current",
        "P_bottom_hole_technical_limit",
        "potential_oil_rate_technical_limit",
        "P_plast",
        "P_zatrub",
        "P_saturation",
        "K_prod",
        "H_pump",
        "H_perf",
        "freq",
        "regime",
    ]
    rename_dict = {
        "padNum": "Номер куста",
        "wellNum": "Номер скважины",
        "pump_model": "Модель ЭЦН",
        "Q": "Qж",
        "potential_oil_rate_technical_limit": "Потенциал (тех лимит)",
        "P_bottom_hole_current": "Текущее забойное",
        "P_bottom_hole_technical_limit": "Забойное тех-предел",
        "P_plast": "Пластовое",
        "P_zatrub": "Затрубное",
        "P_saturation": "Давление насыщения",
        "K_prod": "Коэф продуктивности",
        "freq": "Частота",
        "H_perf": "Глубина перфорации",
        "H_pump": "Глубина спуска насоса",
        "regime": "Режим работы насоса",
    }

    result = df[cols].rename(rename_dict, axis=1)
    return result


def get_optimization(df):
    df["Действия"] = "Поднять частоту"
    return df


def app():
    st.title("Cкважины с потенциалом тех. предел")
    df = get_data(QUERY_POTENTIALS)
    style_df = df_styler(df)
    gb = GridOptionsBuilder.from_dataframe(style_df)
    gb.configure_selection("single", use_checkbox=True)
    gridOptions = gb.build()
    returned = AgGrid(style_df, gridOptions=gridOptions)
    if st.button("Запустить оптимизацию"):
        temp_df = df.copy()
        a = optimize_freq_df(temp_df)
        temp_df = df_styler(temp_df)
        temp_df[
            ["Оптимальный дебит", "Оптимальное забойное", "Оптимальная частота"]
        ] = a

        COLUMNS = [
            "Номер куста",
            "Номер скважины",
            "Qж",
            "Модель ЭЦН",
            "Текущее забойное",
            "Частота",
            "Оптимальный дебит",
            "Оптимальное забойное",
            "Оптимальная частота",
        ]
        temp_df = temp_df[COLUMNS]
        gb = GridOptionsBuilder.from_dataframe(temp_df)
        gb.configure_selection("single", use_checkbox=True)
        gridOptions = gb.build()
        st.title("Рекомендуемые мероприятия")
        AgGrid(temp_df, gridOptions=gridOptions)

