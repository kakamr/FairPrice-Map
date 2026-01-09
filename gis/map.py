import pandas as pd
import folium
import json
import os

# --- KONFIGURASI PATH ---
FOLDER_NAME = 'data'
INPUT_FILENAME = 'hasil_analisis_final.xlsx'  # Langsung baca Excel
GEOJSON_FILENAME = 'gadm41_IDN_1.json'        # Pastikan file ini ada di folder data
OUTPUT_MAP_NAME = 'peta_gadget_jawa.html'

# Menggabungkan path agar membaca dari dalam folder 'data'
INPUT_DATA_PATH = os.path.join(FOLDER_NAME, INPUT_FILENAME)
INPUT_GEOJSON_PATH = os.path.join(FOLDER_NAME, GEOJSON_FILENAME)
OUTPUT_MAP_PATH = os.path.join(FOLDER_NAME, OUTPUT_MAP_NAME)

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

def create_gis_map():
    print(f"📂 Membaca data dari: {INPUT_DATA_PATH}...")
    
    # 1. Validasi File
    if not os.path.exists(INPUT_DATA_PATH):
        print(f"❌ Error: File '{INPUT_DATA_PATH}' tidak ditemukan.")
        print("👉 Pastikan file 'hasil_analisis_final.xlsx' ada di dalam folder 'data'.")
        return

    if not os.path.exists(INPUT_GEOJSON_PATH):
        print(f"❌ Error: File '{INPUT_GEOJSON_PATH}' tidak ditemukan.")
        print("👉 Pastikan file JSON GADM ada di dalam folder 'data'.")
        return

    # 2. Load Data Excel
    try:
        # Menggunakan read_excel karena user meminta file xlsx
        df = pd.read_excel(INPUT_DATA_PATH)
        print(f"✅ Berhasil memuat {len(df)} baris data dari Excel.")
    except Exception as e:
        print(f"❌ Gagal membaca file Excel: {e}")
        return

    # 3. Load GeoJSON GADM
    print(f"🌍 Membaca peta GADM dari: {INPUT_GEOJSON_PATH}...")
    try:
        with open(INPUT_GEOJSON_PATH, 'r') as f:
            indo_geojson = json.load(f)
    except Exception as e:
        print(f"❌ Gagal baca file GeoJSON: {e}")
        return

    # 4. Analisis Data Per Provinsi
    print("🧮 Menghitung statistik wilayah...")
    summary_data = []
    
    # Pastikan nama kolom 'Provinsi' dan 'Brand' sesuai dengan di Excel
    for provinsi, group in df.groupby('Provinsi'):
        # A. Hitung Dominasi (iPhone vs Android)
        iphone_count = len(group[group['Brand'].str.contains('Iphone|Apple', case=False, na=False)])
        android_count = len(group) - iphone_count
        
        if iphone_count > android_count:
            dominasi = "🍏 Dominan iPhone"
            color_code = "#ff4d4d" # Merah
        else:
            dominasi = "🤖 Dominan Android"
            color_code = "#7bed9f" # Hijau
            
        # B. Cari Top 3 HP
        top_brands = group['Brand'].value_counts().head(3).index.tolist()
        
        hp_stats = []
        for i in range(3):
            if i < len(top_brands):
                brand = top_brands[i]
                avg_price = group[group['Brand'] == brand]['Harga_Int'].mean()
                hp_stats.append(f"{brand} ({format_rupiah(avg_price)})")
            else:
                hp_stats.append("-")
        
        summary_data.append({
            'Provinsi': provinsi,
            'Dominant_Label': dominasi,
            'Color': color_code,
            'HP_1': hp_stats[0],
            'HP_2': hp_stats[1],
            'HP_3': hp_stats[2],
            'Total_Listing': len(group)
        })

    df_summary = pd.DataFrame(summary_data)

    # 5. Mapping Nama (Excel -> GADM JSON)
    # Sesuaikan dengan nama provinsi di Excel kamu dan di JSON GADM
    gadm_map = {
        "DKI Jakarta": "JakartaRaya",
        "DI Yogyakarta": "Yogyakarta",
        "Jawa Barat": "JawaBarat",
        "Jawa Tengah": "JawaTengah",
        "Jawa Timur": "JawaTimur",
        "Banten": "Banten"
    }

    # 6. Injeksi Data ke GeoJSON
    print("💉 Menyuntikkan data ke peta...")
    for feature in indo_geojson['features']:
        geo_name = feature['properties'].get('NAME_1', '')
        
        found = False
        for index, row in df_summary.iterrows():
            csv_name = row['Provinsi']
            # Cek mapping, jika tidak ada di map, pakai nama asli
            target_geo_name = gadm_map.get(csv_name, csv_name)
            
            # Pencocokan nama (Case Insensitive & Hapus Spasi jika perlu)
            if target_geo_name.lower().replace(" ", "") == geo_name.lower().replace(" ", ""):
                feature['properties']['info_wilayah'] = csv_name
                feature['properties']['info_dominan'] = row['Dominant_Label']
                feature['properties']['info_hp1'] = row['HP_1']
                feature['properties']['info_hp2'] = row['HP_2']
                feature['properties']['info_hp3'] = row['HP_3']
                feature['properties']['style_color'] = row['Color']
                found = True
                break
        
        if not found:
            feature['properties']['info_wilayah'] = geo_name
            feature['properties']['info_dominan'] = "Tidak Ada Data"
            feature['properties']['info_hp1'] = "-"
            feature['properties']['info_hp2'] = "-"
            feature['properties']['info_hp3'] = "-"
            feature['properties']['style_color'] = "#d1ccc0" # Abu-abu

    # 7. Render Peta
    print("🗺️  Membuat file HTML...")
    m = folium.Map(location=[-7.6145, 110.7122], zoom_start=7)

    def style_function(feature):
        return {
            'fillColor': feature['properties'].get('style_color', '#d1ccc0'),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.6
        }

    folium.GeoJson(
        indo_geojson,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['info_wilayah', 'info_dominan', 'info_hp1', 'info_hp2', 'info_hp3'],
            aliases=['📍 Wilayah:', '🏆 Status:', '🥇 #1:', '🥈 #2:', '🥉 #3:'],
            localize=True
        )
    ).add_to(m)

    m.save(OUTPUT_MAP_PATH)
    print(f"🎉 SUKSES! Peta tersimpan di: {OUTPUT_MAP_PATH}")
    print("👉 Buka folder 'data' dan cari file html tersebut.")

if __name__ == "__main__":
    create_gis_map()