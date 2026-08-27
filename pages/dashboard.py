import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os

st.title("Dashboard")
st.caption(f"อัปเดตล่าสุด: {datetime.now().strftime('%d/%m/%Y %H:%M')} น.")

# ======== Mock Data ========
np.random.seed(42)

dates = pd.date_range(end=datetime.today(), periods=30)
sales_data = pd.DataFrame({
    "วันที่": dates,
    "ยอดขาย": np.random.randint(15000, 45000, size=30)
})

top_products = pd.DataFrame({
    "สินค้า": ["น้ำดื่ม 600ml", "ขนมปังโฮลวีท", "นมสด UHT", "ไข่ไก่ เบอร์ 2", "บะหมี่กึ่งสำเร็จรูป"],
    "จำนวนขาย": [820, 650, 540, 480, 410]
})

category_data = pd.DataFrame({
    "หมวดหมู่": ["เครื่องดื่ม", "ของแห้ง", "ของสด", "ขนม", "ของใช้"],
    "สัดส่วน": [30, 25, 20, 15, 10]
})

low_stock = pd.DataFrame({
    "สินค้า": ["นมสด UHT 1L", "ไข่ไก่ เบอร์ 1", "น้ำมันพืช 1L", "ผงซักฟอก 1kg"],
    "คงเหลือ": [5, 8, 3, 6],
    "จุดสั่งซื้อ": [20, 20, 15, 15]
})

# ======== KPI Cards ========
col1, col2, col3, col4 = st.columns(4)

kpi_cards = [
    {"label": "ยอดขายวันนี้", "value": "฿32,450", "delta": "+12.5%", "accent": "#FF7518", "trend": "up"},
    {"label": "จำนวนออเดอร์", "value": "186", "delta": "+8 รายการ", "accent": "#2563eb", "trend": "up"},
    {"label": "สินค้าคงคลัง", "value": "1,240 SKU", "delta": "-15 SKU", "accent": "#7c3aed", "trend": "down"},
    {"label": "สินค้าใกล้หมด", "value": "4 รายการ", "delta": "ต้องสั่งซื้อ", "accent": "#dc2626", "trend": "warn"},
]

trend_color = {"up": "#16a34a", "down": "#dc2626", "warn": "#d97706"}

for col, kpi in zip([col1, col2, col3, col4], kpi_cards):
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 4px solid {kpi['accent']};">
            <div class="kpi-label">{kpi['label']}</div>
            <div class="kpi-value">{kpi['value']}</div>
            <div class="kpi-delta" style="color:{trend_color[kpi['trend']]};">{kpi['delta']}</div>
        </div>
        """, unsafe_allow_html=True)

# ======== แถวที่ 1: กราฟยอดขาย + สัดส่วนหมวดหมู่ ========
col_left, col_right = st.columns([2, 1])

CHART_FONT = dict(family="Inter, sans-serif", color="#1e1e1e", size=13)

with col_left:
    with st.container(key="card_sales"):
        st.markdown('<p class="section-title">แนวโน้มยอดขาย (30 วันล่าสุด)</p>', unsafe_allow_html=True)

        fig_sales = px.area(
            sales_data,
            x="วันที่",
            y="ยอดขาย",
            color_discrete_sequence=["#FF7518"]
        )
        fig_sales.update_traces(
            line=dict(width=3, color="#FF7518"),
            fillgradient=dict(
                type="vertical",
                colorscale=[[0, "rgba(255,117,24,0.35)"], [1, "rgba(255,117,24,0.0)"]]
            ),
            hovertemplate="<b>%{x|%d %b}</b><br>ยอดขาย: %{y:,.0f} บาท<extra></extra>"
        )
        fig_sales.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=320,
            xaxis_title=None,
            yaxis_title=None,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=CHART_FONT,
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor="#dddddd",
                tickfont=dict(color="#1e1e1e", size=12)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#eeeeee",
                tickprefix="฿",
                tickfont=dict(color="#1e1e1e", size=12)
            ),
            hoverlabel=dict(bgcolor="#1e1e1e", font_color="#ffffff", font_size=13)
        )
        st.plotly_chart(fig_sales, width='stretch', config={"displayModeBar": False})

with col_right:
    with st.container(key="card_category"):
        st.markdown('<p class="section-title">สัดส่วนหมวดหมู่</p>', unsafe_allow_html=True)

        fig_category = px.pie(
            category_data,
            names="หมวดหมู่",
            values="สัดส่วน",
            hole=0.62,
            color_discrete_sequence=["#FF7518", "#FFA05C", "#FFC08A", "#FFD9B3", "#FFEBD9"]
        )
        fig_category.update_traces(
            textinfo="percent",
            textfont_color="#1e1e1e",
            hovertemplate="<b>%{label}</b>: %{percent}<extra></extra>",
            marker=dict(line=dict(color="#ffffff", width=2))
        )
        fig_category.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=320,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=11, color="#1e1e1e")),
            font=CHART_FONT,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            annotations=[dict(text="100%", x=0.5, y=0.5, font_size=16, showarrow=False, font_color="#1e1e1e")]
        )
        st.plotly_chart(fig_category, width='stretch', config={"displayModeBar": False})

# ======== แถวที่ 2: สินค้าขายดี + สินค้าใกล้หมด ========
col_left2, col_right2 = st.columns(2)

with col_left2:
    with st.container(key="card_top"):
        st.markdown('<p class="section-title">สินค้าขายดี 5 อันดับ</p>', unsafe_allow_html=True)

        top_sorted = top_products.sort_values("จำนวนขาย")
        colors = ["#FFD9B3", "#FFC08A", "#FFA05C", "#FF8A3D", "#FF7518"]

        fig_top = go.Figure(go.Bar(
            x=top_sorted["จำนวนขาย"],
            y=top_sorted["สินค้า"],
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=top_sorted["จำนวนขาย"],
            texttemplate="%{text:,} ชิ้น",
            textposition="outside",
            textfont=dict(color="#1e1e1e", size=12),
            hovertemplate="<b>%{y}</b><br>ขายได้ %{x:,} ชิ้น<extra></extra>"
        ))
        fig_top.update_layout(
            margin=dict(l=0, r=40, t=10, b=0),
            height=300,
            xaxis=dict(visible=False),
            yaxis=dict(title=None, tickfont=dict(size=13, color="#1e1e1e")),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=CHART_FONT,
            bargap=0.35
        )
        st.plotly_chart(fig_top, width='stretch', config={"displayModeBar": False})

with col_right2:
    with st.container(key="card_stock"):
        st.markdown('<p class="section-title">สินค้าใกล้หมดสต็อก</p>', unsafe_allow_html=True)

        st.dataframe(
            low_stock,
            width='stretch',
            hide_index=True,
            column_config={
                "สินค้า": st.column_config.TextColumn("สินค้า", width="medium"),
                "คงเหลือ": st.column_config.ProgressColumn(
                    "คงเหลือ",
                    min_value=0,
                    max_value=30,
                    format="%d ชิ้น"
                ),
                "จุดสั่งซื้อ": st.column_config.NumberColumn("จุดสั่งซื้อ", format="%d ชิ้น")
            }
        )
        st.markdown("""
        <div class="alert-box">
            ⚠️ <b>4 รายการ</b> ต่ำกว่าจุดสั่งซื้อ — ควรเติมสต็อกโดยเร็ว
        </div>
        """, unsafe_allow_html=True)