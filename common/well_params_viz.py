import altair as alt
import pandas as pd
import streamlit as st
import config
from common import otp

get_data_conf = config.get_conf("get_data.yaml")


def show():
    st.subheader("Параметры работы скважины")
    with st.form("Параметры работы скважины"):
        col1, col2, col3, col4 = st.beta_columns(4)
        with col1:
            selected_well = st.text_input("Номер скважины")
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
            selected_params = st.multiselect("Параметры", list(params.keys()), [])
        with col3:
            date_range = st.date_input("Временной интервал", [])
        with col4:
            num_samples = st.number_input("Количество точек с подписями", min_value=0, max_value=100, value=10)
        st.form_submit_button("Показать данные")

    if bool(selected_well) & bool(selected_params) & bool(date_range):
        tws, twf = [int(d.strftime("%s")) for d in date_range]  # FIXME Time zones!
        cols = [params[par] for par in selected_params]
        params_query = f"""
            | {get_data_conf["virtual_flow_meter"]["well_params"]}
            | search _time>={tws} AND _time<{twf} 
            | search __well_num="{selected_well}"
        """
        df = pd.DataFrame()
        try:
            df = otp.get_data(params_query).set_index("dt").sort_index()[cols].dropna(how="all")
        except KeyError as err:
            st.error("Ошибка при загрузке данных. Скорее всего, по заданным параметрам данных в платформе не найдено.\n"
                     + str(err))
            return
        charts = []
        resize = alt.selection_interval(bind='scales')
        for col, col_rus in zip(cols, selected_params):
            idf = df[col].dropna().rename(col_rus).reset_index()
            chart = alt.Chart(idf).mark_line(interpolate="cardinal").encode(
                x=alt.X("dt:T", axis=alt.Axis(title="")),
                y=f"{col_rus}:Q"
            ).properties(
                height=150,
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
                ).transform_sample(num_samples)
            charts.append(chart + text)
        st.write(
            alt.vconcat(*charts)
                .configure_axis(gridOpacity=0.5, titlePadding=15, titleFontWeight="normal", titleFontSize=10)
                .configure_view(strokeWidth=0)
        )
    else:
        st.info("Введите номер скважины, временной интервал и выберите хотя бы один параметр")
