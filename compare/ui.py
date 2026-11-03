from urllib.parse import quote

import pandas as pd
import streamlit as st

from . import stores


@st.cache_data(ttl=600, show_spinner=False)
def run_search(queries, shop_names, per_store):
    return stores.search_all(list(queries), list(shop_names), per_store)


def render():
    st.title("🛒 เทียบราคาหลายร้าน")
    st.caption("ค้นสินค้าเดียวกันจาก 7-Eleven, Lotus's, Big C และ All Online พร้อมกัน แล้วดูในตารางเดียว")

    # ── controls ─────────────────────────────────────────────
    chosen = st.multiselect("ร้านที่ต้องการเทียบ", list(stores.STORES), default=list(stores.STORES))
    c_q, c_n, c_go = st.columns([6, 2, 1.2], vertical_alignment="bottom")
    with c_q:
        raw = st.text_input("สินค้า (หลายรายการคั่นด้วย , )", key="pc_query",
                            placeholder="เช่น น้ำดื่ม 600 มล., โอวัลติน, นมโฟร์โมสต์")
    with c_n:
        limit = st.slider("จำนวนต่อร้าน", 3, 12, 6)
    with c_go:
        go = st.button("เทียบราคา", type="primary", width="stretch")


    if go:
        queries = tuple(q.strip() for q in raw.split(",") if q.strip())
        if not queries:
            st.warning("กรุณาพิมพ์ชื่อสินค้าอย่างน้อย 1 รายการ")
        elif not chosen:
            st.warning("เลือกอย่างน้อย 1 ร้าน")
        else:
            with st.spinner(f"กำลังค้น {len(queries)} รายการ × {len(chosen)} ร้าน ..."):
                st.session_state["pc"] = {"queries": queries, "stores": tuple(chosen),
                                          "data": run_search(queries, tuple(chosen), limit)}

    state = st.session_state.get("pc")
    if not state:
        st.info("พิมพ์ชื่อสินค้าแล้วกด 'เทียบราคา' — ร้าน 7-Eleven มีเฉพาะสินค้าใหม่/เครื่องดื่ม All Café ที่เว็บแสดง ไม่ใช่ทุกสินค้า")
        st.stop()

    queries, shop_names, data = state["queries"], state["stores"], state["data"]


    def best(products):
        """Highest relevance; among near-ties the cheapest."""
        if not products:
            return None
        top = max(p["relevance"] for p in products)
        near = [p for p in products if p["relevance"] >= top - 0.05]
        priced = [p for p in near if p["price"]]
        return min(priced, key=lambda p: p["price"]) if priced else near[0]


    # store problems (blocked, down) — shown once per store
    for s in shop_names:
        err = next((data[q][s]["error"] for q in queries if data[q][s]["error"]), None)
        if err:
            st.warning(f"**{s}**: {err}")

    # ── 1) one comparison table ──────────────────────────────
    st.subheader("ตารางเทียบราคา")
    st.caption("แต่ละช่อง = สินค้าที่ตรงคำค้นที่สุดของร้านนั้น (เขียวคือถูกสุดในแถว) — เทียบราคาต่อ 100 มล./กรัมได้ในตารางด้านล่าง")
    rows, prices = [], []
    for q in queries:
        row, price_row = {"สินค้าที่ค้นหา": q}, {}
        for s in shop_names:
            b = best(data[q][s]["products"])
            if b and b["price"]:
                row[s] = f"฿{b['price']:g}  ·  {b['name']}"
                price_row[s] = b["price"]
            elif b:   # found, but the site shows no price in text (promotion page, price only in picture)
                row[s] = f"🏷️ {b['name']}  (ดูราคาที่ลิงก์)"
            else:
                row[s] = "⚠️ ใช้ไม่ได้" if data[q][s]["error"] else "— ไม่พบ"
        if price_row:
            cheapest = min(price_row, key=price_row.get)
            row["ถูกสุด"] = cheapest
            row["ต่างจากแพงสุด"] = f"฿{max(price_row.values()) - price_row[cheapest]:g}" if len(price_row) > 1 else "-"
        else:
            row["ถูกสุด"], row["ต่างจากแพงสุด"] = "-", "-"
        rows.append(row)
        prices.append(price_row)

    pivot = pd.DataFrame(rows)


    def paint(row):
        pr = prices[row.name]
        low = min(pr.values()) if len(pr) > 1 else None
        return [("background-color:#d1fae5;color:#065f46;font-weight:600"
                 if low is not None and col in pr and pr[col] == low else "") for col in row.index]


    st.dataframe(pivot.style.apply(paint, axis=1), hide_index=True, width="stretch")

    # ── 2) every candidate in one table (select 1-4 rows to compare) ──
    st.subheader("สินค้าทั้งหมดที่พบ")
    flat = []
    for q in queries:
        for s in shop_names:
            for p in data[q][s]["products"]:
                flat.append({"คำค้น": q, "ร้าน": s, "สินค้า": p["name"], "ราคา": p["price"], "หมายเหตุ": p.get("note", ""),
                             "ราคาปกติ": p["regular_price"] or p["price"], "ราคา/100": p["per100"],
                             "หน่วย": {"ml": "มล.", "g": "กรัม"}.get(p["unit"], ""), "ตรงคำค้น": p["relevance"],
                             "มีของ": "✅" if p["in_stock"] else "หมด", "ลิงก์": p["url"], "_img": p["image"]})
    if not flat:
        st.error("ไม่พบสินค้าที่ตรงกับคำค้นในร้านที่เลือก ลองใช้คำสั้นลง เช่น ชื่อแบรนด์หรือชนิดสินค้า")
        for q in queries:
            st.write(f"ค้นเองใน: " + " · ".join(f"[{s}]({stores.HOME[s].format(q=quote(q))})" for s in shop_names))
        st.stop()

    df = pd.DataFrame(flat)
    f1, f2 = st.columns([2, 1])
    with f1:
        only_q = st.selectbox("แสดงคำค้น", ["ทั้งหมด"] + list(queries)) if len(queries) > 1 else "ทั้งหมด"
    with f2:
        sort_by = st.selectbox("เรียงตาม", ["ตรงคำค้นมากสุด", "ราคาต่ำสุด", "ราคา/100 ต่ำสุด"])
    view = df if only_q == "ทั้งหมด" else df[df["คำค้น"] == only_q]
    view = view.sort_values({"ตรงคำค้นมากสุด": ["ตรงคำค้น", "ราคา"], "ราคาต่ำสุด": ["ราคา"],
                             "ราคา/100 ต่ำสุด": ["ราคา/100"]}[sort_by],
                            ascending=[False, True] if sort_by == "ตรงคำค้นมากสุด" else True).reset_index(drop=True)

    event = st.dataframe(
        view.drop(columns="_img"), hide_index=True, width="stretch", on_select="rerun", selection_mode="multi-row",
        column_config={
            "ราคา": st.column_config.NumberColumn(format="฿%g"),
            "ราคาปกติ": st.column_config.NumberColumn(format="฿%g"),
            "ราคา/100": st.column_config.NumberColumn(format="฿%.2f", help="ราคาต่อ 100 มล. หรือ 100 กรัม (คำนวณจากขนาดในชื่อสินค้า; ประมาณ)"),
            "ตรงคำค้น": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.0f%%"),
            "ลิงก์": st.column_config.LinkColumn(display_text="เปิด"),
        })

    # ── 3) side-by-side for the rows the user ticks ──────────
    picked = view.iloc[event.selection.rows[:4]] if event.selection.rows else view.iloc[0:0]
    if picked.empty:
        st.caption("💡 ติ๊กแถวด้านบน 1–4 รายการ เพื่อดูเทียบกันแบบเคียงข้างกัน")
    else:
        st.subheader("เทียบสินค้าที่เลือก")
        low_price = picked["ราคา"].min()
        per = picked["ราคา/100"].dropna()
        low_per = per.min() if len(per) > 1 and picked["หน่วย"].nunique() == 1 else None
        for col, (_, p) in zip(st.columns(len(picked)), picked.iterrows()):
            with col, st.container(border=True):
                if isinstance(p["_img"], str) and p["_img"]:
                    st.image(p["_img"], width=110)
                st.caption(p["ร้าน"])
                st.markdown(f"**{p['สินค้า']}**")
                if pd.isna(p["ราคา"]):   # no price in the page text (e.g. promotion): send the user to the page
                    st.write("💬 ไม่มีราคาในข้อความ — ดูที่ลิงก์")
                else:
                    delta = "ถูกสุด" if p["ราคา"] == low_price and len(picked) > 1 else (
                        f"+฿{p['ราคา'] - low_price:g}" if len(picked) > 1 else None)
                    st.metric("ราคา", f"฿{p['ราคา']:g}", delta,
                              delta_color="inverse" if delta and delta != "ถูกสุด" else "normal", delta_arrow="off")
                if p.get("หมายเหตุ"):
                    st.caption(p["หมายเหตุ"])
                if pd.notna(p["ราคา/100"]):
                    tag = " ✅ คุ้มสุด" if low_per is not None and p["ราคา/100"] == low_per else ""
                    st.write(f"฿{p['ราคา/100']:.2f} / 100 {p['หน่วย']}{tag}")
                if pd.notna(p["ราคาปกติ"]) and p["ราคาปกติ"] != p["ราคา"]:
                    st.write(f"ราคาปกติ ฿{p['ราคาปกติ']:g}")
                st.link_button("เปิดหน้าสินค้า", p["ลิงก์"], width="stretch")
