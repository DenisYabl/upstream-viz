import streamlit as st

# Custom imports
from multipage import MultiPage
from pages import start
from pages.well import virtual_flow_meter, well_graphics, pump_starvation, well_what_if, pump_selection, \
    tubing_selection, analysis, potentials
from pages.pipe import pipeline_calculation

st.set_page_config(
    page_title="ИПР ЦУД",
    layout="wide"
)

# Create an instance of the app
app = MultiPage()

# Title of the main page
st.title("Центр Управления Добычей")

# Add all your applications (pages) here
app.add_page("Мехподъем", "Стартовая страница", start.app)
app.add_page("Мехподъем", "Анализ фонда", analysis.app)
app.add_page("Мехподъем", "Виртуальный расходомер", virtual_flow_meter.app)
app.add_page("Мехподъем", "Срывы подачи", pump_starvation.app)
app.add_page("Мехподъем", "What-If анализ скважины", well_what_if.app)
app.add_page("Мехподъем", "Анализ и достижимость потенциалов", potentials.app)
app.add_page("Мехподъем", "Подбор НКТ", tubing_selection.app)
app.add_page("Мехподъем", "Подбор УЭЦН", pump_selection.app)
app.add_page("Мехподъем", "Пример графиков", well_graphics.app)
app.add_page("Трубопровод", "Стартовая страница", start.app)
app.add_page("Трубопровод", "Расчет сети", pipeline_calculation.app)

# The main app
app.run()
