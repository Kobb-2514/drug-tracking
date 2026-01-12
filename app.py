import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Drug Box Tracking Dashboard", layout="wide", page_icon="💊")

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

# --- ส่วน Sidebar ---
st.sidebar.title("🔍 ตัวกรอง (Filter)")
if 'ประเภท กล่อง' in df.columns:
    box_types = st.sidebar.multiselect("ประเภทกล่อง", df['ประเภท กล่อง'].unique(), df['ประเภท กล่อง'].unique())
    df = df[df['ประเภท กล่อง'].isin(box_types)]

if 'ตำเเหน่งกล่อง' in df.columns:
    locations = st.sidebar.multiselect("ตำแหน่ง", df['ตำเเหน่งกล่อง'].unique(), df['ตำเเหน่งกล่อง'].unique())
    df = df[df['ตำเเหน่งกล่อง'].isin(locations)]

# --- Main Dashboard ---
st.title("💊 Drug Box Tracking Dashboard")
st.markdown("---")

# KPI Cards
c1, c2, c3 = st.columns(3)
c1.metric("📦 กล่องทั้งหมด", f"{len(df)} กล่อง")
c2.metric("🔴 หมดอายุแล้ว", f"{len(df[df['DayLeft'] < 0])} กล่อง")
c3.metric("jq ใกล้หมด (<90วัน)", f"{len(df[(df['DayLeft'] >= 0) & (df['DayLeft'] <= 90)])} กล่อง")

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
