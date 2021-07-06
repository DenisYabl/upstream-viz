import streamlit as st
import pandas as pd
import os
import datetime
from ot_simple_connector.connector import Connector
import config


def get_criteria_description(conf, crit_name):
    return conf["description"].get(crit_name, "Для выбранного критерия отсутвует описание")


kes_desc = """
Для скважины должны выполняться следующие условия:

- скважина работает в постоянном режиме;

- номинальная производильность ЭЦН не более 125;

- высота столба жидкости над ЭЦН менее 400м;

- дебит жидкости составляет менее 60% от номинала ЭЦН."
"""

criteria_dict = {
    "Корректировка периодического режима": "crit_adjust_kes",
    "Перевод в КЭС": "crit_kes",
    "Приведение в соответствие (правая зона)": "crit_right",
    "Приподъем": "crit_up",
    "Смена ЭЦН по притоку": "crit_pritok",
    "Смена ЭЦН по технологии": "crit_technology",
    "Смена в постоянный режим": "crit_const",
    "Штуцирование": "crit_shtuz",
    "Все": "one"
}


@st.cache
def get_data(query, conf) -> pd.DataFrame:
    conf_rest = {k: v for k, v in conf["rest"].items() if k in ["host", "port", "user", "password"]}
    conn = Connector(**conf_rest)
    ds = conn.jobs.create(query, cache_ttl=60, tws=0, twf=0).dataset.load()
    return pd.DataFrame(ds)


# TODO. Сделать стайлер, как в виртуальном расходомере
def df_styler(df):
    cols = ["day", "__deposit", "__pad_num", "__well_num", "pumpModel", "AverageLiquidDebit", "AverageOilDebit",
            "VolumeWater", "pumpDepth", "Hdynamic", "PumpInputP", "LinearP", "Pbuffer", "Pzatrub", "PumpFreq",
            "Mode_text", "work_rate", "work_daily", "stop_daily", "LiquidDebitWorkRateLimit"]
    rename_dict = {
        "day": "Дата",
        "__deposit": "Месторождение",
        "__pad_num": "Куст",
        "__well_num": "Скв",
        "pumpModel": "Модель ЭЦН",
        "AverageLiquidDebit": "Qж",
        "AverageOilDebit": "Qн",
        "VolumeWater": "Обв",
        "pumpDepth": "Спуск",
        "Hdynamic": "Дин уровень",
        "PumpInputP": "На приеме",
        "LinearP": "Линейное",
        "Pbuffer": "Буферное",
        "Pzatrub": "Затрубное",
        "PumpFreq": "Частота",
        "Mode_text": "Режим",
        "work_rate": "Коэф. насоса",
        "LiquidDebitWorkRateLimit": "Qпр с учетом вр. работы",
        "work_daily": "Время работы",
        "stop_daily": "Время простоя"
    }
    format_dict = {
        "Qж": "{:.0f}",
        "Qн": "{:.0f}",
        "Обв": "{:.0f}",
        "Дин уровень": "{:.0f}",
        "Линейное": "{:.1f}",
        "На приеме": "{:.1f}",
        "Буферное": "{:.1f}",
        "Затрубное": "{:.1f}",
        "Частота": "{:.1f}",
        "Коэф. насоса": "{:.1f}",
        "Время работы": "{:.1f}",
        "Время простоя": "{:.1f}",
        "Qпр с учетом вр. работы": "{:.1f}",
    }
    return df[cols].sort_values("__well_num").rename(rename_dict, axis=1).style.format(format_dict)


def app():
    conf = config.get_conf("config.yaml")
    col1, col2 = st.beta_columns(2)
    with col1:
        date = st.date_input("Дата", datetime.date(2021, 5, 20))
    with col2:
        crit = st.selectbox("Предлагаемое действие", list(criteria_dict.keys()))

    with st.beta_expander(f"""Какие критерии должны быть выполнены для действия "{crit}"?"""):
        info_text = get_criteria_description(conf, criteria_dict[crit])
        st.markdown(info_text)

    query = f"""| readFile format=parquet path=upstream/analysis
    | eval day = strftime(_time, "%Y-%m-%d")
    | eval one = 1
    | search {criteria_dict[crit]}=1 AND day="{date.strftime("%Y-%m-%d")}" """
    with st.spinner("Загрузка данных..."):
        df = get_data(query, conf)
        if df.empty:
            st.warning("Нет скважин, удовлетворяющих выбранному критерию на выбранную дату")
        else:
            st.write(df_styler(df))
