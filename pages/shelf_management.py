import streamlit as st

# แถบค้นหา: ช่อง input + ปุ่มค้นหา
col1, col2 = st.columns([5, 1])

with col1:
    search_query = st.text_input(
        label="search",
        placeholder="ค้นหาบาร์โค้ด / ชื่อสินค้า",
        autocomplete="off",
        key="search_input",
        label_visibility="collapsed"
    )

with col2:
    search_clicked = st.button(
        "ค้นหา", 
        key="btn_primary",
        width='stretch'
    )

if search_clicked:
    if not search_query.strip():
        st.warning("กรุณากรอกบาร์โค้ดหรือชื่อสินค้าก่อนค้นหา")
    else:
        st.success(f"กำลังค้นหา: {search_query}")