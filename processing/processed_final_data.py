import pandas as pd
import os
import glob
import sys
from github import Github, Auth # Tambah Auth untuk login cara baru
import streamlit as st

# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_FILENAME = 'hasil_analisis_final.xlsx'
OUTPUT_FILE_PATH = os.path.join(DATA_DIR, OUTPUT_FILENAME)

# --- KONFIGURASI GITHUB ---
# PASTIKAN INI BENAR (Huruf besar/kecil berpengaruh)
# Format: "UsernameGithub/NamaRepository"
REPO_NAME = "kakamr/FairPrice-Map" 

def upload_to_github(file_path, repo_name, file_name_in_repo):
    """Fungsi untuk Push file ke GitHub dengan Auth terbaru"""
    try:
        # Ambil token dari Secrets
        token = st.secrets["github"]["token"]
        
        # Login menggunakan metode Auth.Token (Anti Deprecation Warning)
        auth = Auth.Token(token)
        g = Github(auth=auth)
        
        # Cek User Login (Opsional, buat debug)
        user = g.get_user()
        print(f"🔑 Login sebagai: {user.login}")

        # Ambil Repo
        print(f"🔍 Mencari repo: {repo_name}...")
        repo = g.get_repo(repo_name)
        
        # Baca file Excel binary
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Path di dalam repo
        repo_path = f"data/{file_name_in_repo}"
        
        try:
            # Cek apakah file sudah ada
            contents = repo.get_contents(repo_path)
            # UPDATE (Commit message berbeda biar kelihatan update)
            repo.update_file(contents.path, f"Auto-update: {file_name_in_repo}", content, contents.sha)
            print(f"✅ GitHub: File '{repo_path}' berhasil di-UPDATE.")
        except:
            # CREATE (Jika file belum ada)
            repo.create_file(repo_path, f"Auto-create: {file_name_in_repo}", content)
            print(f"✅ GitHub: File '{repo_path}' berhasil di-UPLOAD baru.")
            
    except Exception as e:
        print(f"❌ Gagal Push ke GitHub: {e}")
        print("💡 Tips: Cek 'repo' permission di GitHub Token Anda & pastikan nama REPO_NAME benar.")

def process_data():
    print(f"⚙️ Memulai Processing & Sync...")

    # 1. Load CSV
    search_path = os.path.join(DATA_DIR, "*.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files: 
        print("❌ Tidak ada file CSV ditemukan.")
        return
    
    df_list = []
    for f in csv_files:
        try:
            df_list.append(pd.read_csv(f))
        except: pass
        
    if not df_list: return

    df = pd.concat(df_list, ignore_index=True)
    
    # 2. Cleaning & Processing
    # (Logika Cleaning kamu)
    df['Harga_Clean'] = df['Harga'].astype(str).str.replace('Rp', '').str.replace('.', '').str.strip()
    df['Harga_Int'] = pd.to_numeric(df['Harga_Clean'], errors='coerce').fillna(0).astype(int)

    def categorize_class(price):
        if price > 5000000: return 'Flagship/Sultan'
        elif 2000000 <= price <= 5000000: return 'Mid Range'
        else: return 'Entry Level'

    df['Kelas_Sosial'] = df['Harga_Int'].apply(categorize_class)
    
    # Ekstraksi Brand Sederhana
    brands = ['iphone', 'samsung', 'xiaomi', 'oppo', 'vivo', 'realme', 'infinix', 'asus', 'poco']
    def extract_brand(title):
        t = str(title).lower()
        for b in brands:
            if b in t: return b.capitalize()
        return 'Lainnya'
    df['Brand'] = df['Judul'].apply(extract_brand)
    
    # 3. Hapus Duplikat
    df.drop_duplicates(subset=['Judul', 'Harga_Int', 'Lokasi_Detail'], keep='first', inplace=True)
    print(f"📊 Total Data Bersih: {len(df)}")

    # 4. SIMPAN LOKAL & PUSH
    try:
        # Simpan lokal dulu (wajib)
        df.to_excel(OUTPUT_FILE_PATH, index=False)
        print(f"💾 Simpan Lokal OK.")
        
        # Upload ke GitHub
        print("☁️ Mengupload ke GitHub...")
        upload_to_github(OUTPUT_FILE_PATH, REPO_NAME, OUTPUT_FILENAME)
        
    except Exception as e:
        print(f"❌ Error Saving: {e}")

if __name__ == "__main__":
    process_data()
