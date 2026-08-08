import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ตั้งค่าหน้าจอ Web Application
st.set_page_config(page_title="Store Layout & Scraping Demo", layout="wide")
st.title("🚀 Store Operations & Data Scraping Demo")

# สร้าง Tabs หลัก
tab1, tab2, tab3 = st.tabs(["📊 Dynamic 2D/3D Store Layout", "🕸️ Universal Web Scraper", "💬 LINE Notification"])

# ==========================================
# Tab 1: Interactive 2D Layout & Shelf View
# ==========================================
with tab1:
    st.header("🏪 Interactive Store Layout & Shelf Management")
    
    if 'selected_shelf' not in st.session_state:
        st.session_state.selected_shelf = None

    search_query = st.text_input("🔍 ค้นหาบาร์โค้ด / ชื่อสินค้า", placeholder="กรอกชื่อสินค้าหรือบาร์โค้ด...")
    
    col_layout, col_detail = st.columns([1.2, 1])

    with col_layout:
        st.subheader("1. ผังร้านค้าแบบ 2D (Store Floor Plan)")
        
        shapes_data = [
            {"id": "Shelf A (Red)", "x": [0, 0, 1, 1], "y": [0, 8, 8, 0], "color": "#C84B31"},
            {"id": "Shelf B (Green)", "x": [2, 2, 3, 3], "y": [0, 8, 8, 0], "color": "#88B04B"},
            {"id": "Shelf C (Orange)", "x": [4, 4, 5, 5], "y": [2, 10, 10, 2], "color": "#F2A950"},
            {"id": "Shelf D (Dark)", "x": [6, 6, 7, 7], "y": [1, 7, 7, 1], "color": "#2D2D2D"},
            {"id": "Shelf E (Red Side)", "x": [8, 8, 9, 9], "y": [0, 9, 9, 0], "color": "#C84B31"},
        ]
        
        fig_floor = go.Figure()
        for shape in shapes_data:
            fig_floor.add_trace(go.Scatter(
                x=shape["x"], y=shape["y"],
                fill="toself",
                fillcolor=shape["color"],
                mode="lines+text",
                name=shape["id"],
                text=[shape["id"], "", "", ""],
                textposition="middle center",
                line=dict(color="white", width=2)
            ))

        fig_floor.update_layout(
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=450,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="#F8F9FA",
            plot_bgcolor="#F8F9FA"
        )
        st.plotly_chart(fig_floor, use_container_width=True)
        
        selected = st.selectbox("เลือกชั้นวางที่ต้องการดูข้อมูลซูม (Shelf View):", 
                                ["-- คลิกเลือกชั้นวาง --"] + [s["id"] for s in shapes_data])
        if selected != "-- คลิกเลือกชั้นวาง --":
            st.session_state.selected_shelf = selected

    with col_detail:
        st.subheader("2. มุมมองเจาะลึกชั้นวาง (Shelf View Grid)")
        if st.session_state.selected_shelf:
            st.success(f"📍 กำลังแสดงตำแหน่งสินค้าบน: **{st.session_state.selected_shelf}**")
            
            grid_colors = [
                ["#C84B31", "#88B04B", "#2D2D2D", "#88B04B", "#C84B31"],
                ["#88B04B", "#2D2D2D", "#88B04B", "#88B04B", "#2D2D2D"],
                ["#C84B31", "#88B04B", "#2D2D2D", "#C84B31", "#88B04B"],
                ["#2D2D2D", "#C84B31", "#2D2D2D", "#C84B31", "#C84B31"]
            ]
            
            fig_shelf = px.imshow(
                grid_colors,
                labels=dict(x="คอลัมน์", y="ชั้นวาง", color="สถานะ"),
                x=['1', '2', '3', '4', '5'],
                y=['ชั้น 4', 'ชั้น 3', 'ชั้น 2', 'ชั้น 1']
            )
            fig_shelf.update_xaxes(side="top")
            fig_shelf.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_shelf, use_container_width=True)
            
            st.info("💡 คุณสามารถลากปรับเปลี่ยนตำแหน่งข้อมูลในระบบเพื่อทำการ Planogram Re-layout ได้")
        else:
            st.info("👈 กรุณาคลิกเลือกชั้นวางจากผังด้านซ้ายเพื่อดูโครงสร้าง Shelf View")

# ==========================================
# Tab 2: Universal Web Scraper & HTML Renderer
# ==========================================
with tab2:
    st.header("🕸️ Real-time Web Scraper & Live HTML Renderer")
    st.write("ดึงข้อมูล HTML จาก URL แล้วนำมารัน/แสดงผลเป็นหน้าเว็บจริงอยู่ภายในหน้านี้แบบเรียลไทม์")
    
    # ช่องใส่ URL
    input_url = st.text_input("กรอก URL ที่ต้องการ Scrape และ Render หน้าเว็บ:", "https://example.com")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        fetch_btn = st.button("🔎 Search / Fetch HTML")
    with col_btn2:
        refresh_btn = st.button("🔄 Refresh Page")

    # บันทึก HTML Code ลง Session State เพื่อให้อยู่คงเดิมแม้มีการโต้ตอบกับ UI
    if 'html_content' not in st.session_state:
        st.session_state.html_content = ""

    if fetch_btn or refresh_btn:
        if input_url:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                }
                with st.spinner("กำลังดึงข้อมูลและเตรียม Render หน้าเว็บ HTML..."):
                    res = requests.get(input_url, headers=headers, timeout=10)
                    res.encoding = res.apparent_encoding
                    st.session_state.html_content = res.text
                    
                st.success(f"✅ ดึงข้อมูลสำเร็จ! (Status Code: {res.status_code})")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        else:
            st.warning("กรุณากรอก URL ก่อนกดปุ่มค้นหา")

    # การแสดงผล HTML
    if st.session_state.html_content:
        subtab_view, subtab_source = st.tabs(["🌐 Live HTML Rendered Page", "📜 Raw HTML Code"])
        
        with subtab_view:
            st.subheader("ผลลัพธ์การ Render หน้าเว็บแบบ Sandbox")
            st.caption("หน้าต่างด้านล่างคือ HTML ทั้งหมดที่ถูก Scrape มาเรนเดอร์ในหน้านี้โดยตรง:")
            
            # ใช้ components.html เพื่อเรนเดอร์ HTML Code ภายใน iframe
            components.html(st.session_state.html_content, height=600, scrolling=True)
            
        with subtab_source:
            st.subheader("ซอร์สโค้ด Raw HTML")
            st.code(st.session_state.html_content, language="html")

# ==========================================
# Tab 3: LINE Notification
# ==========================================
with tab3:
    st.header("💬 ระบบส่งการแจ้งเตือนไปยัง LINE")
    
    line_token = st.text_input("Channel Access Token", type="password")
    line_user_id = st.text_input("User ID ผู้รับ")
    message = st.text_area("ข้อความแจ้งเตือน", "แจ้งเตือนการอัปเดตข้อมูลตำแหน่งสินค้าจากระบบ Store Demo")
    
    if st.button("🚀 ส่งข้อความ"):
        if line_token and line_user_id and message:
            url = "https://api.line.me/v2/bot/message/push"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {line_token}"
            }
            payload = {
                "to": line_user_id,
                "messages": [{"type": "text", "text": message}]
            }
            res = requests.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                st.success("✅ ส่งการแจ้งเตือนเข้า LINE เรียบร้อยแล้ว!")
            else:
                st.error(f"❌ ล้มเหลว: {res.status_code} - {res.text}")
        else:
            st.error("กรุณากรอกข้อมูล Token, User ID และข้อความให้ครบถ้วน")