import asyncio
import aiohttp
import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from typing import Dict, List


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Configuration
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/"
MAX_CONCURRENT_REQUESTS = 3  # Conservative to avoid blocks
REQUEST_TIMEOUT = 60
RETRIES = 3
BASE_DELAY = 1.5
OUTPUT_DIR = "sec_filings_2018_2025"
os.makedirs(OUTPUT_DIR, exist_ok=True)

USER_AGENT = "YourOrg AdminContact (houssameddine.benkheder@esprit.tn)" 
KEY_FILING_TYPES = [
    "10-K", "10-Q", "8-K", "S-1", "S-3", "F-1", "F-10",
    "DEF 14A", "SC 13G", "SC 13D", "13F-HR", "D", "N-1A",
    "N-2", "N-3", "N-4", "N-6", "N-8", "N-CSR", "N-PX"
]
# Define the 15 regulatory funds with CIKs
funds = {
    "BlackRock": {"cik": "0001364742", "url": "https://www.blackrock.com"},
    "Blackstone": {"cik": "0001393818", "url": "https://www.blackstone.com"},
    "Fidelity": {"cik": "0000315066", "url": "https://www.fidelity.com"},
    "Ark Invest": {"cik": "0001577040", "url": "https://ark-invest.com"},
    "Franklin Templeton": {"cik": "0000038777", "url": "https://www.franklintempleton.com"},
    "Grayscale": {"cik": "0001588489", "url": "https://grayscale.com"},
    "Invesco": {"cik": "0000914208", "url": "https://www.invesco.com"},
    "VanEck": {"cik": "0000899458", "url": "https://www.vaneck.com"},
    "Bitwise": {"cik": "0001723596", "url": "https://bitwiseinvestments.com"},
    "WisdomTree": {"cik": "0000880631", "url": "https://www.wisdomtree.com"},
    "21Shares": {"cik": "0001840325", "url": "https://21shares.com"},
    "ProShares": {"cik": "0001174610", "url": "https://www.proshares.com"},
    "CoinShares": {"cik": "0001896782", "url": "https://coinshares.com"},
    "Galaxy Digital": {"cik": "0001731348", "url": "https://www.galaxydigital.io"},
    "Hashdex": {"cik": "0001816215", "url": "https://hashdex.com"}
}

def get_headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "text/html,application/xhtml+xml"
    }

async def fetch_with_retry(session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        for attempt in range(RETRIES):
            try:
                await asyncio.sleep(BASE_DELAY * (attempt + 0.5))  # Progressive delay
                async with session.get(url, headers=get_headers(), timeout=REQUEST_TIMEOUT) as response:
                    if response.status == 200:
                        return await response.read()
                    elif response.status == 403:
                        logging.warning(f"Access denied, retrying... (Attempt {attempt + 1})")
                        continue
                    response.raise_for_status()
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
        return None

async def get_filings_for_period(session: aiohttp.ClientSession, cik: str, filing_type: str, 
                               start_date: str, end_date: str, semaphore: asyncio.Semaphore):
    url = (f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
           f"&CIK={cik}&type={filing_type}"
           f"&dateb={end_date}&datea={start_date}"
           f"&count=100&output=atom")
    
    data = await fetch_with_retry(session, url, semaphore)
    if not data:
        return []

    soup = BeautifulSoup(data, "xml")
    entries = []
    for entry in soup.find_all("entry"):
        accession = entry.find("accession-number")
        filing_date = entry.find("filing-date")
        if accession and filing_date:
            entries.append({
                "accession": accession.text,
                "filing_date": filing_date.text,
                "url": f"{SEC_ARCHIVES_URL}edgar/data/{cik}/{accession.text.replace('-', '')}/{accession.text}.txt"
            })
    return entries

async def download_full_filing(session: aiohttp.ClientSession, filing_info: Dict, semaphore: asyncio.Semaphore):
    content = await fetch_with_retry(session, filing_info["url"], semaphore)
    if not content:
        return None
    
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        return content.decode('latin-1')  # Fallback encoding

async def process_fund(session: aiohttp.ClientSession, fund_name: str, fund_info: Dict, semaphore: asyncio.Semaphore):
    logging.info(f"Processing {fund_name}...")
    results = {}
    
    for filing_type in KEY_FILING_TYPES:
        filings = await get_filings_for_period(
            session, fund_info["cik"], filing_type,
            "20180101", "20251231", semaphore
        )
        
        if not filings:
            continue
            
        filing_data = []
        for filing in filings:
            content = await download_full_filing(session, filing, semaphore)
            if not content:
                continue
                
            # Save complete filing as TXT
            file_name = f"{fund_name}_{filing_type}_{filing['filing_date']}_{filing['accession']}.txt"
            file_path = os.path.join(OUTPUT_DIR, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            filing_data.append({
                "filing_date": filing["filing_date"],
                "accession": filing["accession"],
                "file_path": file_path,
                "size_kb": len(content) / 1024
            })
        
        if filing_data:
            results[filing_type] = filing_data
    
    return {fund_name: results} if results else None

async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    connector = aiohttp.TCPConnector(limit_per_host=2, force_close=True)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [process_fund(session, name, info, semaphore) for name, info in funds.items()]
        results = await asyncio.gather(*tasks)
        
        # Save metadata
        metadata = {
            "retrieved": datetime.now().isoformat(),
            "time_period": {"start": "2018-01-01", "end": "2025-12-31"},
            "funds": {k: v for r in results if r for k, v in r.items()}
        }
        
        with open(os.path.join(OUTPUT_DIR, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        logging.info(f"Completed! Files saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info("Starting SEC filings download (2018-2025)")
    
    asyncio.run(main())
    
    duration = datetime.now() - start_time
    logging.info(f"Total execution time: {duration}")