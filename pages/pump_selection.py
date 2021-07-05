import sys

#sys.path.append('upstream/pumpselection/')

import streamlit as st
import pandas as pd
import numpy as np
# import plotly.graph_objects as go
from upstream.pumpselection.hydraulics.oil_params import oil_params
from upstream.pumpselection.PumpSelection.Lyapkov.PumpSelectionAuto import PumpSelectionAuto


def app():
    # st.set_page_config(layout="wide")
    st.header("Подбор УЭЦН")
    dataset = pd.read_csv("./data/input_dataset.csv")

    pump_path = "data/pump_curve"
    inclination_path = "data/inclination"
    nkt_path = "data/HKT"

    pump_chart = pd.read_parquet(pump_path, engine='pyarrow')
    inclination = pd.read_parquet(inclination_path, engine='pyarrow')
    nkt = pd.read_parquet(nkt_path, engine='pyarrow')
    pump_chart["NominalQ"] = pump_chart["pumpModel"].apply(lambda x: float(x.split('-')[1]))

    well_list = inclination.sort_values("wellNum")["wellNum"].unique()
    start_well_idx = int(np.where(well_list == '1817')[0][0])

    with st.beta_expander("Свойства жидкости"):
        with st.form("Свойства жидкости"):
            cols = st.beta_columns(9)
            base_properties = [('OilSaturationP', dataset['OilSaturationP'].iloc[0], "Давление насыщения"),
                              ('PlastT', dataset['PlastT'].iloc[0], "Пластовая температура"),
                              ('GasFactor', dataset['GasFactor'].iloc[0], "Газовый фактор"),
                              ('SepOilWeight', dataset['SepOilWeight'].iloc[0], "Плотность сепарированной нефти"),
                              ('PlastWaterWeight', dataset['PlastWaterWeight'].iloc[0], "Плотность пластовой воды"),
                              ('GasDensity', dataset['GasDensity'].iloc[0], "Плотность газа"),
                              ('SepOilDynamicViscosity', dataset['SepOilDynamicViscosity'].iloc[0], "Вязкость нефти"),
                              ('VolumeOilCoeff', dataset['VolumeOilCoeff'].iloc[0], "Объемный коэффициент"),
                              ('neftWellopVolumeWater', dataset['neftWellopVolumeWater'].iloc[0], "Обводненность")]
            property_dict = {}
            for i, col in enumerate(cols):
                prop = base_properties[i]
                property_dict.update({prop[0]: col.text_input(f"{prop[2]}", prop[1])})
            submitted = st.form_submit_button("Обновить")
            if submitted:
                for key in list(property_dict.keys()):
                    dataset[key] = float(property_dict[key])

    with st.sidebar:
        option = st.selectbox('Выберите скважину из списка', well_list, index=start_well_idx)
        dataset["wellNum"].iloc[0] = option
        with st.form("Параметры скважины"):
            p_zaboy = st.text_input(f"Забойное давление", dataset["ZaboyP"].iloc[0])
            p_head = st.text_input(f"Устьевое давление", dataset["WellheadP"].iloc[0])
            debit = st.text_input(f"Суточный дебит", dataset["dailyDebit"].iloc[0])
            pump_depth = st.text_input(f"Предыдущая глубина установки насоса", dataset["pumpDepth"].iloc[0])
            perforation = st.text_input(f"Глубина перфорации", dataset["perforation"].iloc[0])
            st.form_submit_button("Подобрать ЭЦН")

    dataset["ZaboyP"].iloc[0] = float(p_zaboy)
    dataset["WellheadP"].iloc[0] = float(p_head)
    dataset["dailyDebit"].iloc[0] = float(debit)
    dataset["pumpDepth"].iloc[0] = float(pump_depth)
    dataset["perforation"].iloc[0] = float(perforation)
    # st.write(dataset)

    with st.spinner("Выполнение расчета"):
        row = dataset.iloc[0]
        well_num = row["wellNum"]
        pump_depth = row["pumpDepth"]
        tubing = inclination[inclination["wellNum"] == str(int(well_num))]
        tubing = tubing.sort_values('depth')
        tubing["Roughness"] = 3e-5
        tubing["IntDiameter"] = 0.57
        tubing["NKTlength"] = 10
        local_nkt = nkt[nkt['wellNum'] == well_num]
        for stageNum in local_nkt['stageNum'].unique():
            stage_nkt = local_nkt[local_nkt["stageNum"] == stageNum]
            stage_nkt = stage_nkt[stage_nkt["_time"] == stage_nkt["_time"].max()]
            tubing.loc[tubing["depth"] <= stage_nkt["stageLength"].iloc[0], "IntDiameter"] = (stage_nkt[
                                                                                                  "stageDiameter"].iloc[
                                                                                                  0] - 16) / 1000
        calc_params = oil_params(dailyQ=row["dailyDebit"], saturationPressure=row["OilSaturationP"],
                                 plastT=row["PlastT"], gasFactor=row["GasFactor"],
                                 oilDensity=row["SepOilWeight"], waterDensity=row["PlastWaterWeight"],
                                 gasDensity=row["GasDensity"],
                                 oilViscosity=row["SepOilDynamicViscosity"],
                                 volumeWater=row["neftWellopVolumeWater"], volumeoilcoeff=row["VolumeOilCoeff"])
        calc_params.ZaboiP = row["ZaboyP"]
        calc_params.WellheadP = row["WellheadP"]
        calc_params.perforation = row["perforation"]

        calc_params.adkuLiquidDebit = row["dailyDebit"] * (
            row["SepOilWeight"] * (1 - calc_params.volumewater_percent / 100) +
            row["PlastWaterWeight"] * (calc_params.volumewater_percent / 100)) / 86400

        df_result = pd.DataFrame(
            columns=["wellNum", 'pumpModel', 'debit', 'pressure', 'InputP', 'eff', 'power', 'Separator',
                     'Hdyn', 'intensity 0.2', 'intensity 0.3', 'Depth'])
        temp_result = PumpSelectionAuto(calc_params, tubing, pump_chart, row["PlastT"], calc_params.adkuLiquidDebit,
                                       basedepth=pump_depth, perforation=row["perforation"], ZaboiP=row["ZaboyP"],
                                       WellheadP=row["WellheadP"], RequiredDebit=row["dailyDebit"])
        temp_result["wellNum"] = well_num
        df_result = pd.concat((df_result, temp_result))

    df_result[['debit', 'pressure', 'InputP', 'eff', 'power', 'Hdyn', 'Depth']] = \
        df_result[['debit', 'pressure', 'InputP', 'eff', 'power', 'Hdyn', 'Depth']].astype(
            float).round(2)
    df_result = df_result[["wellNum", "pumpModel", "Depth", "debit", "pressure", "Hdyn", "InputP", "eff", "power",
                           "Separator", "intensity 0.2", "intensity 0.3"]]
    df_result = df_result.drop_duplicates(subset = ['pumpModel', 'Depth'])
    df_result = df_result.rename(columns={'wellNum': "Скважина", 'pumpModel': "Модель насоса",
                                          'debit': "Дебит, м3/сут", 'pressure': "Напор, м.",
                                          'InputP': "Давл на приеме, атм.",
                                          'eff': "КПД, %", 'power': "Мощность, Вт", 'Separator': "Сепаратор",
                                          'Hdyn': "Дин. уровень, м.", 'intensity 0.2': "Кривизна 0.2",
                                          'intensity 0.3': "Кривизна 0.3",
                                          'Depth': 'Глубина установки, м'})
    if not df_result.empty:
        st.write(
            df_result.style.format(
                {"Дебит, м3/сут": '{:.0f}', "Напор, м.": '{:.0f}', "Давл на приеме, атм.": '{:.1f}',
                 "КПД, %": '{:.1f}', "Мощность, Вт": '{:.0f}', "Дин. уровень, м.": '{:.0f}',
                 'Глубина установки, м': '{:.0f}'}))
    else:
        st.error('Для заданных параметров подобрать насос не удалось')

    # fig = go.Figure(
    #     data=[go.Scatter(x=tubing['absMark'], y=tubing['prolongation'], customdata=tubing[['intensity', 'depth']],
    #                      hovertemplate='<b>Глубина :%{x:.3f}</b><br>Удлинение:%{y:.3f} <br>Кривизна: %{customdata[0]:.3f}<br>Глубина по колонне: %{customdata[1]:.3f}<extra></extra>')],
    #     layout=go.Layout(width=1024, height=768,
    #                      xaxis_title="Глубина",
    #                      yaxis_title="Удлинение",
    #                      title=go.layout.Title(text="Инклинометрия скважины")
    #                      ))
    # st.write(fig)
