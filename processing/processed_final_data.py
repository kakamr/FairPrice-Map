import pandas as pd
import os
import glob
import sys

# --- KONFIGURASI PATH ABSOLUT (ANTI NYASAR) ---
# Mengambil path folder project (naik 2 level dari folder 'processing')
# Struktur: Project/processing/script.py -> Project/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folder Data (Project/data)
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'hasil_analisis_final.xlsx')

def process_data():
    print(f"⚙️ Memulai Processing...")
    print(f"📂 Base Directory: {BASE_DIR}")
    print(f"📂 Folder Data: {DATA_DIR}")

    # 1. Cek Folder Data
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Folder data tidak ditemukan di {DATA_DIR}")
        return

    # 2. Cari semua file CSV
    search_path = os.path.join(DATA_DIR, "*.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        print(f"❌ Tidak ada file CSV di {DATA_DIR}")
        return

    # 3. Gabungkan Semua CSV
    df_list = []
    print(f"🔍 Ditemukan {len(csv_files)} file CSV.")
    
    for filename in csv_files:
        try:
            # print(f"   -> Membaca: {os.path.basename(filename)}") 
            temp_df = pd.read_csv(filename)
            df_list.append(temp_df)
        except Exception as e:
            print(f"   ❌ Gagal baca {filename}: {e}")

    if not df_list:
        print("❌ Dataframe kosong.")
        return

    df = pd.concat(df_list, ignore_index=True)
    total_mentah = len(df)
    print(f"📊 Total data mentah (dari CSV): {total_mentah} baris")

    # 4. PROCESSING (Cleaning)
    print("🧹 Cleaning data...")
    
    # A. Bersihkan Harga
    df['Harga_Clean'] = df['Harga'].astype(str).str.replace('Rp', '', case=False).str.replace('.', '').str.strip()
    df['Harga_Int'] = pd.to_numeric(df['Harga_Clean'], errors='coerce').fillna(0).astype(int)

    # B. Kategorisasi Kelas
    def categorize_class(price):
        if price > 5000000: return 'Flagship/Sultan'
        elif 2000000 <= price <= 5000000: return 'Mid Range'
        else: return 'Entry Level'

    df['Kelas_Sosial'] = df['Harga_Int'].apply(categorize_class)

    # C. Ekstraksi Brand
    brands = [
        'iphone', 'samsung', 'xiaomi', 'redmi', 'oppo', 'vivo', 
        'realme', 'infinix', 'asus', 'rog', 'google', 'pixel', 
        'poco', 'tecno', 'itel', 'sony', 'huawei', 'nokia'
    ]

    def extract_brand(title):
        title_lower = str(title).lower()
        for brand in brands:
            if brand in title_lower:
                if brand == 'rog': return 'Asus'
                if brand == 'redmi': return 'Xiaomi'
                if brand == 'pixel': return 'Google'
                return brand.capitalize()
        return 'Lainnya'

    df['Brand'] = df['Judul'].apply(extract_brand)

    # 5. HAPUS DUPLIKAT (LOGIKA UTAMA)
    # Cek duplikat berdasarkan Judul, Harga, dan Lokasi yang sama persis
    sebelum_drop = len(df)
    df.drop_duplicates(subset=['Judul', 'Harga_Int', 'Lokasi_Detail'], keep='first', inplace=True)
    sesudah_drop = len(df)
    jml_duplikat = sebelum_drop - sesudah_drop

    print(f"♻️ Duplikat Dihapus: {jml_duplikat} data")
    print(f"✅ Total Data Bersih: {sesudah_drop} baris")

    if sesudah_drop == 0:
        print("⚠️ Hati-hati: Data menjadi 0 setelah filtering!")

    # 6. SIMPAN EXCEL
    try:
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"💾 Berhasil disimpan ke: {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Gagal menyimpan Excel: {e}")

if __name__ == "__main__":
    process_data()
