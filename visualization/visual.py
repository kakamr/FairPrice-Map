import pandas as pd
import plotly.express as px

# --- FUNGSI 1: SCAM DETECTOR (BOX PLOT) ---
def create_scam_detector(df, brand_choice):
    """
    Membuat Box Plot untuk mendeteksi anomali harga pada brand tertentu.
    """
    # Filter data berdasarkan brand yang dipilih user
    df_filtered = df[df['Brand'] == brand_choice]
    
    fig = px.box(
        df_filtered, 
        x="Provinsi", 
        y="Harga_Int", 
        color="Provinsi",
        points="all", # Tampilkan semua titik data
        hover_data=["Judul", "Lokasi_Detail"], 
        title=f"Distribusi Harga {brand_choice} (Titik Bawah = Potensi Scam)",
        labels={"Harga_Int": "Harga (Rupiah)"}
    )
    fig.update_layout(yaxis_tickformat=",.0f") # Format angka Rp
    return fig

# --- FUNGSI 2: PRICE GAP (BAR CHART) ---
def create_price_gap(df):
    """
    Membuat Bar Chart horizontal rata-rata harga per provinsi.
    """
    # Hitung Rata-rata
    avg_price = df.groupby('Provinsi')['Harga_Int'].mean().reset_index().sort_values('Harga_Int')
    
    fig = px.bar(
        avg_price,
        x="Harga_Int",
        y="Provinsi",
        color="Provinsi",
        orientation='h', 
        text_auto='.2s', 
        title="Rata-rata Harga Gadget per Provinsi",
        labels={"Harga_Int": "Rata-rata Harga"}
    )
    fig.update_layout(xaxis_tickformat=",.0f")
    return fig

# --- FUNGSI 3: EKONOMI DIGITAL (STACKED BAR) ---
def create_economic_profile(df):
    """
    Membuat Histogram/Stacked Bar Chart proporsi kelas sosial.
    """
    fig = px.histogram(
        df, 
        y="Provinsi", 
        color="Kelas_Sosial", 
        barnorm="percent", # Ini bikin jadi 100% stacked
        text_auto='.0f',
        title="Komposisi Kelas Sosial Gadget per Wilayah",
        labels={"count": "Persentase (%)"},
        # Mengatur urutan warna agar konsisten
        category_orders={"Kelas_Sosial": ["Entry Level", "Middle Class", "High End / Sultan"]} 
    )
    return fig