import pandas as pd
import re

# Path to your large CSV file
csv_file = "sec_edgar_daily_indexes_2014_2025.csv"
chunksize = 100000  # Adjust for memory efficiency

# Crypto-related keywords
keywords = [
    "crypto", "blockchain", "bitcoin", "ethereum", "token", "digital asset",
    "defi", "ico", "nft", "stablecoin", "web3", "altcoin", "mining", "metaverse",
    "digital currency", "crypto fund", "digital wallet", "coin", "cryptoassets"
]
pattern = re.compile("|".join(keywords), re.IGNORECASE)

# Form types often linked to crypto activities
crypto_forms = {"d", "s-1", "s-3", "485bpos", "497", "8-k", "10-k", "20-f"}

results = []

for chunk in pd.read_csv(csv_file, chunksize=chunksize):
    chunk['Company Name'] = chunk['Company Name'].astype(str)
    chunk['Form Type'] = chunk['Form Type'].astype(str).str.lower()
    
    for _, row in chunk.iterrows():
        cik = str(row['CIK'])
        name = row['Company Name']
        form = row['Form Type']
        file = row['File Name']

        reason = None
        if re.search(pattern, name):
            reason = f"Name match: {name}"
        elif form in crypto_forms:
            reason = f"Form match: {form}"
        elif re.search(pattern, file):
            reason = f"Filename match: {file}"
        
        if reason:
            results.append(f"{cik}\t{name}  # {reason}")

# Save results to file
with open("likely_crypto_companies.txt", "w", encoding="utf-8") as f:
    for line in results:
        f.write(line + "\n")

print("✅ Analysis complete. File saved as 'likely_crypto_companies.txt'")
