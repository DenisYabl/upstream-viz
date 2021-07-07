import streamlit as st

# Custom imports
from multipage import MultiPage
from pages import start, tubing_selection, analysis, pump_selection, virtual_flow_meter, well_what_if, potentials, pump_starvation, well_graphics

st.set_page_config(
    page_title="Мехподъем",
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
app.add_page("Трубопровод", "Расчет сети", well_graphics.app)

# The main app
app.run()
