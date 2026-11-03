import streamlit as st

from data import shelf_store

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
        st.session_state.pop("shelf_query", None)
    else:
        # keep the query so the result (and its button) survive the next rerun
        st.session_state["shelf_query"] = search_query.strip()

query = st.session_state.get("shelf_query")
if query:
    if not any(w["shelves"] for w in shelf_store.load()["warehouses"]):
        st.info("ยังไม่มีข้อมูลชั้นวาง — เปิดหน้า Stock 2D หนึ่งครั้งเพื่อสร้างข้อมูลก่อน")
    else:
        rows = shelf_store.search(query)
        if not rows:
            st.error(f"ไม่พบสินค้า: {query}")
        else:
            st.success(f"พบ {len(rows)} ตำแหน่ง ใน {len({(r['wh_id'], r['ชั้น']) for r in rows})} ชั้น — ค้นหา: {query}")
            st.dataframe(rows, hide_index=True, width='stretch', column_config={"wh_id": None})
            if st.button("🗺️ เปิดใน Stock 2D", key="btn_open_2d"):
                st.session_state["focus"] = {"query": query, "wh": rows[0]["wh_id"]}
                st.switch_page("pages/stock2d.py")
