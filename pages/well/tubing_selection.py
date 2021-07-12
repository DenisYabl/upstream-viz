import streamlit as st
import pandas as pd
import numpy as np
from typing import List

import config
from os import path
from upstream.nkt.nkt_part import NKTPartDict
from upstream.nkt.solver import Solver


# TODO. Подумать, не перенести ли чтение справочника НКТ в инициализацию upstream.nkt.solver.Solver
def read_nkt_dict(nkt_path: str) -> dict:
    nkt_df = pd.read_csv(nkt_path)
    nkt_dict = nkt_df[nkt_df["PRICE_CORR"].notnull()][["NAME", "QNKT", "LIQ", "DNKT0", "FMAX", "PRICE_CORR"]] \
        .set_index("NAME") \
        .T \
        .to_dict()
    return {k: NKTPartDict(k, v["QNKT"], v["LIQ"], v["DNKT0"], v["FMAX"] * 1000, v["PRICE_CORR"]) for k, v in
            nkt_dict.items()}


def read_pumps(pumps_path: str) -> pd.DataFrame:
    pump_df = pd.read_csv(pumps_path)
    pump_df["pump_nominal"] = pump_df["pumpModel"].apply(lambda x: x.split("-")[1])
    return pump_df.set_index("pumpModel")


def read_ped(ped_path: str) -> pd.DataFrame:
    ped_df = pd.read_csv(ped_path)
    return ped_df.set_index("PED")


def read_cable(cable_path: str) -> pd.DataFrame:
    cable_df = pd.read_csv(cable_path)
    return cable_df.set_index("cable")


# TODO. Перенести в upstreampy/nkt
def calculate_extra_fields(res_dict: List[dict]):
    # наименее прочная ступень, на нее приходится какая-то нагрузка (из поля load)
    weakest_max_load = min([part["max_load"] for part in res_dict])
    # текущая нагрузка на наименее прочную ступень
    weakest_load = max([part["load"] for part in res_dict if part["max_load"] == weakest_max_load])
    for part in res_dict:
        podryv = (part["load"] - weakest_load) + weakest_max_load
        part["podryv"] = part["max_load"] if podryv < weakest_max_load else podryv
        for key in ["load", "max_load", "weight", "podryv"]:
            part[key] = part[key] / 9806.65
    for (idx, part) in enumerate(res_dict):
        part["order"] = idx + 1
    return res_dict


def df_styler(df: pd.DataFrame):
    rename_dict = {
        "nkt_type": "Тип НКТ",
        "order": "Ступень",
        "length": "Длина, м",
        "safety": "Запас",
        "weight": "Вес ступени, т",
        "load": "Общий вес, т",
        "max_load": "Предел текучести, т",
        "podryv": "Макс. нагрузка на подрыв, т"
    }
    format_dict = {
        "Предел текучести, т": "{:.1f}",
        "Запас": "{:.2f}",
        "Общий вес, т": "{:.1f}",
        "Вес ступени, т": "{:.1f}",
        "Макс. нагрузка на подрыв, т": "{:.1f}"
    }

    df_styled = df.sort_values("order", ascending=False) \
        .rename(rename_dict, axis=1)[rename_dict.values()] \
        .style \
        .format(format_dict)\
        .apply(highlight_overweight, axis=None)

    return df_styled


def highlight_overweight(df):
    color = "#ffcccb"
    is_greater = df["Общий вес, т"] > df["Макс. нагрузка на подрыв, т"]
    df_background = pd.DataFrame('background-color: ', index=df.index, columns=df.columns)
    df_background["Общий вес, т"] = np.where(is_greater, f"background: {color}", df_background["Общий вес, т"])
    return df_background


def app():
    data_folder = config.get_data_folder()
    nkt_dict_path = path.join(data_folder, "tubings.csv")
    pumps_path = path.join(data_folder, "pumps_weights.csv")
    ped_path = path.join(data_folder, "PED_weights.csv")
    cable_path = path.join(data_folder, "cable_weights.csv")

    nkt_part_dict = read_nkt_dict(nkt_dict_path)
    pump_df = read_pumps(pumps_path)
    ped_df = read_ped(ped_path)
    cable_df = read_cable(cable_path)

    slv = Solver(nkt_part_dict)

    with st.sidebar.form("Исходные данные для расчета"):
        pump_model = st.selectbox("Модель ЭЦН", pump_df.index.to_list())
        pump_weight = pump_df.loc[pump_model]["pumpWeight"]
        pump_nominal = pump_df.loc[pump_model]["pump_nominal"]

        ped_model = st.selectbox("Модель ПЭД", ped_df.index.to_list())
        ped_weight = ped_df.loc[ped_model]["weightPED"]

        cable_model = st.selectbox("Тип кабеля", cable_df.index.to_list())
        cable_weight = cable_df.loc[cable_model]["cableWeight"]

        p_head = st.number_input("Устьевое давление:", min_value=0, value=11)
        pump_depth = st.number_input("Глубина спуска:", min_value=0, value=2700)
        packers = st.text_input("Пакеры:", "2300,2400")
        safety_limit = st.number_input("Коэффициент запаса:", min_value=0.0, value=1.25)
        is_repaired = True if st.radio("Тип НКТ", ["Новые", "Ремонтные"]) == "Ремонтные" else False

        st.form_submit_button("Подобрать НКТ")

    st.header("Подбор НКТ")
    st.info(
        "Для подбора НКТ введите параметры скважины и оборудования в поля ввода на левой панели и нажмите кнопку 'Подобрать НКТ'."
    )

    try:
        results = slv.solve(
            pump_weight=int(pump_weight),
            pump_nominal=int(pump_nominal),
            ped_weight=int(ped_weight),
            cable_weight=float(cable_weight),
            p_head=int(p_head),
            pump_depth=int(pump_depth),
            packers=[int(p.strip()) for p in packers.split(",")],
            safety_limit=float(safety_limit),
            eps_limit=0.02,
            keep="fit",
            is_repaired=is_repaired
        )

        best, simple = results
        best_df = pd.DataFrame(calculate_extra_fields(best)).drop("id", axis=1)
        simple_df = pd.DataFrame(calculate_extra_fields(simple)).drop("id", axis=1)
        st.subheader("Надежный вариант")
        st.dataframe(df_styler(best_df))
        st.subheader("Простой вариант")
        st.dataframe(df_styler(simple_df))
    except AssertionError as err:
        st.error(err)

    with st.beta_expander("Калькулятор надежности"):
        st.subheader("Калькулятор надежности")
        st.info("Указывайте параметры ступеней от верхней к нижней. После ввода параметров нажмите кнопку 'Рассчитать'.")
        with st.form("Ступени НКТ"):
            col1, col2 = st.beta_columns(2)
            with col1:
                type5 = st.selectbox("Тип ступени 5", ["-"] + list(nkt_part_dict.keys()))
                type4 = st.selectbox("Тип ступени 4", ["-"] + list(nkt_part_dict.keys()))
                type3 = st.selectbox("Тип ступени 3", ["-"] + list(nkt_part_dict.keys()))
                type2 = st.selectbox("Тип ступени 2", ["-"] + list(nkt_part_dict.keys()))
                type1 = st.selectbox("Тип ступени 1", ["-"] + list(nkt_part_dict.keys()))
            with col2:
                len5 = st.text_input("Длина ступени 5", 0)
                len4 = st.text_input("Длина ступени 4", 0)
                len3 = st.text_input("Длина ступени 3", 0)
                len2 = st.text_input("Длина ступени 2", 0)
                len1 = st.text_input("Длина ступени 1", 0)
            st.form_submit_button("Рассчитать")

        all_types = [type1, type2, type3, type4, type5]
        all_lengths = [len1, len2, len3, len4, len5]
        filtered = [(t, int(l)) for t, l in zip(all_types, all_lengths) if (t != "-") & (l != 0)]
        if filtered:
            types, lengths = list(zip(*filtered))
            calculated_nkt = slv.calculate(
                pump_weight=int(pump_weight),
                ped_weight=int(ped_weight),
                cable_weight=float(cable_weight),
                p_head=int(p_head),
                pump_depth=int(pump_depth),
                types=types,
                lengths=lengths
            )
            calculated_df = pd.DataFrame(calculate_extra_fields(calculated_nkt)).drop("id", axis=1)
            st.write("Расчет компоновки", df_styler(calculated_df))
        else:
            st.warning("Укажите параметры хотя бы одной ступени")
