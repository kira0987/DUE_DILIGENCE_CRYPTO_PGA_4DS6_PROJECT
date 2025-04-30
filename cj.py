import os
import pandas as pd
import yfinance as yf

# --- Configuration ---
output_folder = 'downloaded_crypto_data'
os.makedirs(output_folder, exist_ok=True)

# --- Mapping to Yahoo Tickers ---
# Many crypto coins are traded as e.g., ADA-USD, BTC-USD in Yahoo Finance
# We extract from your file names
coin_files = [
    "ADA_USD Binance Historical Data.csv",
    "AVAX_USD CoinW Historical Data.csv",
    "BCH_USD Binance Historical Data.csv",
    "Bitcoin Futures CME Historical Data.csv",
    "BNB_USD Gate.io Historical Data.csv",
    "BTC_USD Bitfinex Historical Data.csv",
    "DOGE_USD Binance Historical Data.csv",
    "ETC_USD Binance Historical Data.csv",
    "ETH_BTC Poloniex Historical Data.csv",
    "ETH_USD Binance Historical Data.csv",
    "IOTA_USD Bitfinex Historical Data.csv",
    "LINK_USD Binance Historical Data.csv",
    "LTC_USD Binance Historical Data.csv",
    "pDOTn_USD Kraken Historical Data.csv",
    "PI_USD OKX Historical Data.csv",
    "SOL_USD Binance Historical Data.csv",
    "SUI_USD Binance Historical Data.csv",
    "TRX_USD Binance Historical Data.csv",
    "USDC_USD Binance Historical Data.csv",
    "USDT_USD Coinbase Pro Historical Data.csv",
    "XRP_USD OKX Historical Data.csv",
]

# --- Helper: Extract Ticker from Filename ---
def extract_ticker(file_name):
    parts = file_name.split('_')
    if len(parts) >= 2:
        return parts[0] + '-USD'
    return None

# --- Download Loop ---
for file_name in coin_files:
    ticker = extract_ticker(file_name)
    if ticker:
        try:
            print(f"📥 Fetching {ticker} data...")
            data = yf.download(ticker, period="730d", interval="1d")  # Last 2 years
            if not data.empty:
                output_path = os.path.join(output_folder, f"{ticker}.csv")
                data.to_csv(output_path)
                print(f"✅ Saved: {output_path}")
            else:
                print(f"⚠️ No data found for {ticker}")
        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")

print("\n✅ All available crypto data downloaded.")
