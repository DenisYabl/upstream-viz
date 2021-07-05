import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# from DFOperations.calculate_DF import calculate_DF


def app():
    st.header("What-If анализ скважины")
    st.info("Work In Progress...")

    # dataset = pd.read_csv("../CommonData/1well.csv")
    dataset = {}
    # pump_curves = pd.read_csv("../CommonData/PumpChart.csv").set_index("pumpModel")

    with st.sidebar:
        with st.form("Параметры скважины"):
            p_plast = st.number_input("Пластовое давление", min_value=0, max_value=350, value=240)
            p_head = st.number_input("Устьевое давление", min_value=0, max_value=50, value=11)
            productivity = st.slider("Коэффициент продуктивности", min_value=0.1, max_value=3.0, value=0.8)
            perforation = st.number_input("Глубина перфорации", min_value=2000, max_value=4000, value=3759)
            pump_depth = st.number_input("Глубина спуска насоса", min_value=1500, max_value=3500, value=2100)
            k_pump = st.slider("Коэффициент заполнения насоса", min_value=0.0, max_value=1.0, value=0.7)
            frequency = st.slider("Частота вращения насоса", min_value=0, max_value=70, value=50)

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

    dataset["startValue"] = p_plast
    dataset["endValue"] = p_head
    dataset["productivity"] = productivity
    dataset["perforation"] = perforation
    dataset["pumpDepth"] = pump_depth
    dataset["K_pump"] = k_pump
    dataset["frequency"] = frequency
    dataset["sat_P_bar"] = p_saturation
    dataset["plastT_C"] = t_plast
    dataset["gasFactor"] = gas_factor
    dataset["oildensity_kg_m3"] = oil_density_kg_m3
    dataset["waterdensity_kg_m3"] = water_density_kg_m3
    dataset["gasdensity_kg_m3"] = gas_density_kg_m3
    dataset["oilviscosity_Pa_s"] = oil_viscosity_pa_s
    dataset["volumeoilcoeff"] = float(volume_oil_coeff)
    df = pd.DataFrame(dataset, index=[0])
    st.write(df)
    # pump_curve = pump_curves.loc[dataset["model"]].sort_values(by="debit")
    # st.write(pump_curve)
    # mdf = calculate_DF(dataset)
    # Q = mdf.iloc[-1]
    # st.write(Q)
    # Q = Q["X_kg_sec"] * 86400 / Q["res_liquid_density_kg_m3"]
    # st.write(f"Текущий дебит - {Q} м^3/сутки")
    # pressure = mdf["startP"][1:]
    # st.write(pressure)

    # fig = go.Figure(
    #     data=[go.Scatter(x=[perforation, pump_depth, pump_depth - 100, 0], y=pressure)],
    #     layout=go.Layout(
    #         title=go.layout.Title(text="Градиент давления")
    #     ))
    # st.write(fig)
    #
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=pump_curve["debit"], y=pump_curve["pressure"]))
    # fig.add_trace(go.Scatter(x=pump_curve["debit"], y=pump_curve["eff"]))
    # fig.add_vline(x=Q, line_width=3, line_dash="dash", line_color="green")
    # st.write(fig)
    #
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
