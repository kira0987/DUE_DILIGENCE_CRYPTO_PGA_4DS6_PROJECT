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
from utils import URL_PATTERN, KEYWORDS, lemmatizer, extract_entities, extract_region, RISK_CATEGORIES, analyze_sentiment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DOMAIN_AUTHORITY = {
    '.gov': 10, '.edu': 9, '.org': 8, '.io': 7, '.co': 7, '.com': 6,
    'coinbase.com': 8, 'binance.com': 8, 'kraken.com': 8, 'gemini.com': 8
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
        logging.error(f"Failed to initialize Selenium driver: {str(e)}")
        return None

def fetch_web_content(url, retries=3):
    logging.debug(f"Fetching content from: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.title.string if soup.title else "Untitled"
            title = re.sub(r'[<>:"/\\|?*]', '', title.strip())[:50]
            metadata = {
                "title": title,
                "description": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "",
                "keywords": soup.find("meta", {"name": "keywords"})["content"] if soup.find("meta", {"name": "keywords"}) else "",
                "authority_score": rank_url(url)
            }

            text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            web_text = "\n".join(element.get_text(strip=True) for element in text_elements if element.get_text(strip=True))

            if len(web_text.strip()) < 50:
                driver = setup_selenium()
                if driver:
                    driver.get(url)
                    time.sleep(2)
                    web_text = driver.find_element(By.TAG_NAME, "body").text
                    driver.quit()

            if not web_text.strip():
                logging.warning(f"No content extracted from {url}.")
                return None, metadata
            return web_text, metadata
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            logging.error(f"Error fetching content from {url} after {retries} attempts: {str(e)}")
            return None, {}

def fuzzy_match_keyword(text, keyword, threshold=85):
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    text_words = [lemmatizer.lemmatize(word) for word in text_lower.split()]
    keyword_root = lemmatizer.lemmatize(keyword_lower)
    return any(fuzz.ratio(word, keyword_root) >= threshold for word in text_words)

def categorize_terms(text):
    text_lower = text.lower()
    categories = {cat: [] for cat in RISK_CATEGORIES}
    for category, terms in RISK_CATEGORIES.items():
        for term in terms:
            if fuzzy_match_keyword(text_lower, term):
                categories[category].append(term)
    return categories

def chunk_text(text, word_limit=500):
    words = text.split()
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for word in words:
        current_chunk.append(word)
        current_word_count += 1
        
        if current_word_count >= word_limit:
            chunk_content = " ".join(current_chunk)
            period_idx = chunk_content.find('.', len(" ".join(current_chunk[:word_limit])))
            if period_idx != -1:
                chunk_content = chunk_content[:period_idx + 1]
                remaining_text = chunk_content[period_idx + 1:].strip()
                chunks.append({"title": f"Chunk {len(chunks) + 1}", "text": chunk_content})
                current_chunk = remaining_text.split() if remaining_text else []
                current_word_count = len(current_chunk)
            else:
                chunks.append({"title": f"Chunk {len(chunks) + 1}", "text": chunk_content})
                current_chunk = []
                current_word_count = 0
    
    if current_chunk:
        chunks.append({"title": f"Chunk {len(chunks) + 1}", "text": " ".join(current_chunk)})
    return chunks

def process_url(url, idx, output_dir, seen_titles):
    try:
        web_text, web_meta = fetch_web_content(url)
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
            return None, f"Removed {full_txt} (Untitled or Redirecting)"
        
        chunks = chunk_text(web_text)
        url_data = []
        
        for j, chunk in enumerate(chunks):
            chunk_content = chunk["text"]
            matched_keywords = [kw for kw in KEYWORDS if fuzzy_match_keyword(chunk_content, kw)]
            entities = extract_entities(chunk_content, source_type="web")
            categories = categorize_terms(chunk_content)
            sentiment_data = analyze_sentiment(chunk_content)
            
            metadata = {
                "matched_keywords": matched_keywords,
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["sentiment_score"],
                "risk_score": entities["risk_score"],
                "categories": categories,
                "entities": entities,
                "source": url,
                "region": extract_region(chunk_content),
                "content_type": "web",
                "web_metadata": web_meta  # Added web-specific metadata
            }
            
            url_data.append({
                "chunk_id": f"web_{idx}_{j}",
                "title": f"Web Content: {url} - Chunk {j + 1}",
                "text": chunk_content,
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
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(process_url, url, i, output_dir, seen_titles): url for i, url in enumerate(urls)}
        for future in as_completed(future_to_url):
            url_data, issue = future.result()
            if url_data:
                all_url_data.extend(url_data)
            if issue:
                issues.append(issue)
    
    url_prefix = os.path.join(output_dir, os.path.splitext(os.path.basename(txt_file))[0] + "_url")
    return all_url_data, url_prefix, issues