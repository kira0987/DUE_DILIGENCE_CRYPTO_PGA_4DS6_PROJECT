import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
import json
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures
from datetime import datetime

# Output directories
OUTPUT_DIR = "crypto_data"
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
METADATA_FILE = os.path.join(OUTPUT_DIR, "metadata.json")
for d in [OUTPUT_DIR, RAW_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# API endpoints and sources
SOURCES = {
    "sec_edgar": "https://www.sec.gov/edgar/search/",
    "coinmarketcap_api": "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
    "coingecko_api": "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&page=1",
    "messari_api": "https://data.messari.io/api/v1/assets",
    "cryptorank": "https://cryptorank.io/",
    "coinbase_hub": "https://www.coinbase.com/assethub",
    "github": "https://github.com/",
}

CMC_API_KEY = "f932df68-944e-4758-a892-a1ab52226f15"  # Replace with your CoinMarketCap API key

# Cache for failed URLs
FAILED_CACHE = set()

# Metadata storage
metadata = {"projects": {}}

async def download_file(session, url, project_name, category, file_type="pdf"):
    """Download a file asynchronously and save with category."""
    if url in FAILED_CACHE:
        return None
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                safe_name = "".join(c for c in project_name if c.isalnum() or c in " _-").strip()
                file_path = os.path.join(RAW_DIR, f"{safe_name}_{category}.{file_type}")
                with open(file_path, "wb") as f:
                    f.write(await response.read())
                print(f"Downloaded {category} for {project_name} to {file_path}")
                return file_path
            else:
                FAILED_CACHE.add(url)
                return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        FAILED_CACHE.add(url)
        return None

async def parse_page(session, url):
    """Parse a webpage asynchronously."""
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return BeautifulSoup(await response.text(), "html.parser")
            return None
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return None

async def fetch_sec_edgar(session, project_name):
    """Fetch SEC filings from EDGAR."""
    search_url = f"{SOURCES['sec_edgar']}?q={project_name}"
    soup = await parse_page(session, search_url)
    if not soup:
        return None
    
    filings = []
    for link in soup.select("a[href*='/Archives/edgar/data']")[:3]:  # Limit to 3 filings
        filing_url = urljoin("https://www.sec.gov", link["href"])
        file_path = await download_file(session, filing_url, project_name, "filing", "html")
        if file_path:
            filings.append({"type": "SEC Filing", "url": filing_url, "path": file_path})
    return filings

async def fetch_whitepaper(session, url, project_name):
    """Fetch whitepaper from a given URL."""
    soup = await parse_page(session, url)
    if not soup:
        return None
    
    link = soup.find("a", href=lambda href: href and "whitepaper" in href.lower())
    if link:
        wp_url = urljoin(url, link["href"])
        file_path = await download_file(session, wp_url, project_name, "whitepaper")
        return {"url": wp_url, "path": file_path} if file_path else None
    return None

async def fetch_coinmarketcap(session):
    """Fetch data from CoinMarketCap API."""
    url = SOURCES["coinmarketcap_api"]
    headers = HEADERS.copy()
    headers["X-CMC_PRO_API_KEY"] = CMC_API_KEY
    params = {"limit": 500}
    
    async with session.get(url, headers=headers, params=params) as response:
        if response.status != 200:
            print(f"CMC API Error: {response.status}")
            return []
        data = await response.json()
    
    projects = []
    for coin in data["data"]:
        name = coin["name"]
        slug = coin["slug"]
        coin_page = f"https://coinmarketcap.com/currencies/{slug}/"
        projects.append({"name": name, "page": coin_page, "tokenomics": {
            "max_supply": coin.get("max_supply"),
            "circulating_supply": coin.get("circulating_supply")
        }})
    return projects

async def fetch_coingecko(session):
    """Fetch data from CoinGecko API."""
    async with session.get(SOURCES["coingecko_api"]) as response:
        if response.status != 200:
            print(f"CoinGecko API Error: {response.status}")
            return []
        coins = await response.json()
    
    projects = []
    for coin in coins:
        name = coin["name"]
        coin_page = f"https://www.coingecko.com/en/coins/{coin['id']}"
        projects.append({"name": name, "page": coin_page, "tokenomics": {
            "max_supply": coin.get("max_supply"),
            "circulating_supply": coin.get("circulating_supply")
        }})
    return projects

async def fetch_messari(session):
    """Fetch data from Messari API."""
    async with session.get(SOURCES["messari_api"]) as response:
        if response.status != 200:
            print(f"Messari API Error: {response.status}")
            return []
        data = await response.json()
    
    projects = []
    for asset in data["data"][:100]:  # Limit for speed
        name = asset["name"]
        profile = asset.get("profile", {})
        projects.append({
            "name": name,
            "page": f"https://messari.io/asset/{asset['slug']}",
            "tokenomics": profile.get("economics", {}),
            "team": profile.get("team", []),
            "governance": profile.get("governance", {})
        })
    return projects

def fetch_cryptorank_sync():
    """Synchronous scrape for CryptoRank (Selenium)."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(SOURCES["cryptorank"])
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    
    projects = []
    for row in soup.select("tr[data-slug]")[:50]:  # Limit for speed
        name_tag = row.find("span", class_="name")
        if name_tag:
            name = name_tag.text.strip()
            projects.append({"name": name, "page": SOURCES["cryptorank"] + row["data-slug"]})
    return projects

async def enrich_project(session, project):
    """Enrich project data with whitepapers, filings, etc."""
    name = project["name"]
    page = project["page"]
    
    # Whitepaper
    whitepaper = await fetch_whitepaper(session, page, name)
    
    # SEC Filings (if regulated)
    filings = await fetch_sec_edgar(session, name) if "regulated" in project.get("tags", []) else []
    
    # Placeholder for other data (expand as needed)
    data = {
        "whitepaper": whitepaper,
        "regulatory_filings": filings,
        "tokenomics": project.get("tokenomics", {}),
        "smart_contracts": {},  # Add Etherscan/GitHub scraping
        "team": project.get("team", []),
        "governance": project.get("governance", {}),
        "partnerships": {},  # Add manual scraping or API
        "compliance": {},  # Add KYC/AML policy scraping
        "risk_disclosures": {},  # Parse from whitepaper
        "financials": {},  # Add treasury wallet tracking
        "communication": {"page": page}
    }
    
    # Store metadata
    metadata["projects"][name] = {
        "raw_files": [f["path"] for f in data.values() if isinstance(f, dict) and "path" in f],
        "metadata": {
            "name": name,
            "date": datetime.now().isoformat(),
            "source": page,
            "language": "en",  # Assume English, refine later
            "file_types": ["pdf", "html"],
            "entities": {"team": [t.get("name") for t in data["team"]]},
            "risk_categories": ["legal", "financial"]  # Expand with NLP later
        },
        "data": data
    }

async def main():
    """Run the comprehensive scraping pipeline."""
    print("Starting comprehensive scraping pipeline...")
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Fetch project lists
        tasks = [
            fetch_coinmarketcap(session) if CMC_API_KEY != "f932df68-944e-4758-a892-a1ab52226f15" else asyncio.Future(),
            fetch_coingecko(session),
            fetch_messari(session)
        ]
        results = await asyncio.gather(*tasks)
        projects = [p for r in results if not isinstance(r, asyncio.Future) for p in r]
        
        # Synchronous CryptoRank scrape
        with concurrent.futures.ThreadPoolExecutor() as executor:
            cryptorank_future = executor.submit(fetch_cryptorank_sync)
            projects.extend(cryptorank_future.result())
        
        # Enrich projects
        enrich_tasks = [enrich_project(session, project) for project in projects[:100]]  # Limit for testing
        await asyncio.gather(*enrich_tasks)
    
    # Save metadata
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Scraping complete! Metadata saved to {METADATA_FILE}")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print(f"Completed in {time.time() - start_time:.2f} seconds")