import streamlit as st

# Custom imports
from multipage import MultiPage
from pages import start, tubing

st.set_page_config(
    page_title="Мехподъем",
    layout="wide"
)

# Create an instance of the app
app = MultiPage()

# Title of the main page
st.title("ИПР ЦУД. Мехподъем")

# Add all your applications (pages) here
app.add_page("Стартовая страница", start.app)
app.add_page("Подбор НКТ", tubing.app)

# The main app
app.run()