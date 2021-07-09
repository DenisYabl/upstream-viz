import streamlit as st
import streamlit.components.v1 as components
import config
from os import path
import pandas as pd
import numpy as np

from upsolver.DFOperations.calculate_DF import calculate_DF
from upsolver.Tools.viz import draw_result_graph

selection_dict = {
    "ДНС 1": "DNS1_real_values.csv",
    "ДНС 2": "DNS2_real_values.csv",
    "ДНС 3": "DNS3_real_values.csv"
}

base_properties = [
    ('sat_P_bar', 66.7, "Давление насыщения"),
    ('plastT_C', 84.0, "Пластовая температура"),
    ('gasFactor', 39.0, "Газовый фактор"),
    ('oildensity_kg_m3', 826.0, "Плотность сепарированной нефти"),
    ('waterdensity_kg_m3', 1015.0, "Плотность пластовой воды"),
    ('gasdensity_kg_m3', 1.0, "Плотность газа"),
    ('oilviscosity_Pa_s', 35e-3, "Вязкость нефти"),
    ('volumeoilcoeff', 1.015, "Объемный коэффициент")
]

data_folder = config.get_data_folder()


def app():
    st.header("Расчет трубопроводной сети")
    option = st.selectbox('Выберите участок для расчета', ('ДНС 1', 'ДНС 2', 'ДНС 3'))
    dataset = pd.read_csv(path.join(data_folder, selection_dict[option]))
    use_coord = st.sidebar.checkbox(label='Отрисовка сети по координатам', value=True)
    coordinate_scaling = float(st.sidebar.text_input(f"Масштаб координат", '6'))
    eff_diam = st.sidebar.slider("Средний эффективный диаметр сети", min_value=0.01, max_value=1.0, value=0.85,
                                 step=0.01)
    dataset["effectiveD"] = eff_diam
    with st.beta_expander("Свойства жидкости"):
        with st.form("Свойства жидкости"):
            cols = st.beta_columns(8)
            property_dict = {}
            for i, col in enumerate(cols):
                property = base_properties[i]
                property_dict.update({property[0]: col.text_input(f"{property[2]}", property[1])})
            submitted = st.form_submit_button("Подтвердить")
            if submitted:
                for key in list(property_dict.keys()):
                    dataset[key] = float(property_dict[key])

    inlets_df = dataset[dataset["startIsSource"]]
    inlets_dict = {}
    inlets_df["__pad_num"] = inlets_df["__pad_num"].astype(float)
    with st.sidebar:
        with st.form("Граничные условия на кустах"):
            st.write("Граничные условия на кустах")
            for index, row in inlets_df.sort_values("__pad_num").iterrows():
                with st.beta_expander(row['node_name_start']):
                    cols = st.beta_columns(2)
                    inlets_dict.update({index: (
                        cols[0].text_input(f"Давление", row["startValue"], key=f"p_{row['node_name_start']}"),
                        cols[1].text_input(f"Обводненность",
                                           np.round(row["VolumeWater"], decimals=1) if pd.notna(row["VolumeWater"]) else 50.0,
                                           key=f"w_{row['node_name_start']}")
                    )})
            st.form_submit_button("Рассчитать")

    for key in list(inlets_dict.keys()):
        dataset.loc[key, "startValue"] = float(inlets_dict[key][0])
        dataset.loc[key, "VolumeWater"] = inlets_dict[key][1]

    dataset["VolumeWater"] = dataset["VolumeWater"].astype(float)
    outlets_df = dataset[dataset["endIsOutlet"]].copy().drop_duplicates(subset='node_id_end')
    outlets_dict = {}

    with st.sidebar:
        with st.form("Выходные условия"):
            for index, row in outlets_df.sort_values("__pad_num").iterrows():
                st.write(row['node_name_end'])
                outlets_dict.update(
                    {index: st.text_input(f"Давление", row["endValue"])}
                )
            st.form_submit_button("Рассчитать")

    for key in list(outlets_dict.keys()):
        dataset.loc[key, "endValue"] = float(outlets_dict[key])

    with st.spinner("Расчет сети"):
        mdf, G = calculate_DF(dataset, data_folder, return_graph=True)
        pyvis_graph = draw_result_graph(mdf, G, use_coordinates=use_coord, coordinate_scaling=coordinate_scaling)
    try:
        cols = ['node_name_start', 'node_name_end', 'L', 'uphillM', 'D', 'startP', 'endP', 'res_watercut_percent',
                'res_liquid_density_kg_m3', 'X_kg_sec', 'velocity_m_sec']
        float_cols = ['L', 'uphillM', 'startP', 'endP', 'res_watercut_percent', 'res_liquid_density_kg_m3', 'X_kg_sec']

        mdf = mdf[cols]
        mdf['velocity_m_sec'] = mdf['velocity_m_sec'].round(2)
        mdf[float_cols] = mdf[float_cols].astype(float).round(1)

        # TODO Add styler
        mdf = mdf.rename(columns={'L': "Длина",
                                  'node_name_start': "Начало участка",
                                  'node_name_end': "Конец участка",
                                  'uphillM': "Перепад высот, м.",
                                  'startP': "P нач., атм.",
                                  'endP': "P кон., атм.",
                                  'D': "D, мм.",
                                  'res_watercut_percent': "Обв., %",
                                  'res_liquid_density_kg_m3': "Плотность, кг/м3",
                                  'X_kg_sec': "Расход, кг/сек",
                                  'velocity_m_sec': "Скорость, м/с"})

        st.success("Решение найдено")
        st.write(mdf.style.format(
            {"Длина": '{:.0f}',
             "Перепад высот, м.": '{:.1f}',
             "P нач., атм.": '{:.1f}',
             "P кон., атм.": '{:.1f}',
             "Обв., %": '{:.0f}',
             "Плотность, кг/м3": '{:.0f}',
             "Расход, кг/сек": '{:.1f}',
             "Скорость, м/с": '{:.2f}'}))
    except:
        st.error("Решение для данной конфигурации сети не найдено")

    pyvis_graph.save_graph('temp.html')
    html_file = open("temp.html", 'r', encoding='utf-8')
    source_code = html_file.read()
    components.html(source_code, height=900, width=1200)
