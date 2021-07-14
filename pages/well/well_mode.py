import pandas as pd
import streamlit as st
import altair as alt
from datetime import date
import numpy as np
from common.otp import get_data
from ot_simple_connector.connector import Connector

QUERY_WELLS = """| readFile format=parquet path=upstream/well_mode_freq 
| stats count by __well_num"""

# replace $day$ and $well$
QUERY_SINGLE_WELL = """| readFile format=parquet path=upstream/well_mode_freq 
| eval day = strftime(_time, "%Y-%m-%d")
| search day="$day$" AND ($well$)"""


def app():
    with st.form("Параметры"):
        col1, col2 = st.beta_columns(2)
        day = col1.date_input("Select date", value=date(2021, 4, 1))
        all_wells_array = get_data(QUERY_WELLS, ttl=300)["__well_num"].unique()
        well_selected = col2.selectbox("Скважина", ["Random"] + list(all_wells_array))
        st.form_submit_button()

    if "wells_for_labelling" not in st.session_state:
        wells_for_labelling = np.random.choice(all_wells_array, size=20, replace=False) if (well_selected == "Random") \
            else [well_selected]
        st.session_state.wells_for_labelling = wells_for_labelling
    else:
        wells_for_labelling = st.session_state.wells_for_labelling
    wells_to_query = [f"""__well_num="{w}\"""" for w in wells_for_labelling]
    query = QUERY_SINGLE_WELL \
        .replace("$well$", " OR ".join(wells_to_query)) \
        .replace("$day$", day.strftime("%Y-%m-%d"))
    data = get_data(query)
    if "labels" not in st.session_state:
        st.session_state.labels = []
    labels = {}
    with st.form("Select mode"):
        for well in wells_for_labelling:
            with st.beta_container():
                data_for_well = data[data["__well_num"] == well]
                data_for_well["dt"] = pd.to_datetime(data_for_well["_time"], unit="s")
                resize = alt.selection_interval(bind='scales')
                chart1 = alt.Chart(
                    data_for_well[data_for_well["adkuControlStationEngineFreq"].notnull()],
                    title=f"Частота на скважине {well}"
                ).mark_line().encode(
                    x="dt",
                    y="adkuControlStationEngineFreq:Q"
                ).add_selection(resize).properties(height=100, width=600)
                chart2 = alt.Chart(
                    data_for_well[data_for_well["adkuWellStatus"].notnull()],
                    title=f"Включение/выключение скважины {well}"
                ).mark_line(interpolate="step-after").encode(
                    x="dt",
                    y="adkuWellStatus:Q"
                ).add_selection(resize).properties(height=100, width=600)
                chart = (chart1 | chart2).configure()
                st.write(chart)
                labels.update(
                    {well: st.selectbox(f"Выберите режим для скважины {well}",
                                        ["const", "periodic", "const_with_stops", "off"],
                                        key=well)
                     })

        btn = st.form_submit_button("Сохранить разметку")
    if btn:
        st.write(labels)
        with open("labels.csv", "a") as f:
            for well, mode in labels.items():
                f.write(f"""{day.strftime("%Y-%m-%d")},{well},{mode}\n""")

    if st.button("Новые скважины"):
        del st.session_state.wells_for_labelling
        del st.session_state.labels
