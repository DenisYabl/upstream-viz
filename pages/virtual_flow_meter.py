import altair as alt
import streamlit as st
import pandas as pd
from datetime import date
import config

gzu_cols_format = {
    "day_str": ("Дата", None),
    "__pad_num": ("Куст", None),
    "anomaly_wells_in_pad": ("Проблемных скв.", "{:.0f}"),
    "__well_num": ("Скважины", None)
}

gzu_detail_cols_format = {
    "__well_num": ("Скважины", None),
    "pump_model": ("Модель ЭЦН", None),
    "Q": ("Qж", "{:.0f}"),
    "Q_regime": ("Qреж", "{:.0f}"),
    "Q_predict": ("Qпрогноз", "{:.1f}"),
    "water": ("Обв", "{:.0f}%"),
    "InputP": ("Прием", "{:.1f}"),
    "LinearP": ("Устье", "{:.1f}"),
    "P_zaboy": ("Забой", "{:.1f}")
}

q_detail_cols = {
    "__well_num": ("Скважина", None),
    "pump_model": ("Модель ЭЦН", None),
    "Q": ("Qж", "{:.0f}"),
    "Q_regime": ("Qреж", "{:.0f}"),
    "margin": ("Допуск", "{:.0f}%"),
    "water": ("Обв", "{:.0f}%"),
    "InputP": ("Прием", "{:.1f}"),
    "LinearP": ("Устье", "{:.1f}"),
    "P_zaboy": ("Забой", "{:.1f}"),
    "low_rate": ("Доля сниж.", "{:.2f}")
}


def styler(df: pd.DataFrame, style_dict: dict):
    rename_cols = {k: v[0] for k, v in style_dict.items()}
    format_cols = {v[0]: v[1] for _, v in style_dict.items() if v[1]}
    return df.rename(rename_cols, axis=1).style.format(format_cols)


@st.cache
def get_data(query):
    conn = config.get_rest_connector()
    df = pd.DataFrame(conn.jobs.create(query, cache_ttl=60, tws=0, twf=0).dataset.load())
    df["dt"] = pd.to_datetime(df["_time"], unit="s")
    return df


def app():
    st.header("Виртуальный расходомер")
    selected_date = st.date_input("Выберите дату", value=date(2021, 6, 9))
    get_data_conf = config.get_conf("get_data.yaml")
    query = f"""| {get_data_conf["virtual_flow_meter"]["vfm"]}
        | sort _time
        | streamstats time_window=1w sum(Q_is_low) as low_Qs, count as total by __well_num
        | eval low_rate = low_Qs / total
        | eval is_q_decrease = if(low_rate>0.5, 1, 0)
        | search day_str="{selected_date}"
        | eval anomaly_well_num = if(Q_is_anomaly == 1, __well_num, null)
        | eventstats dc(anomaly_well_num) as anomaly_wells_in_pad by day_str, __pad_num
        | eval is_gzu_problem = if(anomaly_wells_in_pad>2 AND Q_is_anomaly=1, 1, 0)
        | search is_gzu_problem=1 OR is_q_decrease=1
    """

    with st.spinner("Загрузка данных..."):
        df = get_data(query)

    with st.beta_container():
        col1, col2 = st.beta_columns(2)
        with col1:
            st.subheader("Возможные проблемы с ГЗУ")
            st.markdown("Модель машинного обучения прогнозирует суточный дебит по параметрам работы скважины. "
                        "Считается, что на кусте есть проблемы с замерами, если для трех и более скважин куста "
                        "отклонение замеренного дебита от прогнозируемого составляет более 20%")
            df_gzu = df[df["is_gzu_problem"] == 1] \
                .groupby("__pad_num") \
                .agg({"day_str": "max",
                      "anomaly_wells_in_pad": "max",
                      "__well_num": "unique"})
            gzu_cols = ["day_str", "__pad_num", "anomaly_wells_in_pad", "__well_num"]
            st.write(
                styler(
                    df_gzu.reset_index().sort_values("anomaly_wells_in_pad", ascending=False)[gzu_cols],
                    gzu_cols_format
                )
            )
            selected_pad1 = st.selectbox("Выберите куст", df_gzu.index.unique())
            detail_cols = ["__well_num", "pump_model", "Q", "Q_regime", "Q_predict", "water",
                           "InputP", "LinearP", "P_zaboy"]
            st.dataframe(
                styler(
                    df[(df["is_gzu_problem"] == 1) & (df["__pad_num"] == selected_pad1)][detail_cols]
                        .sort_values("Q", ascending=False),
                    gzu_detail_cols_format
                )
            )
        with col2:
            st.subheader("Возможное снижение дебита")
            st.markdown("Считается, что на скважине снижается дебит, если за последнюю неделю более чем в половине "
                        "замеров дебит был меньше режимного и величина отклонения превышала допустимую. "
                        "Допустимые величины отклонений задаются в справочнике и зависят от номинала ЭЦН и "
                        "обводненности скважины")
            df_low = df[df["is_q_decrease"] == 1] \
                .groupby("__pad_num") \
                .agg(
                {"day_str": "max",
                 "__well_num": "unique"}
            )
            df_low["anomaly_wells_in_pad"] = df_low["__well_num"].apply(len)
            limit = st.radio("", ["Топ-5 кустов", "Все кусты"])
            low_cols = ["day_str", "__pad_num", "anomaly_wells_in_pad", "__well_num"]
            rows = 5 if limit == "Топ-5 кустов" else 99999
            st.dataframe(
                styler(
                    df_low.reset_index().sort_values("anomaly_wells_in_pad", ascending=False)[low_cols].head(rows),
                    gzu_cols_format
                )
            )
            selected_pad2 = st.selectbox("Выберите куст", df_low.index.unique())
            detail_cols = ["__well_num", "pump_model", "Q", "Q_regime", "margin", "water",
                           "InputP", "LinearP", "P_zaboy", "low_rate"]
            st.dataframe(
                styler(
                    df[(df["is_q_decrease"] == 1) & (df["__pad_num"] == selected_pad2)][detail_cols]
                        .sort_values("Q", ascending=False),
                    q_detail_cols
                )
            )

    st.subheader("Параметры работы скважины")
    with st.form("Параметры работы скважины"):
        col1, col2, col3 = st.beta_columns(3)
        with col1:
            selected_well = st.text_input("Введите номер скважины")
        with col2:
            params = {
                "Состояние ЭЦН": "adkuWellStatus",
                "Суточный дебит, м3/сут": "adkuWellLiquidDebit",
                "Режимный дебит, м3/сут": "oilWellopAverageLiquidDebit",
                "Обводненность": "oilWellopVolumeWater",
                "Давление затрубное": "adkuWellZatrubP",
                "Давление на приеме ЭЦН": "adkuWellInputP",
                "Температура на приеме ЭЦН": "",  # Пусто
                "Дисбаланс напряжения": "adkuControlStationVoltageDisbalance",
                "Ток фазы A": "adkuControlStationCurrentA",
                "Ток фазы B": "adkuControlStationCurrentB",
                "Ток фазы C": "adkuControlStationCurrentC",
                "Напряжение BA": "adkuControlStationVoltageBA",
                "Напряжение AC": "adkuControlStationVoltageAC",
                "Напряжение CB": "adkuControlStationVoltageCB",
                "Частота ЭЦН": "adkuControlStationEngineFreq",
                "Дисбаланс токов": "adkuControlStationCurrentDisbalance",
                "Сопротивление изоляции": "adkuControlStationResistance",
                "Коэффициент мощности": "adkuControlStationPowerCoeff",
                "Загрузка": "adkuControlStationLoading",
                "Давление в коллекторе ГЗУ": "adkuWellLinearP"
            }
            selected_params = st.multiselect("Выберите параметры", list(params.keys()), [])
        with col3:
            height = st.number_input("Высота графиков", min_value=10, max_value=500, value=150)
        st.form_submit_button("Показать данные")

    cols = [params[par] for par in selected_params]
    params_query = f"""
        | {get_data_conf["virtual_flow_meter"]["well_params"]} 
        | search __well_num="{selected_well}"
    """
    if bool(selected_well) & bool(selected_params):
        df = get_data(params_query).set_index("dt").sort_index()[cols].dropna(how="all")
        charts = []
        resize = alt.selection_interval(bind='scales')
        for col, col_rus in zip(cols, selected_params):
            idf = df[col].dropna().rename(col_rus).reset_index()
            chart = alt.Chart(idf).mark_line(interpolate="cardinal").encode(
                x=alt.X("dt:T", axis=alt.Axis(title="")),
                y=f"{col_rus}:Q"
            ).properties(
                height=height,
                width=1000
            ).transform_sample(1000).add_selection(resize)
            text = alt.Chart(idf)\
                .mark_text(
                    baseline="top",
                    dy=5,
                    fontWeight="normal")\
                .encode(
                    x=alt.X("dt:T", axis=alt.Axis(title="")),
                    y=f"{col_rus}:Q",
                    text=f"{col_rus}:Q"
                ).transform_sample(10)
            charts.append(chart + text)
        st.write(
            alt.vconcat(*charts)
                .configure_axis(gridOpacity=0.5, titlePadding=15, titleFontWeight="normal", titleFontSize=9)
                .configure_view(strokeWidth=0)
        )
    else:
        st.info("Введите номер скважины и выберите хотя бы один параметр")
