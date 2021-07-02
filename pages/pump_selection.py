import sys

sys.path.append('upstream/pumpselection/')

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from upstream.pumpselection.Hydraulics.oil_params import oil_params
from upstream.pumpselection.PumpSelection.Lyapkov.PumpSelectionAuto import PumpSelectionAuto


def app():
    #st.set_page_config(layout="wide")
    st.title("Подбор УЭЦН")
    dataset = pd.read_csv("./data/input_dataset.csv")
    
    pump_path = "data/pump_curve"
    inclination_path = "data/inclination"
    HKT_path = "data/HKT"
    
    PumpChart = pd.read_parquet(pump_path, engine = 'pyarrow')
    inclination = pd.read_parquet(inclination_path, engine = 'pyarrow')
    HKT = pd.read_parquet(HKT_path, engine = 'pyarrow')

    option = st.selectbox('Выберите скважину из списка',
                          inclination.sort_values("wellNum")["wellNum"].unique(), index = int(np.where(inclination.sort_values("wellNum")["wellNum"].unique() == '4100')[0][0]))
    dataset["wellNum"].iloc[0] = option

    with st.form("Свойства жидкости"):
        st.write("Свойства жидкости")
        cols = st.beta_columns(8)
        baseproperties = [('OilSaturationP', dataset['OilSaturationP'].iloc[0], "Давление насыщения"),
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
            property = baseproperties[i]
            property_dict.update({property[0]:col.text_input(f"{property[2]}", property[1])})
        submitted = st.form_submit_button("Submit")
        if submitted:
            for key in list(property_dict.keys()):
                dataset[key] = float(property_dict[key])

    zaboyP = st.sidebar.text_input(f"Забойное давление", dataset["ZaboyP"].iloc[0])
    dataset["ZaboyP"].iloc[0] = float(zaboyP)
    wellheadP = st.sidebar.text_input(f"Устьевое давление", dataset["WellheadP"].iloc[0])
    dataset["WellheadP"].iloc[0] = float(wellheadP)
    debit = st.sidebar.text_input(f"Суточный дебит", dataset["dailyDebit"].iloc[0])
    dataset["dailyDebit"].iloc[0] = float(debit)
    pumpdepth = st.sidebar.text_input(f"Предыдущая глубина установки насоса", dataset["pumpDepth"].iloc[0])
    dataset["pumpDepth"].iloc[0] = float(pumpdepth)
    perforation = st.sidebar.text_input(f"Глубина перфорации", dataset["perforation"].iloc[0])
    dataset["perforation"].iloc[0] = float(perforation)
    #st.write(dataset)
    with st.spinner("Выполнение расчета"):
        row = dataset.iloc[0]
        wellNum = row["wellNum"]
        pumpDepth = row["pumpDepth"]
        tubing = inclination[inclination["wellNum"] == str(int(wellNum))]
        tubing = tubing.sort_values('depth')
        tubing["Roughness"] = 3e-5
        tubing["IntDiameter"] = 0.57
        tubing["NKTlength"] = 10
        local_HKT = HKT[HKT['wellNum'] == wellNum]
        for stageNum in local_HKT['stageNum'].unique():
            stage_HKT = local_HKT[local_HKT["stageNum"] == stageNum]
            stage_HKT = stage_HKT[stage_HKT["_time"] == stage_HKT["_time"].max()]
            tubing.loc[tubing["depth"] <= stage_HKT["stageLength"].iloc[0], "IntDiameter"] = (stage_HKT[
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
        tempresult = PumpSelectionAuto(calc_params, tubing, PumpChart, row["PlastT"], calc_params.adkuLiquidDebit, basedepth=pumpDepth, perforation = row["perforation"], ZaboiP = row["ZaboyP"],
                          WellheadP = row["WellheadP"], RequiredDebit = row["dailyDebit"] )
        tempresult["wellNum"] = wellNum
        df_result = pd.concat((df_result, tempresult))


    df_result[['debit', 'pressure', 'InputP', 'eff', 'power', 'Hdyn', 'Depth']] = \
        df_result[['debit', 'pressure', 'InputP', 'eff', 'power', 'Hdyn', 'Depth']].astype(
            float).round(2)
    df_result = df_result.rename(columns = {'wellNum': "Номер скважины", 'pumpModel': "Модель насоса",
                   'debit': "Дебит, м3/сутки", 'pressure': "Напор насоса, м.", 'InputP' : "Давление на приеме, атм.",
                   'eff': "КПД, %", 'power': "Мощность, Вт", 'Separator':"Сепаратор",
                                    'Hdyn':"Дин. уровень, м.", 'intensity 0.2':"Кривизна 0.2", 'intensity 0.3':"Кривизна 0.3",
                                           'Depth':'Глубина установки, м'})
    if not df_result.empty:
        st.write(
            df_result.style.format({"Дебит, м3/сутки": '{:.2f}', "Напор насоса, м.": '{:.2f}', "Давление на приеме, атм.": '{:.2f}',
                       "КПД, %": '{:.2f}', "Мощность, Вт": '{:.2f}', "Дин. уровень, м.": '{:.2f}', 'Глубина установки, м': '{:.2f}'}))
    else:
        st.error('Для заданных параметров подобрать насос не удалось')

    fig = go.Figure(
	    data=[go.Scatter(x=tubing['absMark'], y=tubing['prolongation'],     customdata = tubing[['intensity', 'depth']],
                         hovertemplate = '<b>Глубина :%{x:.3f}</b><br>Удлинение:%{y:.3f} <br>Кривизна: %{customdata[0]:.3f}<br>Глубина по колонне: %{customdata[1]:.3f}<extra></extra>')],
	    layout=go.Layout(width = 1024, height = 768,
        xaxis_title="Глубина",
        yaxis_title="Удлинение",
		title=go.layout.Title(text="Инклинометрия скважины")
	    ))
    st.write(fig)

