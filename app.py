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
st.write("Mendeteksi aktivitas akumulasi koin oleh *Whale* berdasarkan volume perdagangan dan rasio Vol/Mcap secara live. coingecko Basic Mengapa Whale *Terjebak* oleh Indikator Ini? Whale memiliki modal jutaan hingga miliaran dolar. Mereka tidak bisa menyembunyikan volume transaksi mereka. Ketika whale mulai mengakumulasi (membeli) atau melakukan distribusi (menjual) sebuah koin, mereka akan menyuntikkan likuiditas dalam jumlah raksasa. Akibatnya, volume perdagangan harian koin tersebut melonjak drastis, sementara kapitalisasi pasarnya (Market Cap) belum berubah banyak. Hal inilah yang membuat rasio Vol/Mcap melompat naik dan langsung terdeteksi oleh screener ini")

# 2. Fungsi untuk Mengambil Data Real-Time + Data Sparkline (Grafik)
@st.cache_data(ttl=60)
def fetch_whale_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "true", # Mengaktifkan data grafik 7 hari
        "price_change_percentage": "7d"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            raw_data = response.json()
            processed_list = []
            sparkline_dict = {}
            
            for coin in raw_data:
                mcap = coin.get("market_cap", 0)
                vol = coin.get("total_volume", 0)
                vol_mcap_ratio = vol / mcap if mcap > 0 else 0
                coin_name = f"{coin.get('name')} ({coin.get('symbol').upper()})"
                
                processed_list.append({
                    "Koin": coin_name,
                    "Harga Saat Ini": coin.get("current_price", 0),
                    "Tren 7 Hari (%)": coin.get("price_change_percentage_7d_in_currency", 0),
                    "Rasio Vol/Mcap": vol_mcap_ratio,
                    "Vol Perdagangan (24H)": vol,
                    "Market Cap": mcap
                })
                
                # Simpan data riwayat harga untuk grafik
                if "sparkline_in_7d" in coin:
                    sparkline_dict[coin_name] = coin["sparkline_in_7d"]["price"]
                    
            return pd.DataFrame(processed_list), sparkline_dict
        else:
            st.error(f"Gagal mengambil data dari API (Status Code: {response.status_code})")
            return pd.DataFrame(), {}
    except Exception as e:
        st.error(f"Terjadi kesalahan koneksi: {e}")
        return pd.DataFrame(), {}

# 3. Memuat Data Utama
with st.spinner("🔄 Sedang menarik data kripto & grafik real-time..."):
    df_crypto, sparkline_data = fetch_whale_data()

if not df_crypto.empty:
    # 4. Panel Kontrol Filter di Bagian Sidebar (Kiri)
    st.sidebar.header("🎯 Parameter Penyaringan Whale")
    min_ratio = st.sidebar.slider("Minimal Rasio Vol/Mcap", 0.0, 1.0, 0.20, step=0.05)
    min_volume = st.sidebar.number_input("Minimal Volume Perdagangan (USD)", min_value=0, value=10_000_000, step=5_000_000, format="%d")

    # 5. Logika Penyaringan Data
    filtered_df = df_crypto[
        (df_crypto["Rasio Vol/Mcap"] >= min_ratio) & 
        (df_crypto["Vol Perdagangan (24H)"] >= min_volume)
    ].sort_values(by="Rasio Vol/Mcap", ascending=False)

    # 6. Menampilkan Ringkasan Metrik Pasar
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Koin Dipantau", len(df_crypto))
    col2.metric("Koin Terdeteksi Whale", len(filtered_df))
    col3.text(f"Terakhir Diperbarui: \n{time.strftime('%H:%M:%S WIB')}")

    # 7. FITUR BARU: Menampilkan Grafik Tren Koin Teratas
    st.markdown("---")
    st.subheader("📈 Grafik Tren Harga 7 Hari (Koin Teratas Hasil Filter)")
    
    if not filtered_df.empty:
        # Ambil maksimal 5 koin teratas yang paling kuat indikasi whale-nya
        top_coins = filtered_df["Koin"].head(5).tolist()
        
        # Satukan data harga untuk grafik
        chart_data = {}
        for coin in top_coins:
            if coin in sparkline_data:
                chart_data[coin] = sparkline_data[coin]
        
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            # Tampilkan grafik garis interaktif
            st.line_chart(df_chart)
        else:
            st.info("Data grafik belum tersedia.")
    else:
        st.warning("⚠️ Naikkan atau sesuaikan filter untuk melihat grafik.")

    # 8. Tampilan Tabel Data Utama di Web
    st.markdown("---")
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
            height=400
        )
    
    # 9. Kredit Pembuat
    st.markdown("---")
    st.caption("🚀 **Created by Bahauddin Tarigan** | © 2026 Crypto Whale Tracker")
