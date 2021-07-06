import streamlit as st
import pandas as pd
import numpy as np
import config
from os import path
import plotly.graph_objects as go
from upsolver.DFOperations.calculate_DF import calculate_DF
import altair as alt


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

    dataset = {"wellNum": well_num, "juncType": "oilwell", "node_id_end": {0: 3}, "node_id_start": {0: 24}, "startIsSource": {0: True},
               "VolumeWater": {0: 50}, "startKind": {0: "P"}, "endIsOutlet": {0: True}, "endKind": {0: "P"},
               "startP": {0: np.nan}, "startT": {0: 84}, "endP": {0: 1.02}, "endT": {0: np.nan}, "startValue": p_plast,
               "endValue": p_head, "productivity": productivity, "perforation": perforation, "pumpDepth": pump_depth,
               "K_pump": k_pump, "model": pump_model, "frequency": frequency, "sat_P_bar": p_saturation, "plastT_C": t_plast,
               "gasFactor": gas_factor, "oildensity_kg_m3": oil_density_kg_m3,
               "waterdensity_kg_m3": water_density_kg_m3, "gasdensity_kg_m3": gas_density_kg_m3,
               "oilviscosity_Pa_s": oil_viscosity_pa_s, "volumeoilcoeff": float(volume_oil_coeff)}

    df = pd.DataFrame(dataset, index=[0])
    pump_curve = pump_curves.loc[dataset["model"]].sort_values(by="debit")
    st.subheader("НРХ")
    col1, col2 = st.beta_columns(2)
    with col1:
        st.line_chart(pump_curve.set_index("debit")["pressure"])
    with col2:
        st.line_chart(pump_curve.set_index("debit")["eff"])

    mdf = calculate_DF(df, folder=data_folder)
    Q = mdf.iloc[-1]
    st.write(Q.to_dict())
    Q = Q["X_kg_sec"] * 86400 / Q["res_liquid_density_kg_m3"]
    st.write(f"Расчетный дебит - {Q:.1f} м^3")
    pressure = mdf["startP"][1:]
    df_pressure = pd.DataFrame(mdf["startP"][1:])
    df_pressure["Давление"] = pd.Series(["0", "Забойное", "На приеме", "На выкиде", "Устьевое"])
    st.write(df_pressure)

    fig = go.Figure(
        data=[go.Scatter(x=[perforation, pump_depth, pump_depth - 100, 0], y=pressure)],
        layout=go.Layout(
            title=go.layout.Title(text="Градиент давления")
        ))
    st.write(fig)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pump_curve["debit"], y=pump_curve["pressure"]))
    fig.add_trace(go.Scatter(x=pump_curve["debit"], y=pump_curve["eff"]))
    fig.add_vline(x=Q, line_width=3, line_dash="dash", line_color="green")
    st.write(fig)

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
