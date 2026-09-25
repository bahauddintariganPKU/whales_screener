import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# 1. Konfigurasi Tampilan Halaman Web
st.set_page_config(
    page_title="Whale Screener Live",
    page_icon="🐋",
    layout="wide"
)

st.title("🐋 Live Crypto Whale Screener Dashboard")
st.write("Mendeteksi aktivitas akumulasi koin oleh *Whale* berdasarkan volume perdagangan dan rasio Vol/Mcap secara live.")

# 2. FITUR AUTO-REFRESH: Otomatis memicu pembaruan halaman setiap 60 detik
st.sidebar.markdown("### 🕒 Auto Refresh Status")
countdown_placeholder = st.sidebar.empty()

# Fungsi untuk Mengambil Data Real-Time + Data Sparkline (Grafik)
@st.cache_data(ttl=60) # Data di-cache selama 60 detik untuk efisiensi API
def fetch_whale_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "true", 
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

    # Tombol Refresh Manual di Sidebar
    if st.sidebar.button("🔄 Perbarui Data Sekarang (Manual)"):
        st.cache_data.clear()
        st.rerun()

    # 5. Logika Penyaringan Data
    filtered_df = df_crypto[
        (df_crypto["Rasio Vol/Mcap"] >= min_ratio) & 
        (df_crypto["Vol Perdagangan (24H)"] >= min_volume)
    ].sort_values(by="Rasio Vol/Mcap", ascending=False)

    # 6. Menampilkan Ringkasan Metrik Pasar
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Koin Dipantau", len(df_crypto))
    col2.metric("Koin Terdeteksi Whale", len(filtered_df))
    
    # Konversi hari ke Bahasa Indonesia
    hari_en = datetime.now().strftime('%A')
    kamus_hari = {
        'Sunday': 'Minggu', 'Monday': 'Senin', 'Tuesday': 'Selasa',
        'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu'
    }
    hari_id = kamus_hari.get(hari_en, hari_en)
    
    # Menggabungkan tanggal dan jam terupdate
    waktu_live = datetime.now().strftime('%d/%m/%Y - %H:%M:%S WIB')
    waktu_lengkap = f"{hari_id}, {waktu_live}"
    col3.metric("Terakhir Diperbarui", waktu_lengkap)

    # 7. Menampilkan Grafik Tren Koin Teratas
    st.markdown("---")
    st.subheader("📈 Grafik Tren Harga 7 Hari (Koin Teratas Hasil Filter)")
    
    if not filtered_df.empty:
        top_coins = filtered_df["Koin"].head(5).tolist()
        chart_data = {}
        for coin in top_coins:
            if coin in sparkline_data:
                chart_data[coin] = sparkline_data[coin]
        
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.line_chart(df_chart)
        else:
            st.info("Data grafik belum tersedia.")
    else:
        st.warning("⚠️ Naikkan atau sesuaikan filter untuk melihat grafik.")

    # 8. Tombol Download Data ke CSV
    st.markdown("---")
    col_title, col_download = st.columns()
    with col_title:
        st.subheader("📊 Hasil Analisis Penyaringan Koin")
    
    with col_download:
        if not filtered_df.empty:
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Data (CSV)",
                data=csv_data,
                file_name=f"whale_screener_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Tampilan Tabel Data Utama di Web
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
    else:
        st.warning("⚠️ Tidak ada koin yang memenuhi kriteria filter saat ini.")
    
    # 9. Kredit Pembuat
    st.markdown("---")
    st.caption("🚀 **Created by Bahauddin Tarigan** | © 2026 Crypto Whale Tracker")

    # Memicu hitung mundur otomatis untuk melakukan refresh layar tiap 60 detik
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
