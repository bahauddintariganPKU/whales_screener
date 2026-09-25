import streamlit as st
import requests
import pandas as pd
import time

# 1. Konfigurasi Tampilan Halaman Web
st.set_page_config(
    page_title="Whale Screener Live",
    page_icon="🐋",
    layout="wide"
)

st.title("🐋 Live Crypto Whale Screener Dashboard")
st.write("Mendeteksi aktivitas akumulasi koin oleh *Whale* berdasarkan volume perdagangan dan rasio Vol/Mcap secara live.")

# 2. Fungsi untuk Mengambil Data Real-Time dari CoinGecko API
@st.cache_data(ttl=60) # Data otomatis diperbarui setiap 60 detik jika halaman di-refresh
def fetch_whale_data():
    # Mengambil top 100 koin berdasarkan Market Cap
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "7d"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            raw_data = response.json()
            processed_list = []
            
            for coin in raw_data:
                mcap = coin.get("market_cap", 0)
                vol = coin.get("total_volume", 0)
                
                # Menghitung Rasio Vol/Mcap secara matematis
                vol_mcap_ratio = vol / mcap if mcap > 0 else 0
                
                processed_list.append({
                    "Koin": f"{coin.get('name')} ({coin.get('symbol').upper()})",
                    "Harga Saat Ini": coin.get("current_price", 0),
                    "Tren 7 Hari (%)": coin.get("price_change_percentage_7d_in_currency", 0),
                    "Rasio Vol/Mcap": vol_mcap_ratio,
                    "Vol Perdagangan (24H)": vol,
                    "Market Cap": mcap
                })
            return pd.DataFrame(processed_list)
        else:
            st.error(f"Gagal mengambil data dari API (Status Code: {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Terjadi kesalahan koneksi: {e}")
        return pd.DataFrame()

# 3. Memuat Data Utama
with st.spinner("🔄 Sedang menarik data kripto real-time..."):
    df_crypto = fetch_whale_data()

if not df_crypto.empty:
    # 4. Panel Kontrol Filter di Bagian Sidebar (Kiri)
    st.sidebar.header("🎯 Parameter Penyaringan Whale")
    
    # Slider untuk menentukan batasan minimal akumulasi whale
    min_ratio = st.sidebar.slider(
        "Minimal Rasio Vol/Mcap", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.20, 
        step=0.05,
        help="Rasio > 0.20 menandakan koin sangat aktif diperdagangkan. > 0.50 menandakan anomali transaksi besar (Whale)."
    )
    
    min_volume = st.sidebar.number_input(
        "Minimal Volume Perdagangan (USD)", 
        min_value=0, 
        value=10_000_000, 
        step=5_000_000,
        format="%d"
    )

    # 5. Logika Penyaringan Data
    filtered_df = df_crypto[
        (df_crypto["Rasio Vol/Mcap"] >= min_ratio) & 
        (df_crypto["Vol Perdagangan (24H)"] >= min_volume)
    ]
    
    # Mengurutkan koin dari rasio Vol/Mcap tertinggi (paling berpotensi di-pump)
    filtered_df = filtered_df.sort_values(by="Rasio Vol/Mcap", ascending=False)

    # 6. Menampilkan Ringkasan Metrik Pasar
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Koin Dipantau", len(df_crypto))
    col2.metric("Koin Terdeteksi Whale", len(filtered_df))
    col3.text(f"Terakhir Diperbarui: \n{time.strftime('%H:%M:%S WIB')}")

    # 7. Tampilan Tabel Data Utama di Web
    st.subheader("📊 Hasil Analisis Penyaringan Koin")
    if not filtered_df.empty:
        st.dataframe(
            filtered_df.style.format({
                "Harga Saat Ini": "${:,.4f}",
                "Tren 7 Hari (%)": "{:+.2f}%",
                "Rasio Vol/Mcap": "{:.4f}",
                "Vol Perdagangan (24H)": "${:,.0f}",
                "Market Cap": "${:,.0f}"
            }),
            use_container_width=True,
            height=500
        )
    else:
        st.warning("⚠️ Tidak ada koin yang memenuhi kriteria filter saat ini. Coba turunkan nilai batasan filter di sidebar.")
        # 8. Menambahkan Kredit Pembuat di Bagian Bawah Halaman Web
st.markdown("---")
st.caption("🚀 **Created by Bahauddin Tarigan** | © 2026 Crypto Whale Tracker")

