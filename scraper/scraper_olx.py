import time
import pandas as pd
import random
import os
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- KONFIGURASI ---
TARGET_MINIMAL = 50  # Ubah sesuai kebutuhan (misal 200)

# Path Output
FOLDER_DATA = "data"
FILENAME = "hasil_analisis_final.xlsx" # Kita langsung simpan ke Excel agar App.py bisa baca
# Atau csv jika app.py kamu bacanya csv: FILENAME = "data_hp_jawa_fix_lokasi.csv"

# Pastikan path absolut agar tidak nyasar
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Naik 1 level dari folder scraper
FULL_PATH = os.path.join(BASE_DIR, FOLDER_DATA, FILENAME)

DAFTAR_LOKASI = {
    "DKI Jakarta": "jakarta-dki_g2000007",
    "Jawa Barat": "jawa-barat_g2000009",
    "Jawa Tengah": "jawa-tengah_g2000010",
    "DI Yogyakarta": "yogyakarta-di_g2000032",
    "Jawa Timur": "jawa-timur_g2000011",
    "Banten": "banten_g2000004"
}

def get_driver():
    """Fungsi Cerdas untuk mendeteksi Environment (Local vs Cloud)"""
    options = Options()
    options.add_argument("--headless=new") # Wajib untuk server
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Cek apakah Chromium ada di lokasi standar Linux (Streamlit Cloud)
    chromium_path = "/usr/bin/chromium"
    chromedriver_path = "/usr/bin/chromedriver"

    if os.path.exists(chromium_path) and os.path.exists(chromedriver_path):
        print("[INFO] Terdeteksi Lingkungan Linux/Cloud. Menggunakan Chromium System.")
        options.binary_location = chromium_path
        service = Service(chromedriver_path)
        return webdriver.Chrome(service=service, options=options)
    else:
        print("[INFO] Terdeteksi Lingkungan Local/Windows. Menggunakan ChromeDriverManager.")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def run_scraper():
    print(f"[START] Memulai Scraping OLX...")
    print(f"[INFO] Target Output: {FULL_PATH}")

    # Buat folder jika belum ada
    if not os.path.exists(os.path.dirname(FULL_PATH)):
        os.makedirs(os.path.dirname(FULL_PATH))
        print(f"[INFO] Folder '{FOLDER_DATA}' dibuat.")

    all_data = []

    # --- LOOPING PROVINSI ---
    for provinsi, slug in DAFTAR_LOKASI.items():
        print(f"\n" + "="*50)
        print(f"📍 Membuka Provinsi: {provinsi}...")
        
        driver = None
        try:
            driver = get_driver()
            url = f"https://www.olx.co.id/{slug}/handphone_c208"
            driver.get(url)
            time.sleep(3)

            # --- FASE 1: LOAD MORE ---
            print(f"   🔄 Memulai Load More (Target: {TARGET_MINIMAL})...")
            consecutive_fails = 0
            last_item_count = 0
            
            while True:
                items = driver.find_elements(By.CSS_SELECTOR, "li[data-aut-id='itemBox']")
                current_count = len(items)
                print(f"      -> Terkumpul: {current_count} items")

                if current_count >= TARGET_MINIMAL:
                    print("      ✅ Target tercapai!")
                    break
                
                if current_count == last_item_count and current_count > 0:
                    consecutive_fails += 1
                    if consecutive_fails >= 3:
                        print("      ⚠️ Data mentok 3x. Stop.")
                        break
                else:
                    consecutive_fails = 0
                
                last_item_count = current_count

                try:
                    load_btn = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-aut-id='btnLoadMore']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", load_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", load_btn)
                    time.sleep(3) 
                except TimeoutException:
                    print("      ⚠️ Tombol habis.")
                    break
                except Exception:
                    break

            # --- FASE 2: EKSTRAKSI ---
            print(f"   📝 Menyalin data {provinsi}...")
            items = driver.find_elements(By.CSS_SELECTOR, "li[data-aut-id='itemBox']")
            
            count_local = 0
            for item in items:
                try:
                    try: judul = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='itemTitle']").text
                    except: judul = "N/A"

                    try: 
                        harga_text = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='itemPrice']").text
                        # Bersihkan harga jadi angka murni
                        harga_clean = int(harga_text.replace("Rp", "").replace(".", "").strip())
                    except: harga_clean = 0

                    try: 
                        lokasi = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='item-location']").text
                    except: 
                        lokasi = provinsi
                    
                    try: link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: link = "N/A"

                    # FILTER SEDERHANA
                    if harga_clean < 100000 or judul == "N/A": continue

                    # LOGIKA TAMBAHAN (BRAND & KELAS) UNTUK DASHBOARD
                    brand = "Lainnya"
                    if "iphone" in judul.lower(): brand = "Iphone"
                    elif "samsung" in judul.lower(): brand = "Samsung"
                    elif "xiaomi" in judul.lower(): brand = "Xiaomi"
                    
                    kelas = "Entry Level"
                    if harga_clean > 7000000: kelas = "Flagship (Sultan)"
                    elif harga_clean > 3000000: kelas = "Mid-Range"

                    all_data.append({
                        "Judul": judul,
                        "Harga_Int": harga_clean, # Nama kolom disesuaikan dgn app.py
                        "Brand": brand,
                        "Kelas_Sosial": kelas,
                        "Provinsi": provinsi,
                        "Lokasi_Detail": lokasi,
                        "Link": link
                    })
                    count_local += 1
                except: continue
            
            print(f"   💾 Ambil {count_local} data.")

        except Exception as e:
            print(f"   ❌ Error {provinsi}: {e}")
        
        finally:
            if driver: driver.quit()

    # --- SIMPAN SEMUA DATA KE EXCEL ---
    print(f"\n💾 Menyimpan Total {len(all_data)} data ke Excel...")
    if all_data:
        df = pd.DataFrame(all_data)
        # Hapus duplikat link
        df.drop_duplicates(subset=['Link'], inplace=True)
        
        # Simpan ke Excel (agar app.py langsung bisa baca formatnya)
        df.to_excel(FULL_PATH, index=False)
        print(f"✅ SUKSES! File tersimpan di: {FULL_PATH}")
    else:
        print("⚠️ Tidak ada data yang didapat.")

    print("\n🎉 SELESAI SEMUA PROVINSI!")

if __name__ == "__main__":
    run_scraper()
