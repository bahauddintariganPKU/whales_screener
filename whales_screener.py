import requests
import pandas as pd
import time
from datetime import datetime

def get_contract_address(coin_id):
    """Fungsi untuk mengambil Contract Address (CA) berdasarkan ID koin"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            coin_details = response.json()
            platforms = coin_details.get("platforms", {})
            
            if not platforms:
                return "Koin Native/Jaringan Utama (Tidak punya CA khusus)"
            
            # Merangkai string CA dari platform jaringan yang tersedia
            ca_list = []
            for network, address in platforms.items():
                if address: # Jika alamat tidak kosong
                    ca_list.append(f"{network.upper()}: {address}")
            
            return " | ".join(ca_list[:2]) # Tampilkan maksimal 2 jaringan utama agar terminal rapi
        elif response.status_code == 429:
            time.sleep(2) # Jeda singkat jika terkena rate limit ringan
            return "Rate limit API (Gagal memuat CA)"
        return "Tidak ditemukan CA"
    except Exception:
        return "Gagal memuat CA"

def run_pure_screener(interval_seconds=3600):
    print(f"🚀 Memulai Whale Accumulation Screener. Pemindaian otomatis setiap {interval_seconds // 5} menit.")
    print("📢 Hasil!!! , creator Bahauddin\n")
    
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏰ [{current_time}] Mengambil data pasar real-time...")
        
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "7d"
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                
                df = df[['id', 'symbol', 'name', 'current_price', 'total_volume', 'market_cap', 'price_change_percentage_7d_in_currency']]
                df.rename(columns={'price_change_percentage_7d_in_currency': 'price_change_7d'}, inplace=True)
                
                df['volume_to_mc_ratio'] = df['total_volume'] / df['market_cap']
                
                # --- STRUKTUR FILTER ---
                stablecoin_keywords = ['usd', 'usdt', 'usdc', 'dai', 'frax', 'tusd', 'busd', 'fdusd', 'pyusd', 'usde', 'weth', 'wbtc', 'wsol']
                is_stablecoin = df['symbol'].str.lower().isin(stablecoin_keywords) | df['name'].str.lower().str.contains('stablecoin|pegged|wrapped')
                
                condition_high_volume = df['volume_to_mc_ratio'] > 0.12
                condition_accumulation_price = (df['price_change_7d'] >= -15.0) & (df['price_change_7d'] <= 8.0)
                condition_market_cap = (df['market_cap'] >= 20_000_000) & (df['market_cap'] <= 1_500_000_000)
                
                filtered_df = df[~is_stablecoin & condition_high_volume & condition_accumulation_price & condition_market_cap].copy()
                filtered_df = filtered_df.sort_values(by='volume_to_mc_ratio', ascending=False)
                
                if not filtered_df.empty:
                    print(f"\n🎯 [SINYAL DIANGKUT WHALE] Ditemukan {len(filtered_df)} koin potensial:")
                    print("=" * 65)
                    for index, row in filtered_df.head(5).iterrows():
                        print(f"🪙 Koin           : {row['name']} ({row['symbol'].upper()})")
                        print(f"   💰 Harga Saat Ini: ${row['current_price']:,}")
                        print(f"   📈 Tren 7 Hari   : {row['price_change_7d']:.2f}%")
                        print(f"   📊 Rasio Vol/Mcap: {row['volume_to_mc_ratio']:.4f}")
                        print(f"   💸 Vol Perdagangan: ${row['total_volume']:,}")
                        
                        # Mengambil data CA secara real-time untuk koin yang lolos filter
                        print("   🔍 Memuat data Contract Address (CA)...")
                        coin_ca = get_contract_address(row['id'])
                        print(f"   📋 CA/Platform   : {coin_ca}")
                        print("-" * 65)
                        
                        time.sleep(1.5) # Jeda 1.5 detik antar koin agar tidak terkena rate limit API CoinGecko gratisan
                else:
                    print("📅 Pemindaian selesai: Belum ada koin baru yang memenuhi kriteria akumulasi senyap jam ini.")
                    
            else:
                print(f"❌ Error Server API CoinGecko: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Terjadi kesalahan pada sistem: {e}")
            
        print(f"💤 Menunggu {interval_seconds // 60} menit untuk pemindaian berikutnya...\n")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_pure_screener(interval_seconds=100)
