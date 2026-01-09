import time
import pandas as pd
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# --- KONFIGURASI ---
TARGET_MINIMAL = 200
FOLDER_NAME = "data"  # Nama folder penyimpanan
FILE_NAME = "data_hp_jawa_fix_lokasi.csv" # Nama file output
FULL_PATH = os.path.join(FOLDER_NAME, FILE_NAME) # Gabungan: data/data_hp_jawa_fix_lokasi.csv

DAFTAR_LOKASI = {
    "DKI Jakarta": "jakarta-dki_g2000007",
    "Jawa Barat": "jawa-barat_g2000006", # Perbaikan slug (cek ulang jika perlu)
    "Jawa Tengah": "jawa-tengah_g2000005",
    "DI Yogyakarta": "di-yogyakarta_g2000008",
    "Jawa Timur": "jawa-timur_g2000004",
    "Banten": "banten_g2000003"
}

def run_scraper():
    print(f"🚀 Memulai Scraping (Output Folder: {FOLDER_NAME})...")

    # 1. BUAT FOLDER JIKA BELUM ADA
    if not os.path.exists(FOLDER_NAME):
        os.makedirs(FOLDER_NAME)
        print(f"📂 Folder '{FOLDER_NAME}' berhasil dibuat.")

    # --- LOOPING PROVINSI ---
    for provinsi, slug in DAFTAR_LOKASI.items():
        print(f"\n" + "="*50)
        print(f"📍 Membuka Provinsi: {provinsi}...")
        
        # BUKA BROWSER BARU
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        all_data_provinsi = [] # Tampung data per provinsi dulu

        try:
            url = f"https://www.olx.co.id/{slug}/handphone_c208"
            driver.get(url)
            time.sleep(3)

            # --- FASE 1: LOAD MORE ---
            print(f"   🔄 Memulai proses 'Load More' (Target: {TARGET_MINIMAL})...")
            consecutive_fails = 0
            last_item_count = 0
            
            while True:
                items = driver.find_elements(By.CSS_SELECTOR, "li[data-aut-id='itemBox']")
                current_count = len(items)
                print(f"      -> Data terkumpul: {current_count} / {TARGET_MINIMAL}")

                if current_count >= TARGET_MINIMAL:
                    print("      ✅ Target tercapai! Lanjut ekstrak.")
                    break
                
                if current_count == last_item_count and current_count > 0:
                    consecutive_fails += 1
                    if consecutive_fails >= 3:
                        print("      ⚠️ Data mentok 3x. Stop klik.")
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
                    print("      ⚠️ Tombol habis/hilang.")
                    break
                except Exception as e:
                    print(f"      ❌ Error klik: {e}")
                    break

            # --- FASE 2: EKSTRAKSI ---
            print(f"   📝 Menyalin detail data {provinsi}...")
            items = driver.find_elements(By.CSS_SELECTOR, "li[data-aut-id='itemBox']")
            
            count_local = 0
            for item in items:
                try:
                    # AMBIL JUDUL
                    try: judul = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='itemTitle']").text
                    except: judul = "N/A"

                    # AMBIL HARGA
                    try: 
                        harga_text = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='itemPrice']").text
                        harga_clean = harga_text.replace("Rp", "").replace(".", "").strip()
                    except: harga_clean = "0"

                    # AMBIL LOKASI (Pakai ID item-location)
                    try: 
                        lokasi = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='item-location']").text
                    except: 
                        # Fallback jika ID tidak ketemu
                        try:
                            lokasi = provinsi # Default
                        except:
                            lokasi = provinsi
                    
                    # AMBIL LINK
                    try: link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: link = "N/A"

                    # Validasi
                    if harga_clean == "0" or judul == "N/A": continue

                    all_data_provinsi.append({
                        "Provinsi": provinsi,
                        "Judul": judul,
                        "Harga": harga_clean,
                        "Lokasi_Detail": lokasi,
                        "Link": link
                    })
                    count_local += 1
                except: continue
            
            print(f"   💾 Berhasil ambil {count_local} data valid.")

        except Exception as e:
            print(f"   ❌ TERJADI ERROR DI {provinsi}: {e}")
        
        finally:
            driver.quit()
            
            # --- SIMPAN DATA KE FOLDER 'DATA' ---
            if all_data_provinsi:
                df = pd.DataFrame(all_data_provinsi)
                
                # Cek apakah file sudah ada di dalam folder data
                file_exists = os.path.isfile(FULL_PATH)
                
                # Simpan mode append
                df.to_csv(FULL_PATH, mode='a', header=not file_exists, index=False)
                print(f"   ✅ Data {provinsi} tersimpan ke '{FULL_PATH}'")
            else:
                print(f"   ⚠️ Tidak ada data yang disimpan untuk {provinsi}.")

    print("\n🎉 SELESAI SEMUA PROVINSI!")

if __name__ == "__main__":
    run_scraper()