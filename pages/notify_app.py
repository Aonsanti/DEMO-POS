import streamlit as st

line_token = st.text_input(
    label="Channel Access Token", 
    placeholder="รหัสอนุญาตเข้าถึงช่องทางบริการ (Token)",
    autocomplete="off",
    type="password",
    key="input_token",
    label_visibility="collapsed"
)

line_user_id = st.text_input(
    label="User ID", 
    placeholder="User ID ผู้รับ",
    autocomplete="off",
    key="input_user_id",
    label_visibility="collapsed"
)

message = st.text_area(
    label="ข้อความแจ้งเตือน", 
    placeholder="แจ้งเตือนการอัปเดตข้อมูลตำแหน่งสินค้าจากระบบ Store Demo",
    key="textarea_message",
    label_visibility="collapsed",
    height=400
)

# Button
col1, col2 = st.columns([3, 3])

with col1:
    send_clicked = st.button(
        "ส่งข้อความ",
        key="btn_primary",
        width='stretch'
    )

with col2:
    cancel_clicked = st.button(
        "ยกเลิก",
        key="btn_secondary", 
        width='stretch'
    )

if send_clicked:
    errors = []
    if not line_token.strip():
        errors.append("Channel Access Token")
    if not line_user_id.strip():
        errors.append("User ID")
    if not message.strip():
        errors.append("ข้อความแจ้งเตือน")

    if errors:
        st.error(f"กรุณากรอกข้อมูลให้ครบ: {', '.join(errors)}")
    else:
        st.success("ส่งข้อความเรียบร้อยแล้ว ✅")

if cancel_clicked:
    st.info("ยกเลิกการส่งข้อความแล้ว")