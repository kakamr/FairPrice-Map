import streamlit as st
import pandas as pd
import os
import base64
import subprocess
import sys
import streamlit.components.v1 as components
from visualization import visual 

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="FairPrice Map", page_icon="📱", layout="wide")

# Constants
FOLDER_DATA = 'data'
FOLDER_VIEWS = 'views' # Folder HTML baru
FILE_DATA = os.path.join(FOLDER_DATA, 'hasil_analisis_final.xlsx')
FILE_MAP = os.path.join(FOLDER_DATA, 'peta_gadget_jawa.html')
SCRIPT_SCRAPER = os.path.join('scraper', 'scraper_olx.py')
SCRIPT_PROCESSOR = os.path.join('processing', 'processing.py')

# --- 2. HELPER FUNCTIONS (Logic Murni) ---
def render_view(filename):
    """Membaca file HTML dari folder views dan menampilkannya"""
    path = os.path.join(FOLDER_VIEWS, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            st.markdown(f.read(), unsafe_allow_html=True)
    else:
        st.error(f"View {filename} tidak ditemukan.")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    if os.path.exists(FILE_DATA): return pd.read_excel(FILE_DATA)
    return None

def run_script(script_path, log_placeholder, current_logs):
    """Logika menjalankan subprocess Python"""
    if not os.path.exists(script_path):
        return False, current_logs + f"\n❌ File hilang: {script_path}\n"
    
    try:
        current_logs += f"\n🔵 [RUN] {script_path}...\n"
        log_placeholder.code(current_logs, language="bash")
        
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', env=env)
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None: break
            if line:
                current_logs += line 
                log_placeholder.code(current_logs[-4000:], language="bash")
        
        success = (process.returncode == 0)
        status = "✅ SELESAI" if success else "❌ GAGAL"
        current_logs += f"{status}: {script_path}\n"
        return success, current_logs
    except Exception as e:
        return False, current_logs + f"❌ Exception: {e}\n"

# --- 3. INIT ASSETS ---
load_css(os.path.join("assets", "style.css"))
df = load_data()

# --- 4. SIDEBAR ---
st.sidebar.title("FairPrice Map")
menu = st.sidebar.radio("Menu", ["Beranda", "Data & Statistik", "Visualisasi", "Map GIS", "Update Data"], label_visibility="collapsed")
st.sidebar.markdown('<div class="sidebar-footer"><p>© 2026 Project Sains Data</p></div>', unsafe_allow_html=True)

# ==============================================================================
# ROUTING MENU (LOGIC ONLY)
# ==============================================================================

if menu == "Beranda":
    # Tampilan dipindah total ke HTML
    render_view("beranda.html")

elif menu == "Data & Statistik":
    st.title("📂 Eksplorasi Data")
    if df is not None:
        # Metric Logic
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Listings", f"{len(df):,}")
        c2.metric("Termurah", f"Rp {df['Harga_Int'].min():,.0f}")
        c3.metric("Rata-rata", f"Rp {df['Harga_Int'].mean():,.0f}")
        c4.metric("Provinsi", f"{df['Provinsi'].nunique()}")
        
        st.divider()
        
        # Filter Logic
        c1, c2 = st.columns(2)
        prov = c1.multiselect("Provinsi:", df['Provinsi'].unique(), default=df['Provinsi'].unique())
        brand = c2.multiselect("Brand:", df['Brand'].unique(), default=['Iphone', 'Samsung'])
        
        # Dataframe View
        st.dataframe(df[(df['Provinsi'].isin(prov)) & (df['Brand'].isin(brand))], use_container_width=True)
    else:
        st.error("Data belum tersedia. Silakan Update Data.")

elif menu == "Visualisasi":
    st.title("📈 Analisis Interaktif")
    if df is not None:
        t1, t2, t3 = st.tabs(["Scam Detector", "Price Gap", "Ekonomi"])
        
        with t1:
            brand = st.selectbox("Pilih Brand:", df['Brand'].unique())
            st.plotly_chart(visual.create_scam_detector(df, brand), use_container_width=True)
        with t2:
            st.plotly_chart(visual.create_price_gap(df), use_container_width=True)
        with t3:
            st.plotly_chart(visual.create_economic_profile(df), use_container_width=True)
    else:
        st.warning("Data kosong.")

elif menu == "Map GIS":
    st.title("🗺️ Geo-Pricing Map")
    if os.path.exists(FILE_MAP):
        with open(FILE_MAP, 'r', encoding='utf-8') as f:
            components.html(f.read(), height=600)
    else:
        st.error("Peta belum digenerate.")

elif menu == "Update Data":
    # Header dari HTML
    render_view("update.html") 
    
    # Logic Tombol & Script
    col1, col2 = st.columns([1, 2])
    with col1:
        st.warning("⚠️ Estimasi waktu: 5-15 menit.")
        if st.button("🚀 Mulai Update Full", type="primary"):
            logs = ""
            log_box = col2.empty()
            
            # Chain Execution
            ok_scrape, logs = run_script(SCRIPT_SCRAPER, log_box, logs)
            if ok_scrape:
                ok_proc, logs = run_script(SCRIPT_PROCESSOR, log_box, logs)
                if ok_proc:
                    st.success("Selesai!")
                    st.cache_data.clear()
            else:
                st.error("Gagal di Scraping.")
