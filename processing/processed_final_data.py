import pandas as pd
import os
import glob

# --- KONFIGURASI ---
FOLDER_NAME = 'data'  # Nama folder
OUTPUT_FILE = 'hasil_analisis_final.xlsx' # Nama file output

def process_data():
    # Cek apakah folder ada
    if not os.path.exists(FOLDER_NAME):
        print(f"❌ Error: Folder '{FOLDER_NAME}' tidak ditemukan.")
        print(f"👉 Buat folder bernama '{FOLDER_NAME}' dan masukkan file CSV hasil scraping ke dalamnya.")
        return

    print(f"📂 Mencari file CSV di dalam folder '{FOLDER_NAME}'...")
    
    # 1. Cari semua file .csv di dalam folder 'data'
    # Pattern: data/*.csv
    search_path = os.path.join(FOLDER_NAME, "*.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        print(f"❌ Tidak ada file CSV di folder '{FOLDER_NAME}'.")
        return

    # 2. Gabungkan File
    df_list = []
    for filename in csv_files:
        try:
            print(f"   -> Membaca: {os.path.basename(filename)}...")
            temp_df = pd.read_csv(filename)
            df_list.append(temp_df)
        except Exception as e:
            print(f"   ❌ Gagal baca {filename}: {e}")

    if not df_list:
        return

    df = pd.concat(df_list, ignore_index=True)
    print(f"✅ Total data mentah: {len(df)} baris.")

    # 3. PROCESSING (Cleaning & Categorization)
    print("🧹 Sedang memproses data...")
    
    # A. Bersihkan Harga
    df['Harga_Clean'] = df['Harga'].astype(str).str.replace('Rp', '', case=False).str.replace('.', '').str.strip()
    df['Harga_Int'] = pd.to_numeric(df['Harga_Clean'], errors='coerce').fillna(0).astype(int)

    # B. Kategorisasi Kelas (Range Baru: <2jt, 2-5jt, >5jt)
    def categorize_class(price):
        if price > 5000000:
            return 'High End / Sultan'
        elif 2000000 <= price <= 5000000:
            return 'Middle Class'
        else:
            return 'Entry Level'

    df['Kelas_Sosial'] = df['Harga_Int'].apply(categorize_class)

    # C. Ekstraksi Brand
    brands = [
        'iphone', 'samsung', 'xiaomi', 'redmi', 'oppo', 'vivo', 
        'realme', 'infinix', 'asus', 'rog', 'google', 'pixel', 
        'poco', 'tecno', 'itel', 'sony', 'huawei', 'nokia', 'advan'
    ]

    def extract_brand(title):
        title_lower = str(title).lower()
        for brand in brands:
            if brand in title_lower:
                if brand == 'rog': return 'Asus'
                if brand == 'redmi': return 'Xiaomi'
                if brand == 'pixel': return 'Google'
                return brand.capitalize()
        return 'Lainnya/Unknown'

    df['Brand'] = df['Judul'].apply(extract_brand)

    # 4. SIMPAN KE FOLDER DATA
    # Path lengkap: data/hasil_analisis_final.xlsx
    output_path = os.path.join(FOLDER_NAME, OUTPUT_FILE)
    
    try:
        df.to_excel(output_path, index=False)
        print("\n" + "="*50)
        print(f"🎉 SUKSES! File berhasil disimpan di:")
        print(f"📂 {output_path}")
        print("="*50)
        
        # Info Singkat
        print(df['Kelas_Sosial'].value_counts())
        
    except Exception as e:
        print(f"❌ Gagal menyimpan file: {e}")
        print("Pastikan file Excel tidak sedang dibuka!")

if __name__ == "__main__":
    process_data()