import os
import pandas as pd
import numpy as np

# --- Configuration ---
base_folder = 'more_processing_data'
output_folder = 'enhanced_cleaned_crypto_data_v1'

file_list = [
    "IOTA_USD Bitfinex Historical Data.csv",
    "SUI_USD Binance Historical Data.csv",
    "USDC_USD Binance Historical Data.csv",
    "USDT_USD Coinbase Pro Historical Data.csv"
]

feature_list = ['Price', 'Open', 'High', 'Low', 'Vol.', 'Change %']

threshold_ratio = 0.05   # 5% allowed max for any repeating value, otherwise replace

# Create output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# --- Cleaning Functions ---
def smart_clean_dataframe(df):
    # Parse Dates
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values('Date').reset_index(drop=True)

    # Keep only important columns
    df = df[['Date'] + feature_list]

    # Remove commas and convert to float
    for col in feature_list:
        df[col] = df[col].replace(',', '', regex=True).astype(float)

    # Forward Fill first, then Backward Fill
    df = df.fillna(method='ffill')
    df = df.fillna(method='bfill')

    total_rows = len(df)

    # Handle repeating suspicious values for each column
    for col in ['Price', 'Open', 'High', 'Low', 'Vol.']:
        unique_values, counts = np.unique(df[col], return_counts=True)

        for value, count in zip(unique_values, counts):
            ratio = count / total_rows

            if ratio > threshold_ratio:
                # More than threshold => treat it as suspicious
                # Don't use this value to compute mean
                good_values = df[col][(df[col] != value)]
                col_mean = good_values.mean()

                # Replace all occurrences of that suspicious value by mean
                df[col] = df[col].apply(lambda x: col_mean if np.isclose(x, value) else x)

    # Handle outliers (IQR method)
    for col in ['Price', 'Open', 'High', 'Low', 'Vol.']:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df[col] = np.where(df[col] < lower_bound, lower_bound, df[col])
        df[col] = np.where(df[col] > upper_bound, upper_bound, df[col])

    return df

# --- Process Each File ---
print(f"Current Working Directory: {os.getcwd()}")

for file_name in file_list:
    try:
        print(f"\n🔍 Smart Cleaning {file_name}...")

        file_path = os.path.join(base_folder, file_name)
        df = pd.read_csv(file_path)

        cleaned_df = smart_clean_dataframe(df)

        # Save cleaned version
        cleaned_path = os.path.join(output_folder, file_name)
        cleaned_df.to_csv(cleaned_path, index=False)

        print(f"✅ Cleaned and saved: {cleaned_path}")

    except Exception as e:
        print(f"❌ Error cleaning {file_name}: {e}")

print("\n🏆 All selected crypto files cleaned SMARTLY with ANY repeating value handling and saved successfully!")
