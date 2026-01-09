import time
import pandas as pd
import random
import os
import sys 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# --- KONFIGURASI ---
TARGET_MINIMAL = 200
FOLDER_NAME = "data"
FILE_NAME = "data_hp_jawa_fix_lokasi.csv"

# Path Absolute (Wajib untuk Cloud)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL_PATH = os.path.join(BASE_DIR, FOLDER_NAME, FILE_NAME) 

DAFTAR_LOKASI = {
    "DKI Jakarta": "jakarta-dki_g2000007",
    "Jawa Barat": "jawa-barat_g2000009",
    "Jawa Tengah": "jawa-tengah_g2000010",
    "DI Yogyakarta": "yogyakarta-di_g2000032",
    "Jawa Timur": "jawa-timur_g2000011",
    "Banten": "banten_g2000004"
}

def run_scraper():
    print(f"🚀 Memulai Scraping (Output: {FILE_NAME})")
    
    # 1. SETUP FOLDER
    folder_abs_path = os.path.join(BASE_DIR, FOLDER_NAME)
    if not os.path.exists(folder_abs_path):
        os.makedirs(folder_abs_path)

    # --- LOOPING PROVINSI ---
    for provinsi, slug in DAFTAR_LOKASI.items():
        print(f"\n📍 {provinsi}...", end=" ", flush=True) # Print satu baris saja
        
        # --- SETUP BROWSER (HEADLESS) ---
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        
        driver = None
        try:
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            except:
                # Fallback Linux Streamlit Cloud
                options.binary_location = "/usr/bin/chromium"
                service = Service("/usr/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            print("❌ Gagal Driver.")
            continue
        
        all_data_provinsi = []

        try:
            url = f"https://www.olx.co.id/{slug}/handphone_c208"
            driver.get(url)
            time.sleep(3)

            # --- FASE 1: LOAD MORE (VERSI QUIET) ---
            # print(f"   🔄 Load More...") # Dihapus biar gak panjang
            consecutive_fails = 0
            last_item_count = 0
            
            while True:
                items = driver.find_elements(By.CSS_SELECTOR, "li[data-aut-id='itemBox']")
                current_count = len(items)
                
                # --- MODIFIKASI: Hanya print status setiap 50 data ---
                if current_count % 50 == 0 and current_count > 0:
                    print(f"[{current_count}]..", end=" ", flush=True)
                # -----------------------------------------------------

                if current_count >= TARGET_MINIMAL:
                    break
                
                if current_count == last_item_count and current_count > 0:
                    consecutive_fails += 1
                    if consecutive_fails >= 3: break
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
                    time.sleep(2) 
                except:
                    break

            # --- FASE 2: EKSTRAKSI ---
            items = driver.find_elements(By.CSS_SELECTOR, "li[data-aut-id='itemBox']")
            
            for item in items:
                try:
                    try: judul = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='itemTitle']").text
                    except: judul = "N/A"

                    try: 
                        harga_text = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='itemPrice']").text
                        harga_clean = harga_text.replace("Rp", "").replace(".", "").strip()
                    except: harga_clean = "0"

                    try: lokasi = item.find_element(By.CSS_SELECTOR, "span[data-aut-id='item-location']").text
                    except: lokasi = provinsi
                    
                    try: link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: link = "N/A"

                    if harga_clean == "0" or judul == "N/A": continue

                    all_data_provinsi.append({
                        "Provinsi": provinsi,
                        "Judul": judul,
                        "Harga": harga_clean,
                        "Lokasi_Detail": lokasi,
                        "Link": link
                    })
                except: continue
            
            # --- SIMPAN DATA ---
            if all_data_provinsi:
                df = pd.DataFrame(all_data_provinsi)
                file_exists = os.path.isfile(FULL_PATH)
                df.to_csv(FULL_PATH, mode='a', header=not file_exists, index=False)
                print(f"✅ OK ({len(all_data_provinsi)} data)") # Print singkat
            else:
                print(f"⚠️ Kosong")
            
        except Exception as e:
            print(f"❌ Err: {e}")
        
        finally:
            if driver: driver.quit()

    print("\n🎉 SELESAI!")

if __name__ == "__main__":
    run_scraper()
