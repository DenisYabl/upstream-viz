import streamlit as st
import datetime
import config
from common import otp
from common import styler

criteria_dict = {
    "crit_adjust_kes":
        ("Корректировка периодического режима", [
            "скважина работает в периодическом режиме",
            "номинальная производительность ЭЦН <= 125",
            "дебит жидкости < номинала насоса, умноженного на коэффициент подачи (доля времени, которую насос "
            "работает за сутки) "
        ]),
    "crit_kes":
        ("Перевод в КЭС", [
            "скважина работает в постоянном режиме",
            "номинальная производильность ЭЦН <= 125",
            "высота столба жидкости над ЭЦН < 400м",
            "дебит жидкости < 60% от номинала ЭЦН",
        ]),
    "crit_right":
        ("Приведение в соответствме (правая зона)", [
            "дебит жидкости > 130% от номинальной производительности",
            "номинальная производительность >= 160",
            "дебит нефти < 50т",
            "Частота ЭЦН > 55Гц",
        ]),
    "crit_up":
        ("Приподъем", [
            "номинальная производительность ЭЦН >= 250",
            "высота столба жидкости над ЭЦН > 800м",
            "обводненность > 80%",
            "время от запуска насоса > 700дн"
        ]),
    "crit_pritok": (
        "Смена ЭЦН по притоку", [
            "скважина работает в постоянном режиме",
            "номинальная производительность ЭЦН >= 160",
            "высота столбы жидкости над ЭЦН < 400м",
            "дебит жидкости составляет менее 70% от номинала насоса",
        ]
    ),
    "crit_technology": (
        "Смена ЭЦН по технологии", [
            "скважина работает в постоянном режиме",
            "высота столба жидкости над ЭЦН >= 400м",
            "дебит жидкости < 70% от номинала насоса",
        ]),
    "crit_shtuz": (
        "Штуцирование", [
            "буферное давление > линейного давления на 3атм и более",
            "скважина работает в постоянном режиме"
        ])
}

format_dict = {
        "day": ("Дата", None),
        "__deposit": ("Месторождение", None),
        "__pad_num": ("Куст", None),
        "__well_num": ("Скв", None),
        "pumpModel": ("Модель ЭЦН", None),
        "AverageLiquidDebit": ("Qж", "{:.0f}"),
        "AverageOilDebit": ("Qн", "{:.0f}"),
        "VolumeWater": ("Обв", "{:.0f}"),
        "pumpDepth": ("Спуск", None),
        "Hdynamic": ("Дин уровень", "{:.0f}"),
        "PumpInputP": ("На приеме", "{:.1f}"),
        "LinearP": ("Линейное", "{:.1f}"),
        "Pbuffer": ("Буферное", "{:.1f}"),
        "Pzatrub": ("Затрубное", "{:.1f}"),
        "PumpFreq": ("Частота", "{:.1f}"),
        "Mode_text": ("Режим", None),
        "work_rate": ("Коэф. насоса", "{:.2f}"),
        "LiquidDebitWorkRateLimit": ("Qпр с учетом вр. работы", "{:.1f}"),
        "work_daily": ("Время работы", "{:.1f}"),
        "stop_daily": ("Время простоя", "{:.1f}"),
    }


def app():
    st.header("Анализ мех.фонда")
    col_date, col_criteria, _ = st.beta_columns((1, 1.1, 3))
    date = col_date.date_input("Дата", datetime.date(2021, 5, 20))
    criteria = col_criteria.selectbox("Предлагаемое действие",
                                      list(criteria_dict.keys()),
                                      format_func=lambda c: criteria_dict.get(c)[0])

    with st.beta_expander(f"""Какие критерии должны быть выполнены для действия?"""):
        info_text = "\n".join([f"- {condition}" for condition in criteria_dict[criteria][1]]) + "\n"
        st.markdown(info_text)

    source = config.get_conf("get_data.yaml")["analysis"]
    query = f"""| {source}
    | eval day = strftime(_time, "%Y-%m-%d")
    | eval one = 1
    | search {criteria}=1 AND day="{date.strftime("%Y-%m-%d")}" """
    df = otp.get_data(query)
    if df.empty:
        st.warning("Нет скважин, удовлетворяющих выбранному критерию на выбранную дату")
    else:
        st.subheader("Список скважин")
        st.write(
            styler.style_df(df, format_dict)
        )

    with st.beta_expander("Проверка техрежимов"):
        st.subheader("Проверка на корректность техрежимов из АДКУ")
