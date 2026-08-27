import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import os
from bs4 import BeautifulSoup

# ตั้งค่าหน้าจอ Web Application
st.set_page_config(
    page_title="KornThongPOS", 
    page_icon="🛒", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.logo("https://streamlit.io/images/brand/streamlit-mark-color.png")

# โหลด custom CSS แบบมี error handling
css_path = 'assets/style.css'
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(
            f'<style>{f.read()}</style>', 
            unsafe_allow_html=True
        )
else:
    st.warning(f"ไม่พบไฟล์ {css_path} — ใช้สไตล์ default แทน")

dashboard_page = st.Page(
    page="pages/dashboard.py",
    title="Dashboard",
    icon=":material/bar_chart_4_bars:",
    default=True,
)

shelf_management_page = st.Page(
    page="pages/shelf_management.py",
    title="Shelf Management",
    icon=":material/location_on:",
)

web_scraper_page = st.Page(
    page="pages/web_scraper.py",
    title="Web Scraper",
    icon=":material/language:",
)

notify_app_page = st.Page(
    page="pages/notify_app.py",
    title="Notify App",
    icon=":material/notifications:",
)

pg = st.navigation(
    pages=[dashboard_page, shelf_management_page, web_scraper_page, notify_app_page]
)
pg.run()