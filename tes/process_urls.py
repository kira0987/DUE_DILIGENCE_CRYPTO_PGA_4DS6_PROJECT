import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from fuzzywuzzy import fuzz
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import URL_PATTERN, KEYWORDS, lemmatizer, extract_entities, analyze_sentiment, BASE_RISK_CATEGORIES
import aiohttp
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DOMAIN_AUTHORITY = {
    '.gov': 10, '.edu': 9, '.org': 8, '.io': 7, '.co': 7, '.com': 6,
    'coinbase.com': 8, 'binance.com': 8, 'kraken.com': 8, 'gemini.com': 8,
    'sec.gov': 10, 'cftc.gov': 10, 'finra.org': 9
}

def rank_url(url):
    score = 6
    for domain, weight in DOMAIN_AUTHORITY.items():
        if domain in url:
            score = weight
            break
    return score

def setup_selenium():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize Selenium: {str(e)}")
        return None

async def fetch_web_content_async(url, retries=3):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    async with aiohttp.ClientSession() as session:
        for attempt in range(retries):
            try:
                async with session.get(url, headers=headers, timeout=5) as response:
                    response.raise_for_status()
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    title = soup.title.string if soup.title else "Untitled"
                    title = re.sub(r'[<>:"/\\|?*]', '', title.strip())[:50]
                    meta_desc = soup.find("meta", {"name": "description"})
                    metadata = {
                        "title": title,
                        "description": meta_desc["content"] if meta_desc else "",
                        "authority_score": rank_url(url)
                    }
                    text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
                    web_text = "\n".join(el.get_text(strip=True) for el in text_elements if el.get_text(strip=True))
                    if len(web_text.strip()) < 50 or not any(kw.lower() in web_text.lower() for kw in KEYWORDS):
                        logging.info(f"Low-value content at {url}. Attempting Selenium.")
                        driver = setup_selenium()
                        if driver:
                            driver.get(url)
                            time.sleep(1)
                            web_text = driver.find_element(By.TAG_NAME, "body").text
                            driver.quit()
                    if not web_text.strip():
                        logging.warning(f"No content extracted from {url}.")
                        return None, metadata
                    return web_text, metadata
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt / 2)  # Faster retry
                    continue
                logging.error(f"Failed to fetch {url} after {retries} attempts: {str(e)}")
                return None, {}

def process_url(url, idx, output_dir, seen_titles):
    try:
        web_text, web_meta = asyncio.run(fetch_web_content_async(url))
        if not web_text:
            return None, f"Failed to fetch content from {url}"
        title = web_meta["title"]
        if title in seen_titles:
            title = f"{title}_{idx + 1}"
        seen_titles.add(title)
        full_txt = os.path.join(output_dir, f"{title}.txt")
        with open(full_txt, "w", encoding="utf-8") as f:
            f.write(web_text)
        logging.info(f"Extracted full text from {url} to {full_txt}")
        if title in ["Untitled", "Redirecting"] or re.match(r"^(Untitled|Redirecting)_\d+$", title):
            os.remove(full_txt)
            logging.info(f"Deleted uninformative file: {full_txt}")
            return None, f"Removed {full_txt} (low value)"
        from chunk_text import semantic_chunking
        chunks = semantic_chunking(web_text, target_chunk_size=500)
        url_data = []
        for j, chunk in enumerate(chunks):
            chunk_text = chunk["text"]
            entities, anonymized_chunk = extract_entities(chunk_text, source_type="web")
            sentiment_data = analyze_sentiment(anonymized_chunk)
            metadata = {
                "matched_keywords": [kw for kw in KEYWORDS if kw.lower() in anonymized_chunk.lower()],
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["sentiment_score"],
                "risk_score": entities["risk_score"],
                "categories": {cat: [t for t in terms if t.lower() in anonymized_chunk.lower()] 
                               for cat, terms in BASE_RISK_CATEGORIES.items()},
                "entities": entities,
                "source": url,
                "region": entities["region"],
                "content_type": "web",
                "web_metadata": web_meta,
                "section": chunk["section"]
            }
            url_data.append({
                "chunk_id": f"web_{idx}_{j}",
                "title": f"Web Content: {url} - Chunk {j + 1}",
                "text": anonymized_chunk,
                "metadata": metadata
            })
        return url_data, None
    except Exception as e:
        return None, f"Error processing {url}: {str(e)}"

def process_urls(txt_file, output_dir):
    logging.info(f"Processing URLs from: {txt_file}")
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    urls = list(set(URL_PATTERN.findall(text)))
    urls = sorted(urls, key=rank_url, reverse=True)
    logging.info(f"Found {len(urls)} unique URLs, prioritized by authority")
    all_url_data = []
    issues = []
    seen_titles = set()
    batch_size = 10  # Process URLs in batches
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(process_url, url, i + j, output_dir, seen_titles): url 
                             for j, url in enumerate(batch_urls)}
            for future in as_completed(future_to_url):
                url_data, issue = future.result()
                if url_data:
                    all_url_data.extend(url_data)
                if issue:
                    issues.append(issue)
    url_prefix = os.path.join(output_dir, os.path.splitext(os.path.basename(txt_file))[0] + "_url")
    return all_url_data, url_prefix, issues