import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บ (Page Config)
st.set_page_config(
    page_title="Drug Box Tracking : Tha Tum Hospital", 
    layout="wide", 
    page_icon="💊",
    initial_sidebar_state="collapsed" # ในมือถือให้ซ่อนเมนูก่อน เพื่อความสะอาดตา
)

# 2. 📱 CSS Hack: ปรับแต่งให้เข้ากับมือถือ (ลดขอบ, ซ่อน Footer)
st.markdown("""
    <style>
        /* ลดขอบขาวด้านบนสุด (Header padding) */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        /* ปรับขนาดตัวหนังสือ Metric ให้พอดีมือถือ */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        /* ซ่อน Footer "Made with Streamlit" เพื่อความเนียน */
        footer {visibility: hidden;}
        /* ปรับระยะห่างระหว่างบรรทัดให้แน่นขึ้น */
        .stMarkdown {margin-bottom: -10px;}
    </style>
""", unsafe_allow_html=True)

# --- ส่วนของการจัดการข้อมูล ---
@st.cache_data(ttl=60)
def load_data():
    # -------------------------------------------------------------
    # 🔴 ใส่ Link CSV ของคุณที่นี่
    gsheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQA2BrARJBp5oYf1cjTBdaU1Bi82FhtqO6TjDkVXoGQVNLSGQHGlhrIG15tV9FlhOw30meuha29Hq5Z/pub?output=csv" 
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

# --- ส่วน Sidebar (ตัวกรองแบบ Dropdown) ---
st.sidebar.header("🔍 ตัวกรอง (Filters)")
st.sidebar.markdown("กดที่ช่องเพื่อเลือกรายการ")

filtered_df = df.copy()

# ฟังก์ชันสร้าง Dropdown ให้โค้ดสั้นลง
def create_filter(label, col_name):
    if col_name in df.columns:
        options = sorted(df[col_name].astype(str).unique())
        selected = st.sidebar.multiselect(label, options)
        if selected:
            return filtered_df[filtered_df[col_name].isin(selected)]
    return filtered_df

filtered_df = create_filter("1. ประเภทกล่อง", "ประเภท กล่อง")
filtered_df = create_filter("2. ตำแหน่ง", "ตำเเหน่งกล่อง")
filtered_df = create_filter("3. สถานะ", "Status")
filtered_df = create_filter("4. ชื่อยา", "ยาที่หมดอายุไวสุด")

# --- Main Dashboard ---
st.title("💊 Drug Box Tracking")
st.caption("Tha Tum Hospital") # ใช้ Caption แทนชื่อยาวๆ เพื่อประหยัดพื้นที่แนวตั้ง

# ปุ่ม Action (Update / Edit)
c_edit, c_refresh = st.columns([1, 1])
with c_edit:
    # 🔴 ใส่ Link Google Sheet หน้า Edit ที่นี่
    st.link_button("📝 แก้ไข (Sheet)", "https://docs.google.com/spreadsheets/d/xxxxxx/edit", use_container_width=True)
with c_refresh:
    if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# KPI Cards (บนมือถือจะเรียงลงมาเอง, บนคอมฯ จะเรียงหน้ากระดาน 3 ช่อง)
col1, col2, col3 = st.columns(3)
total = len(filtered_df)
expired = len(filtered_df[filtered_df['DayLeft'] < 0])
soon = len(filtered_df[(filtered_df['DayLeft'] >= 0) & (filtered_df['DayLeft'] <= 90)])

col1.metric("📦 ทั้งหมด", f"{total}", "กล่อง")
col2.metric("🔴 หมดอายุ", f"{expired}", "กล่อง", delta_color="inverse")
col3.metric("jq ใกล้หมด", f"{soon}", "กล่อง", delta_color="off")

# Charts (กราฟ)
st.markdown("### 📊 ภาพรวม")

# ใช้ Tab เพื่อประหยัดพื้นที่หน้าจอมือถือ (ไม่ต้องไถยาวๆ)
tab1, tab2 = st.tabs(["📍 ตามตำแหน่ง", "🍰 สัดส่วนสถานะ"])

with tab1:
    if 'ตำเเหน่งกล่อง' in filtered_df.columns:
        counts = filtered_df['ตำเเหน่งกล่อง'].value_counts().reset_index()
        counts.columns = ['Location', 'Count']
        # ปรับความสูงกราฟให้พอดีมือถือ (height=350)
        fig = px.bar(counts, x='Location', y='Count', text='Count', height=350)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0)) # ลดขอบกราฟ
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    if 'Status' in filtered_df.columns:
        status_counts = filtered_df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig2 = px.pie(status_counts, values='Count', names='Status', hole=0.4, height=350,
                      color='Status', color_discrete_map={"Expired (หมดอายุ)":"#FF4B4B", "OK (ปกติ)":"#00CC96", "Expiring Soon (ใกล้หมด)":"#FFA500"})
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=-0.1)) # เอา Legend ไว้ข้างล่าง
        st.plotly_chart(fig2, use_container_width=True)

# Table (ตาราง)
st.markdown("### 📋 รายละเอียด")
# เลือกแสดงเฉพาะคอลัมน์ที่จำเป็น เพื่อไม่ให้ตารางกว้างเกินไปบนมือถือ
show_cols = ['ชื่อกล่อง', 'ตำเเหน่งกล่อง', 'DayLeft', 'Status']
# ถ้ามีคอลัมน์ครบ ให้โชว์ ถ้าไม่ครบก็โชว์หมด
final_cols = [c for c in show_cols if c in filtered_df.columns]
if not final_cols: final_cols = filtered_df.columns

def color_survived(val):
    color = '#ffcccc' if val == "Expired (หมดอายุ)" else '#ffebcc' if val == "Expiring Soon (ใกล้หมด)" else ''
    return f'background-color: {color}'

st.dataframe(
    filtered_df[final_cols].style.map(color_survived, subset=['Status'] if 'Status' in final_cols else None),
    use_container_width=True,
    hide_index=True # ซ่อนเลขบรรทัด 0,1,2 เพื่อประหยัดที่
)
