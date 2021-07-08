import streamlit as st
import pandas as pd
import numpy as np
from altair import datum

import config
from os import path
import plotly.graph_objects as go
from upsolver.DFOperations.calculate_DF import calculate_DF
import altair as alt


def show_pump_curves(pump_curve):
    st.subheader("НРХ")
    base = alt.Chart(pump_curve).encode(
        alt.X('debit:Q', axis=alt.Axis(title="Дебит, м3/сут"))
    )

    pressure = base.mark_line(color='#57A44C').encode(
        alt.Y("pressure", axis=alt.Axis(title="Напор, м.", titleColor='#57A44C'))
    )

    eff = base.mark_line().encode(
        alt.Y("eff", axis=alt.Axis(title='КПД, %', titleColor='#5276A7'))
    )

    st.write(
        alt.layer(pressure, eff)
        .resolve_scale(y='independent')
        .configure_axis(gridOpacity=0.5, titlePadding=15, titleFontWeight="normal", titleFontSize=10)
        .configure_view(strokeWidth=0)
        .properties(
            height=250,
            width=600
        )
    )


def app():
    data_folder = config.get_data_folder()
    st.header("What-If анализ скважины")
    well_num = st.text_input("Введите номер скважины", "22")

    pump_curves = pd.read_csv(path.join(data_folder, "PumpChart.csv")).set_index("pumpModel")
    pump_model_list = list(set(pump_curves.index))
    df_well_params = pd.read_csv(path.join(data_folder, "well_params_for_whatif.csv"))
    params_dict = df_well_params[df_well_params["__well_num"] == well_num]\
        .sort_values("day_str", ascending=False)\
        .head(1)\
        .reset_index()\
        .T.to_dict().get(0)

    with st.sidebar:
        with st.form("Параметры скважины"):
            p_plast = st.number_input("Пластовое давление", min_value=0, max_value=350,
                                      value=int(params_dict["p_plast"]))
            p_head = st.number_input("Устьевое давление", min_value=0, max_value=50,
                                     value=int(params_dict["p_head"]))
            productivity = st.slider("Коэффициент продуктивности", min_value=0.1, max_value=3.0,
                                     value=round(float(params_dict["k_prod"]), 2))
            perforation = st.number_input("Глубина перфорации", min_value=2000, max_value=4000,
                                          value=int(params_dict["perf_depth"]))
            pump_depth = st.number_input("Глубина спуска насоса", min_value=1500, max_value=3500,
                                         value=int(params_dict["pump_depth"]))
            k_pump = st.slider("Коэффициент заполнения насоса", min_value=0.0, max_value=1.0, value=0.7)
            pump_model = st.selectbox("Модель насоса", pump_model_list,
                                      index=pump_model_list.index(params_dict["pump_model"]))
            frequency = st.slider("Частота вращения насоса", min_value=0.0, max_value=70.0,
                                  value=float(params_dict["freq"]))

            with st.beta_expander("Параметры жидкости"):
                p_saturation = st.number_input("Давление насыщения", min_value=0, max_value=100, value=63)
                t_plast = st.number_input("Пластовая температура", min_value=0, max_value=100, value=84)
                gas_factor = st.number_input("Газовый фактор", min_value=0, max_value=100, value=49)
                oil_density_kg_m3 = st.slider("Плотность сепарированной нефти", min_value=700, max_value=1200,
                                                      value=826)
                water_density_kg_m3 = st.slider("Плотность пластовой воды", min_value=900, max_value=1100,
                                                        value=1015)
                gas_density_kg_m3 = st.slider("Плотность попутного газа", min_value=0.1, max_value=2.1,
                                                      value=1.0)
                oil_viscosity_pa_s = st.slider("Вязкость сепарированной нефти", min_value=0.0, max_value=100e-3,
                                                       value=35e-3)
                volume_oil_coeff = st.text_input("Объемный коэффициент нефти", "1.015")

            st.form_submit_button("Рассчитать скважину")
        st.button("Сбросить к исходным")

    dataset = {"wellNum": well_num, "juncType": "oilwell", "node_id_end": {0: 3}, "node_id_start": {0: 24}, "startIsSource": {0: True},
               "VolumeWater": {0: 50}, "startKind": {0: "P"}, "endIsOutlet": {0: True}, "endKind": {0: "P"},
               "startP": {0: np.nan}, "startT": {0: 84}, "endP": {0: 1.02}, "endT": {0: np.nan}, "startValue": p_plast,
               "endValue": p_head, "productivity": productivity, "perforation": perforation, "pumpDepth": pump_depth,
               "K_pump": k_pump, "model": pump_model, "frequency": frequency, "sat_P_bar": p_saturation, "plastT_C": t_plast,
               "gasFactor": gas_factor, "oildensity_kg_m3": oil_density_kg_m3,
               "waterdensity_kg_m3": water_density_kg_m3, "gasdensity_kg_m3": gas_density_kg_m3,
               "oilviscosity_Pa_s": oil_viscosity_pa_s, "volumeoilcoeff": float(volume_oil_coeff)}

    df = pd.DataFrame(dataset, index=[0])

    col1, col2 = st.beta_columns(2)
    with col1:
        st.subheader("Расчетные параметры")
        # Calculate well params
        mdf = calculate_DF(df, data_folder)
        # st.write(mdf)
        Q = mdf.iloc[-1]
        Q = Q["X_kg_sec"] * 86400 / Q["res_liquid_density_kg_m3"]
        init_params = [round(params_dict.get(k, -1)) for k in
                       ["debit", "p_plast", "p_zaboy", "p_input", "p_output", "p_head"]]
        calculated_params = [round(Q)] + [round(p) for p in mdf["startP"].values]
        result_dict = {
            "Параметр": ["Дебит", "Пластовое", "Забойное", "На приеме", "На выкиде", "Устьевое"],
            "Исходные": init_params,
            "Расчетные": calculated_params
        }
        st.write(pd.DataFrame(result_dict).set_index("Параметр"))

    with col2:
        # Show pump curve
        pump_curve = pump_curves.loc[dataset["model"]].sort_values(by="debit")
        show_pump_curves(pump_curve)

    # st.write("Моделирование периодического режима")
    # well_973 = pd.read_csv("~/well_973.csv", parse_dates=["index"])
    #
    # def calc_q(dataset):
    #     mdf = calculate_DF(dataset)
    #     Q = mdf.iloc[-1]
    #     Q = Q["X_kg_sec"] * 86400 / Q["res_liquid_density_kg_m3"]
    #     return Q
    #
    # Q_list = []
    # if st.button("Запустить периодический режим"):
    #     for _, state in well_973.iterrows():
    #         temp_dataset = dataset.copy()
    #
    #         if state["status"] == 1.0:
    #             q = calc_q(dataset)
    #         else:
    #             temp_dataset["frequency"] = 1.0
    #             q = calc_q(temp_dataset)
    #             if q < 0:
    #                 q = 0
    #         Q_list.append(q)
    #     well_973["Q"] = Q_list
    #     st.write(well_973)
    #     fig = go.Figure()
    #     fig.add_trace(go.Scatter(x=well_973["index"], y=well_973["status"], line_shape="hv"))
    #     fig.add_trace(go.Scatter(x=well_973["index"], y=well_973["Q"], line_shape="hv"))
    #     st.write(fig)
