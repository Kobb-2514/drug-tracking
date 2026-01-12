import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Drug Box Tracking Dashboard : Tha Tum Hospital", layout="wide", page_icon="💊")

# --- ส่วนของการจัดการข้อมูล ---
@st.cache_data(ttl=60)
def load_data():
    # -------------------------------------------------------------
    # 🔴 สำคัญ! นำลิงก์จากขั้นตอนที่ 1 (Publish to web) มาวางแทนที่ตรงนี้
    gsheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQA2BrARJBp5oYf1cjTBdaU1Bi82FhtqO6TjDkVXoGQVNLSGQHGlhrIG15tV9FlhOw30meuha29Hq5Z/pub?output=csv"
    # ตัวอย่าง: "https://docs.google.com/spreadsheets/d/e/2PACX.../pub?output=csv"
    # -------------------------------------------------------------
    
    try:
        df = pd.read_csv(gsheet_url)
        
        # Clean Data
        if 'DayLeft' in df.columns:
            df['DayLeft'] = df['DayLeft'].astype(str).str.replace(',', '').str.replace('"', '')
            df['DayLeft'] = pd.to_numeric(df['DayLeft'], errors='coerce').fillna(0).astype(int)
        
        df = df.fillna("ไม่ระบุ")
        
        def get_status(day_left):
            if day_left < 0: return "Expired (หมดอายุ)"
            elif day_left <= 90: return "Expiring Soon (ใกล้หมด)"
            else: return "OK (ปกติ)"
        
        if 'DayLeft' in df.columns:
            df['Status'] = df['DayLeft'].apply(get_status)
            
        return df
    except Exception as e:
        st.error(f"ไม่สามารถดึงข้อมูลได้: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("กรุณาตรวจสอบลิงก์ Google Sheet ในโค้ดอีกครั้ง")
    st.stop()

# --- ส่วน Sidebar (Menu & Filters) ปรับปรุงใหม่ ---
st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")
st.sidebar.markdown("เลือกรายการที่ต้องการกรอง (ปล่อยว่าง = เลือกทั้งหมด)")

# 1. Filter ประเภทกล่อง (Drop Down)
# ดึงข้อมูลที่ไม่ซ้ำมาทำตัวเลือก
type_options = sorted(df['ประเภท กล่อง'].astype(str).unique())
selected_types = st.sidebar.multiselect("1. ประเภทกล่อง", options=type_options)

# 2. Filter ตำแหน่งกล่อง (Drop Down)
loc_options = sorted(df['ตำเเหน่งกล่อง'].astype(str).unique())
selected_locs = st.sidebar.multiselect("2. ตำแหน่งกล่อง", options=loc_options)

# 3. Filter สถานะยา/DayLeft (Drop Down แทน Slider)
# แปลง DayLeft เป็นกลุ่มเพื่อให้เลือกง่าย
status_options = sorted(df['Status'].unique())
selected_status = st.sidebar.multiselect("3. สถานะ (หมดอายุ/ปกติ)", options=status_options)

# 4. Filter ยาที่หมดอายุไวสุด (Drop Down แทนพิมพ์ค้นหา)
drug_options = sorted(df['ยาที่หมดอายุไวสุด'].astype(str).unique())
selected_drugs = st.sidebar.multiselect("4. ชื่อยา (Drug Name)", options=drug_options)

# 5. Filter ชื่อกล่อง (Drop Down แทนพิมพ์ค้นหา)
box_name_options = sorted(df['ชื่อกล่อง'].astype(str).unique())
selected_box_names = st.sidebar.multiselect("5. ชื่อกล่อง", options=box_name_options)


# --- Apply Filters (Logic การกรองข้อมูล) ---
# สร้างตัวแปร filtered_df เพื่อไม่ให้กระทบข้อมูลหลัก
filtered_df = df.copy()

# ถ้ามีการเลือกตัวเลือก ให้ทำการกรอง (ถ้าไม่เลือก ให้ข้ามไปแสดงทั้งหมด)
if selected_types:
    filtered_df = filtered_df[filtered_df['ประเภท กล่อง'].isin(selected_types)]

if selected_locs:
    filtered_df = filtered_df[filtered_df['ตำเเหน่งกล่อง'].isin(selected_locs)]

if selected_status:
    filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]

if selected_drugs:
    filtered_df = filtered_df[filtered_df['ยาที่หมดอายุไวสุด'].isin(selected_drugs)]

if selected_box_names:
    filtered_df = filtered_df[filtered_df['ชื่อกล่อง'].isin(selected_box_names)]

# อัปเดตตัวแปร df ให้เป็นตัวที่กรองแล้ว เพื่อส่งต่อไปยังกราฟและตาราง
df = filtered_df

# --- Main Dashboard ---
st.title("💊 Drug Box Tracking Dashboard")
st.markdown("---")

# KPI Cards
c1, c2, c3 = st.columns(3)
c1.metric("📦 กล่องทั้งหมด", f"{len(df)} กล่อง")
c2.metric("🔴 หมดอายุแล้ว", f"{len(df[df['DayLeft'] < 0])} กล่อง")
c3.metric(" ใกล้หมด (<90วัน)", f"{len(df[(df['DayLeft'] >= 0) & (df['DayLeft'] <= 90)])} กล่อง")

# Charts
col_chart1, col_chart2 = st.columns([3, 2])
with col_chart1:
    if 'ตำเเหน่งกล่อง' in df.columns:
        counts = df['ตำเเหน่งกล่อง'].value_counts().reset_index()
        counts.columns = ['Location', 'Count']
        fig = px.bar(counts, x='Location', y='Count', title="จำนวนกล่องตามตำแหน่ง", text='Count')
        st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig2 = px.pie(status_counts, values='Count', names='Status', title="สัดส่วนสถานะยา", hole=0.4, 
                      color='Status', color_discrete_map={"Expired (หมดอายุ)":"red", "OK (ปกติ)":"green", "Expiring Soon (ใกล้หมด)":"orange"})
        st.plotly_chart(fig2, use_container_width=True)

# Table
st.markdown("### 📋 รายละเอียด")
def color_survived(val):
    color = '#ffcccc' if val == "Expired (หมดอายุ)" else '#ffebcc' if val == "Expiring Soon (ใกล้หมด)" else ''
    return f'background-color: {color}'

st.dataframe(df.style.map(color_survived, subset=['Status']), use_container_width=True)
