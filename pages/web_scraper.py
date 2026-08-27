import streamlit as st
from urllib.parse import urlparse

# แถบค้นหา: ช่อง input + ปุ่มค้นหา
col1, col2, col3 = st.columns([4, 1, 1])

with col1:
    search_query = st.text_input(
        label="search",
        placeholder="https://example.com",
        autocomplete="off",
        key="search_input",
        label_visibility="collapsed"
    )

with col2:
    search_clicked = st.button(
        "ค้นหา", 
        key="btn_primary",
        width='stretch',
    )

with col3:
    add_clicked = st.button(
        "รีเฟรช", 
        icon=":material/refresh:", 
        key="btn_secondary", 
        width='stretch', 
    )

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except ValueError:
        return False

if search_clicked:
    if not search_query.strip():
        st.warning("กรุณากรอก URL ก่อนค้นหา")
    elif not is_valid_url(search_query.strip()):
        st.error("รูปแบบ URL ไม่ถูกต้อง กรุณาระบุเป็น http:// หรือ https://")
    else:
        st.success(f"กำลังดึงข้อมูลจาก: {search_query}")