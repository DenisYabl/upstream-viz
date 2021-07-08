import time
import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from st_aggrid import GridOptionsBuilder, AgGrid, DataReturnMode
from altair import datum

from upstream.potentials.InFlowCorrelation import Vogel_megion_K_prod
from ot_simple_connector.connector import Connector

start_time = time.time()

QUERY_POTENTIALS = """
| readFile format=parquet path=ermilov/omds/potential_rate 
"""


@st.cache()
def get_data():
    df = pd.read_parquet("./data/raw_data_can_DELETE.parquet")
    return df.query(
        'address == "цех_4__месторождение_Тайлаковское__куст_32__скважина_1291"'
    )


def create_multiline_graphic(source, one_line_one_row=True, annotations=False, beetwen_annotation=20):
    """
    _df : Датафрейм в long-wide формате, ожидаются колонки (_time, value, variable). См. pd.melt
    !!! Altair не умеет в pandas index !!!
    one_line_one_row: По умолчанию каждая метрика будет отображаться на отдельная строке, иначе все графики на одной строке
    annotatins: добавить аннотации на график
    beetwen_annotation:  Растояние между аннотацииями, TODO: для каждой метрики свое расстояние
    """

    source = source.assign(if_visible=source.index % beetwen_annotation == 0)
    st.write(source)
    zoom = alt.selection(type="interval", encodings=["x"])
    # Создаем базовый слой
    base = (
        alt.Chart(source)
            .mark_line(point=True)
            .encode(x="_time", y="value", color="variable"))

    upper = base.properties(width=1200)

    annotation = (
        alt.Chart(source)
            .mark_text(
            align="center",
            baseline="top",
            dx=0
        )
            .encode(x="_time", y="value", text="value")
            .transform_filter(datum.if_visible == 1)
    )
    if one_line_one_row:
        upper = (upper + annotation)
    else:
        upper = upper
    upper = upper.encode(alt.X("_time", scale=alt.Scale(domain=zoom)))

    if annotations:
        upper = upper.facet(row="variable")
    else:
        upper = upper
    upper = upper.resolve_scale(y='independent')
    lower = base.properties(height=60, width=1200).add_selection(zoom)

    return (upper & lower)


def app():
    st.title("Графики АДКУ")
    df = get_data()
    df["_time"] = pd.to_datetime(df["_time"], unit="s")
    AgGrid(df, editable=True)
    COLUMNS = st.multiselect("Выберите параметры", list(df.columns), ["_time"])
    st.write(COLUMNS)
    date_range = st.date_input("Выберите интервал времени", [])
    source = df[COLUMNS].melt(id_vars=["_time"]).dropna()
    st.write(source)
    st.write(len(source))

    #   selection = alt.selection_multi(fields=["variable"])
    rez = create_multiline_graphic(source, False, False)
    st.altair_chart(rez)
    rez = create_multiline_graphic(source, False, True)
    st.altair_chart(rez)
    rez = create_multiline_graphic(source, True, False)
    st.altair_chart(rez)
    rez = create_multiline_graphic(source, True, True)
    st.altair_chart(rez)
