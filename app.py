from utils.summary import generate_summary
from utils.utilities import utilities_ui
import streamlit as st

# Main Streamlit App
st.title("SQLite Reading Summary Generator")

# Tabs for navigation
tabs = st.tabs(["Summary", "Utilities"])

with tabs[0]:
    st.write("### Summary")
    generate_summary()

with tabs[1]:
    st.write("### Utilities")
    utilities_ui()

    # Footer Banner
st.markdown(
    """
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #f1f1f1;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            font-family: Arial, sans-serif;
            box-shadow: 0px -2px 5px rgba(0, 0, 0, 0.1);
        }
        .footer a {
            text-decoration: none;
            color: #0366d6;
            font-weight: bold;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
    <div class="footer">
        Code is OpenSource from <a href="https://github.com/MontyTheSoftwareEngineer/KoboStatisticsReader" target="_blank">MontyTheSoftwareEngineer</a>
    </div>
    """,
    unsafe_allow_html=True
)
