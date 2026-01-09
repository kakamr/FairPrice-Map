import pandas as pd
import os

# --- KONFIGURASI PATH ---
# Mengambil path folder project (naik satu level dari folder 'scraper')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV = os.path.join(BASE_DIR, 'data', 'data_hp_jawa_fix_lokasi.csv')
OUTPUT_EXCEL = os.path.join(BASE_DIR, 'data', 'hasil_analisis_final.xlsx')

def clean_price(price):
    """Membersihkan format Rp dan titik"""
    try:
        if isinstance(price, str):
            clean = price.replace('Rp', '').replace('.', '').replace(',', '').strip()
            return int(clean)
        return int(price)
    except:
        return 0

def detect_brand(title):
    """Mendeteksi brand berdasarkan judul"""
    title = str(title).lower()
    if 'iphone' in title: return 'Iphone'
    if 'samsung' in title: return 'Samsung'
    if 'xiaomi' in title or 'redmi' in title or 'poco' in title: return 'Xiaomi'
    if 'oppo' in title: return 'Oppo'
    if 'vivo' in title: return 'Vivo'
    if 'realme' in title: return 'Realme'
    if 'infinix' in title: return 'Infinix'
    if 'asus' in title or 'rog' in title: return 'Asus'
    return 'Lainnya'

def classify_class(price):
    """Mengelompokkan kelas sosial berdasarkan harga"""
    if price < 1500000: return 'Entry Level'
    elif 1500000 <= price < 4000000: return 'Mid Range'
    elif 4000000 <= price < 8000000: return 'High End'
    else: return 'Flagship/Sultan'

def run_processing():
    print(f"⚙️ Memulai Processing Data...")
    print(f"   📂 Membaca file: {INPUT_CSV}")

    if not os.path.exists(INPUT_CSV):
        print("   ❌ File CSV tidak ditemukan. Harap scraping dulu.")
        return

    # 1. Load Data CSV
    try:
        df = pd.read_csv(INPUT_CSV)
    except Exception as e:
        print(f"   ❌ Gagal membaca CSV: {e}")
        return

    print(f"   📊 Data mentah ditemukan: {len(df)} baris")

    # 2. Cleaning Harga
    df['Harga_Int'] = df['Harga'].apply(clean_price)
    
    # Hapus harga aneh (misal di bawah 100rb atau 0)
    df = df[df['Harga_Int'] > 100000]

    # 3. Klasifikasi Brand & Kelas
    df['Brand'] = df['Judul'].apply(detect_brand)
    df['Kelas_Sosial'] = df['Harga_Int'].apply(classify_class)

    # 4. Hapus Duplikat
    df.drop_duplicates(subset=['Judul', 'Harga_Int', 'Lokasi_Detail'], inplace=True)

    # 5. Simpan ke Excel (Wajib pakai engine openpyxl untuk xlsx)
    print(f"   💾 Menyimpan ke: {OUTPUT_EXCEL}")
    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"   ✅ Processing Selesai! Data bersih: {len(df)} baris siap divisualisasikan.")

if __name__ == "__main__":
    run_processing()
