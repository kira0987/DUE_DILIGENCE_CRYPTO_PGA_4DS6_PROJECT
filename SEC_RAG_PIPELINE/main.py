# sec_rag_pipeline/main.py - Optimized Version
import pandas as pd
import os
import asyncio
import aiohttp
from tqdm import tqdm
import random
import time
import json
from pathlib import Path
from utils.fetch_sec_txt import fetch_sec_filing
from utils.parse_and_clean import clean_filing_text
from utils.ocr_fallback import ocr_if_needed
from utils.build_vectorstore import build_vector_store
from utils.query_rag import ask_question, analyze_filing_time_series
from utils.cik_utils import CIKManager


manager = CIKManager()

# Config
CSV_PATH = "sec_edgar_daily_indexes_2014_2025.csv"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/"
OUTPUT_DIR = "output/"
CACHE_DIR = os.path.join(OUTPUT_DIR, "cache")
CIK_CACHE_FILE = os.path.join(OUTPUT_DIR, "cik_cache.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Houssam CRYPTODUEDILIGENCE (houssameddine.benkheder@esprit.tn)",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

def load_cik_cache():
    if os.path.exists(CIK_CACHE_FILE):
        with open(CIK_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cik_cache(cache):
    with open(CIK_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def build_sec_url(cik, accession_number_with_dashes):
    accession_folder = accession_number_with_dashes.replace('-', '')
    return f"{SEC_ARCHIVES_URL}edgar/data/{cik}/{accession_folder}/{accession_number_with_dashes}.txt"

async def async_fetch(session, url, cache_path, pbar):
    try:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                raw_text = await response.text()
                cleaned_text = clean_filing_text(raw_text)
                final_text = ocr_if_needed(cleaned_text)
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(final_text)
                pbar.update(1)
                return (f"\n\n--- Filing: {os.path.basename(cache_path)} ---\n\n" + final_text, True)
            else:
                pbar.write(f"⚠️ Failed {url} (Status: {response.status})")
    except Exception as e:
        pbar.write(f"⚠️ Error fetching {url}: {str(e)[:100]}...")
    pbar.update(1)
    return ("", False)

def read_cached_file(cache_path, accession):
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            content = f.read()
        return (f"\n\n--- Filing: {accession} (cached) ---\n\n" + content, True)
    except Exception as e:
        return (f"\n\n⚠️ Error reading cached file {accession}: {str(e)[:100]}...", False)

async def fetch_all_async(filing_records):
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
        with tqdm(total=len(filing_records), desc="📥 Fetching Filings", unit="file",
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            tasks = []
            for row in filing_records:
                cik = row['CIK']
                accession = row['File Name'].split('/')[-1].replace('.txt', '')
                cache_path = os.path.join(CACHE_DIR, f"{accession}.txt")
                
                if os.path.exists(cache_path):
                    tasks.append(asyncio.to_thread(read_cached_file, cache_path, accession))
                else:
                    url = build_sec_url(cik, accession)
                    tasks.append(async_fetch(session, url, cache_path, pbar))
                    await asyncio.sleep(random.uniform(0.1, 0.5))
            
            results = await asyncio.gather(*tasks)
            successful_fetches = sum(1 for _, success in results if success)
            pbar.write(f"\n✅ Fetch completed: {successful_fetches} successful | {len(filing_records)} total")
            return [text for text, _ in results]

def train_with_progress(all_text):
    with tqdm(total=3, desc="🛠️ Training Model", unit="step",
             bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        pbar.set_postfix({"stage": "Preprocessing"})
        time.sleep(0.5)
        pbar.update(1)
        
        pbar.set_postfix({"stage": "Vectorizing"})
        db = build_vector_store(all_text)
        pbar.update(1)
        
        pbar.set_postfix({"stage": "Indexing"})
        time.sleep(0.5)
        pbar.update(1)
        
    return db

if __name__ == "__main__":
    print("\n🔍 Loading SEC Index CSV...")
    df = pd.read_csv(CSV_PATH)
    
    # Load CIK cache
    cik_cache = load_cik_cache()
    
    user_cik = input("Enter exact CIK to fetch all filings (or 'list' to see cached CIKs): ").strip()
    
    if user_cik.lower() == 'list':
        print("\n📋 Recently processed CIKs:")
        for i, cik in enumerate(cik_cache.keys(), 1):
            print(f"{i}. {cik} - {cik_cache[cik]['name']} ({len(cik_cache[cik]['filings'])} filings)")
        exit()
    
    if not user_cik.isdigit():
        print("❌ CIK must be numeric.")
        exit()
    
    matching_filings = df[df['CIK'].astype(str) == user_cik]
    if matching_filings.empty:
        print("❌ No filings found for this CIK.")
        exit()
    
    # Update CIK cache
    company_name = matching_filings.iloc[0]['Company Name']
    cik_cache[user_cik] = {
        'name': company_name,
        'filings': matching_filings['File Name'].tolist(),
        'last_accessed': str(pd.Timestamp.now())
    }
    save_cik_cache(cik_cache)
    
    print("\n🔎 Found filings:")
    print(matching_filings[['CIK', 'Company Name', 'Form Type', 'Date Filed', 'File Name']].head(10))
    
    print("\n⚡ Fetching filings...")
    try:
        filings = asyncio.run(fetch_all_async(matching_filings.to_dict('records')))
    except Exception as e:
        print(f"❌ Critical error during fetching: {str(e)[:200]}...")
        exit()
    
    all_text = "".join([f for f in filings if f])
    if not all_text:
        print("❌ No valid filing content was retrieved.")
        exit()
    
    temp_path = os.path.join(OUTPUT_DIR, f"{user_cik}_combined_filings.txt")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(all_text)
    
    summary, chart_path = analyze_filing_time_series(user_cik, company_name)
    print("\n📈 Time Series Summary:")
    print(summary)
    print(f"Chart saved to: {chart_path}")
    
    print("\n")
    db = train_with_progress(all_text)
    
    while True:
        question = input("\n💬 Ask a question about this company's filings (or type 'exit'): ").strip()
        if question.lower() == 'exit':
            break
        response = ask_question(db, question)
        print("\n🤖 Answer:", response)
        with open(os.path.join(OUTPUT_DIR, f"{user_cik}_extracted_metadata.txt"), "a", encoding="utf-8") as f:
            f.write(f"\n\nQuestion: {question}\nAnswer: {response}\n")