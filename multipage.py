"""
This file is the framework for generating multiple Streamlit applications
through an object oriented framework.
"""

# Import necessary libraries
import streamlit as st


# Define the multipage class to manage the multiple apps in our program
class MultiPage:
    """Framework for combining multiple streamlit applications."""

    def __init__(self) -> None:
        """Constructor class to generate a list which will store all our applications as an instance variable."""
        self.pages = []

    def add_page(self, category, title, func) -> None:
        """Class Method to Add pages to the project
        Args:
            :param function func: Python function to render this page in Streamlit
            :param str title: The title of page which we are adding to the list of apps
            :param str category: Page category (subsystem)
        """

        self.pages.append({
            "category": category,
            "title": title,
            "function": func
        })

    def run(self):
        col1, col2 = st.beta_columns(2)
        with col1:
            cat = st.selectbox("Подсистема", ["Мехподъем", "Трубопровод"])

        with col2:
            # Dropdown to select the page to run
            page = st.selectbox(
                f"""Навигация по подсистеме "{cat}" """,
                [page for page in self.pages if page["category"] == cat],
                format_func=lambda page: page['title']
            )
        st.markdown("---")
        # run the app function
        page['function']()