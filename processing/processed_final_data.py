import pandas as pd
import os
import glob
import sys
from github import Github # Perlu install: pip install PyGithub
import streamlit as st

# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_FILENAME = 'hasil_analisis_final.xlsx' # Nama file saja
OUTPUT_FILE_PATH = os.path.join(DATA_DIR, OUTPUT_FILENAME)

# --- KONFIGURASI GITHUB ---
# Ganti sesuai nama repo kamu: "username/nama-repo"
REPO_NAME = "kakamr/FairPrice-Map" 
GITHUB_TOKEN = st.secrets["github"]["token"] # Ambil dari Secrets

def upload_to_github(file_path, repo_name, file_name_in_repo):
    """Fungsi untuk Push file ke GitHub"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        
        # Baca file Excel binary
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Path di dalam repo (misal: data/hasil_analisis_final.xlsx)
        repo_path = f"data/{file_name_in_repo}"
        
        try:
            # Cek apakah file sudah ada di repo
            contents = repo.get_contents(repo_path)
            # Jika ada, UPDATE
            repo.update_file(contents.path, f"Auto-update data: {file_name_in_repo}", content, contents.sha)
            print(f"✅ GitHub: File '{repo_path}' berhasil di-UPDATE.")
        except:
            # Jika belum ada, CREATE
            repo.create_file(repo_path, f"Auto-create data: {file_name_in_repo}", content)
            print(f"✅ GitHub: File '{repo_path}' berhasil di-UPLOAD baru.")
            
    except Exception as e:
        print(f"❌ Gagal Push ke GitHub: {e}")

def process_data():
    print(f"⚙️ Memulai Processing & Sync...")

    # ... [BAGIAN LOAD & CLEANING DATA SAMA SEPERTI SEBELUMNYA] ...
    # (Saya singkat agar tidak kepanjangan, pakai logika cleaning kamu yg tadi)
    
    # 1. Load CSV
    search_path = os.path.join(DATA_DIR, "*.csv")
    csv_files = glob.glob(search_path)
    if not csv_files: return
    
    df_list = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(df_list, ignore_index=True)
    
    # 2. Cleaning Simple (Contoh)
    df['Harga_Clean'] = df['Harga'].astype(str).str.replace('Rp', '').str.replace('.', '').str.strip()
    df['Harga_Int'] = pd.to_numeric(df['Harga_Clean'], errors='coerce').fillna(0).astype(int)
    
    # ... (Masukkan logika Brand & Kelas Sosial kamu di sini) ...
    
    # 3. Hapus Duplikat
    df.drop_duplicates(subset=['Judul', 'Harga_Int', 'Lokasi_Detail'], keep='first', inplace=True)
    print(f"📊 Total Data Bersih: {len(df)}")

    # 4. SIMPAN LOKAL (Wajib disimpan lokal dulu)
    try:
        df.to_excel(OUTPUT_FILE_PATH, index=False)
        print(f"💾 Simpan Lokal OK.")
        
        # 5. PUSH KE GITHUB (INI KUNCINYA)
        print("☁️ Mengupload ke GitHub...")
        upload_to_github(OUTPUT_FILE_PATH, REPO_NAME, OUTPUT_FILENAME)
        
    except Exception as e:
        print(f"❌ Error Saving: {e}")

if __name__ == "__main__":
    process_data()
