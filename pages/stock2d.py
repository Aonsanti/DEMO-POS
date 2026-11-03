import streamlit as st

from components.stock2d_canvas import canvas
from data import shelf_store

st.title("📦 Stock 2D Layout")
st.caption("จัดวางสินค้าบนชั้นวาง 2D — เพิ่มช่อง, ลากวางช่อง, ปรับขนาด, คลิกเพื่อดูและแก้ไขสินค้า")

st.divider()

data = shelf_store.load()
# "focus" comes from Shelf Management: open that warehouse with the search filled in.
focus = st.session_state.pop("focus", {})
result = canvas(
    data=data,
    query=focus.get("query", ""),
    focus_wh=focus.get("wh"),
    key="stock2d",
    default=None,
)

# The canvas sends its full state after every change; save it so Shelf Management sees the same data.
if result is not None and result != data:
    shelf_store.save(result)
