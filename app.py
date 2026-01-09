import streamlit as st
import pandas as pd
import os
import base64
import subprocess
import sys
import streamlit.components.v1 as components

# --- IMPORT MODULE VISUALISASI SENDIRI ---
from visualization import visual 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="FairPrice Map - Anti Scam Gadget",
    page_icon="📱",
    layout="wide"
)

# --- 2. FUNGSI UTILITIES (CSS & GAMBAR) ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def get_img_as_base64(file_path):
    """Membaca file gambar, deteksi format, dan ubah ke Base64"""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    if file_path.lower().endswith(('.jpg', '.jpeg')):
        mime_type = "image/jpeg"
    elif file_path.lower().endswith('.png'):
        mime_type = "image/png"
    elif file_path.lower().endswith('.gif'):
        mime_type = "image/gif"
    else:
        mime_type = "image/png"
        
    return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"

def inject_sidebar_icons(icon_files):
    css_icons = ""
    for index, file_name in enumerate(icon_files):
        icon_path = os.path.join("icon", file_name)
        img_b64 = get_img_as_base64(icon_path)
        
        if img_b64:
            extra_style = ""
            bg_pos = "15px center"
            
            # --- LOGIKA KHUSUS UNTUK TOMBOL UPDATE ---
            if "update.png" in file_name:
                extra_style = """
                margin-top: 25rem !important;        /* Jarak jauh dari menu atas */
                border-top: 1px solid #e0e0e0;      /* Garis pemisah tipis */
                padding-top: 1rem !important;       /* Ruang di dalam kotak */
                border-radius: 0 !important;        /* Hilangkan radius atas */
                """
                bg_pos = "15px calc(1rem + 4px)" 
            
            css_icons += f"""
            /* Target Label Menu ke-{index+1} */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type({index + 1}) {{
                background-image: url("{img_b64}");
                background-repeat: no-repeat;
                background-position: {bg_pos};
                background-size: 20px 20px;
                padding-left: 45px !important;
                {extra_style}
            }}
            """
    
    custom_sidebar_css = """
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
        padding-bottom: 8rem !important; 
    }
    """
    
    final_css = css_icons + custom_sidebar_css
    st.markdown(f'<style>{final_css}</style>', unsafe_allow_html=True)

# Panggil CSS
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    load_css(css_path)
else:
    st.warning(f"⚠️ File style.css tidak ditemukan.")

# --- 3. KONFIGURASI ICON MENU ---
icon_list = [
    "beranda.png",
    "table.png",
    "statistik.png",
    "map.png",
    "update.png" 
]
inject_sidebar_icons(icon_list)

# --- 4. KONFIGURASI PATH DATA & SCRIPT ---
FOLDER_DATA = 'data'
FOLDER_SCRAPER = 'scraper' # Folder tempat script berada
FILE_DATA = os.path.join(FOLDER_DATA, 'hasil_analisis_final.xlsx')
FILE_MAP = os.path.join(FOLDER_DATA, 'peta_gadget_jawa.html')

# Path Lengkap ke Script Scraper
SCRIPT_SCRAPER = os.path.join(FOLDER_SCRAPER, 'scraper_olx_to_data.py')
SCRIPT_PROCESSOR = os.path.join(FOLDER_SCRAPER, 'processing.py')

# --- 5. LOAD DATA ---
@st.cache_data
def load_data():
    if os.path.exists(FILE_DATA):
        return pd.read_excel(FILE_DATA)
    return None

df = load_data()

# --- 6. SIDEBAR NAVIGASI ---
st.sidebar.title("FairPrice Map")

menu = st.sidebar.radio(
    "Pilih Menu:",
    ["Beranda", "Data & Statistik", "Visualisasi", "Map GIS", "Update Data"],
    label_visibility="collapsed"
)

# --- FOOTER STICKY ---
st.sidebar.markdown(
    """
    <div class="sidebar-footer">
        <p>© 2026 Project Sains Data<br>Anti Scam Initiative</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================================================================
# MENU 1: BERANDA
# ==============================================================================
if menu == "Beranda":
    st.title("🛡️ FairPrice Map: Sistem Patokan Harga Wajar")
    st.markdown("### *Analisis Spasial Disparitas Harga Smartphone Bekas di Pulau Jawa*")
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        ### 🚨 Masalah Sosial:
        Pembeli HP bekas di daerah sering tertipu:
        * **Scam:** Harga terlalu murah (Penipuan/Barang Rusak).
        * **Overpriced:** Harga dinaikkan semena-mena oleh tengkulak karena minim informasi.
        
        ### 💡 Solusi Inovasi:
        Sistem ini menggunakan **Big Data** dari kota besar sebagai 'Harga Acuan'.
        Jika harga di daerahmu menyimpang jauh dari acuan ini, sistem akan memberikan peringatan visual.
        """)
        st.info("👈 Silakan pilih menu di samping untuk melihat analisisnya.")

    with col2:
        st.write("#### Konsep Sistem:")
        st.success("""
        1. **Scraping:** Ambil data pasar real-time.
        2. **Processing:** Bersihkan & kategorikan data.
        3. **Visualisasi:** Deteksi anomali harga.
        4. **Mapping:** Petakan zona mahal vs murah.
        """)

# ==============================================================================
# MENU 2: DATASET
# ==============================================================================
elif menu == "Data & Statistik":
    st.title("📂 Eksplorasi Data Scraping")
    
    if df is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Listings", f"{len(df):,}")
        col2.metric("Harga Terendah", f"Rp {df['Harga_Int'].min():,.0f}")
        col3.metric("Harga Rata-rata", f"Rp {df['Harga_Int'].mean():,.0f}")
        col4.metric("Provinsi Terdata", f"{df['Provinsi'].nunique()}")
        
        st.divider()
        
        st.subheader("🔍 Filter Database")
        c1, c2 = st.columns(2)
        with c1:
            prov_filter = st.multiselect("Pilih Provinsi:", df['Provinsi'].unique(), default=df['Provinsi'].unique())
        with c2:
            brand_filter = st.multiselect("Pilih Brand:", df['Brand'].unique(), default=['Iphone', 'Samsung'])
        
        filtered_df = df[
            (df['Provinsi'].isin(prov_filter)) & 
            (df['Brand'].isin(brand_filter))
        ]
        
        st.dataframe(filtered_df[['Judul', 'Harga_Int', 'Brand', 'Kelas_Sosial', 'Provinsi', 'Lokasi_Detail']], use_container_width=True)
    else:
        st.error("⚠️ File data tidak ditemukan.")

# ==============================================================================
# MENU 3: VISUALISASI
# ==============================================================================
elif menu == "Visualisasi":
    st.title("📈 Analisis Interaktif Anti-Scam")
    
    if df is not None:
        tab1, tab2, tab3 = st.tabs(["⚠️ Scam Detector", "💰 Price Gap", "📊 Ekonomi Digital"])
        
        with tab1:
            st.subheader("Radar Deteksi Scam (Anomali Harga)")
            st.caption("Grafik ini interaktif! Arahkan mouse ke titik-titik di luar kotak untuk melihat detail.")
            brand_choice = st.selectbox("Pilih Brand:", df['Brand'].unique(), index=0)
            fig1 = visual.create_scam_detector(df, brand_choice)
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            st.subheader("Perbandingan Rata-rata Harga Antar Wilayah")
            st.caption("Membuktikan di mana tempat termurah untuk membeli gadget.")
            fig2 = visual.create_price_gap(df)
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            st.subheader("Profil Daya Beli Masyarakat")
            st.caption("Persentase HP Sultan vs Entry Level di setiap provinsi.")
            fig3 = visual.create_economic_profile(df)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Data belum dimuat.")

# ==============================================================================
# MENU 4: PETA GIS
# ==============================================================================
elif menu == "Map GIS":
    st.title("🗺️ Geo-Pricing Intelligence")
    st.write("Peta persebaran dominasi brand dan harga rata-rata.")
    
    if os.path.exists(FILE_MAP):
        with open(FILE_MAP, 'r', encoding='utf-8') as f:
            map_html = f.read()
        components.html(map_html, height=600, scrolling=True)
    else:
        st.error("⚠️ File peta tidak ditemukan.")

# ==============================================================================
# MENU 5: UPDATE DATA
# ==============================================================================
elif menu == "Update Data":
    st.title("⚙️ Update Database Real-Time")
    st.write("Fitur ini akan menjalankan **Bot Scraper** lalu **Data Processing** secara otomatis.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.warning("⚠️ **Perhatian:** Proses total memakan waktu 5-15 menit.")
        start_btn = st.button("🚀 Mulai Update Full", type="primary")
    
    with col2:
        st.subheader("Terminal Log:")
        log_container = st.empty()
        
        # --- FUNGSI REUSABLE UNTUK MENJALANKAN SCRIPT ---
        def run_script_in_subprocess(script_path, log_placeholder, current_logs):
            """Menjalankan script python via subprocess dan streaming output ke UI"""
            if not os.path.exists(script_path):
                log_placeholder.error(f"❌ File tidak ditemukan: {script_path}")
                return False, current_logs

            try:
                current_logs += f"\n🔵 [SYSTEM] Menjalankan: {script_path}...\n"
                log_placeholder.code(current_logs, language="bash")
                
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env["PYTHONUNBUFFERED"] = "1"

                process = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    bufsize=1,
                    encoding='utf-8', 
                    env=env
                )
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        current_logs += line 
                        # Update log di layar (batasi panjang agar tidak lag)
                        log_placeholder.code(current_logs[-4000:], language="bash")
                
                if process.returncode == 0:
                    current_logs += f"✅ [SUCCESS] {script_path} selesai.\n"
                    return True, current_logs
                else:
                    current_logs += f"❌ [ERROR] {script_path} gagal (Code {process.returncode}).\n"
                    return False, current_logs

            except Exception as e:
                current_logs += f"❌ [EXCEPTION] {e}\n"
                log_placeholder.code(current_logs, language="bash")
                return False, current_logs

        # --- EKSEKUSI BERANTAI (CHAINING) ---
        if start_btn:
            full_logs = ""
            
            # 1. JALANKAN SCRAPER
            success_scraper, full_logs = run_script_in_subprocess(SCRIPT_SCRAPER, log_container, full_logs)
            
            if success_scraper:
                # 2. JALANKAN PROCESSING (Hanya jika Scraper Berhasil)
                success_process, full_logs = run_script_in_subprocess(SCRIPT_PROCESSOR, log_container, full_logs)
                
                if success_process:
                    st.success("🎉 Seluruh proses selesai! Database telah diperbarui.")
                    st.balloons()
                    st.cache_data.clear() # Hapus cache agar data baru terbaca
                else:
                    st.error("⚠️ Scraper berhasil, tetapi Processing gagal.")
            else:
                st.error("⚠️ Proses Scraping gagal. Processing dibatalkan.")


