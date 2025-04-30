import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
from webdriver_manager.chrome import ChromeDriverManager  # Added for auto ChromeDriver management

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directory to save whitepapers
OUTPUT_DIR = "whitepapers_1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Base URL
BASE_URL = "https://www.allcryptowhitepapers.com/whitepaper-overview/"

def setup_selenium():
    """Initialize Selenium WebDriver with headless Chrome."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Auto-install compatible ChromeDriver
    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def get_whitepaper_links(driver):
    """Scrape all whitepaper detail page links from the overview with retries."""
    all_links = set()
    total_pages = 40  # 40 pages as per site structure
    retries = 3

    for attempt in range(retries):
        try:
            driver.get(BASE_URL)
            # Wait for the table with ID 'whitepaper_table' (more specific)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "whitepaper_table"))
            )
            break
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed to load page: {e}")
            if attempt == retries - 1:
                logging.error("Max retries reached. Dumping page source for debugging:")
                logging.error(driver.page_source[:1000])  # Log first 1000 chars
                raise
            time.sleep(2 ** attempt)

    for page in tqdm(range(total_pages), desc="Scraping overview pages"):
        # Extract links from current page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", {"id": "whitepaper_table"})
        if table:
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                link = row.find("a", href=True)
                if link and "whitepaper" in link["href"]:
                    full_url = f"https://www.allcryptowhitepapers.com{link['href']}"
                    all_links.add(full_url)
        else:
            logging.warning(f"No table found on page {page + 1}")
        
        # Navigate to next page if not the last
        if page < total_pages - 1:
            try:
                next_button = driver.find_element(By.XPATH, "//a[@aria-label='Next']")
                if "disabled" not in next_button.get_attribute("class"):
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)  # Increased wait for stability
                else:
                    logging.info("Reached last page early")
                    break
            except Exception as e:
                logging.error(f"Pagination error on page {page + 1}: {e}")
                break
    
    logging.info(f"Found {len(all_links)} unique whitepaper links")
    return list(all_links)

def get_pdf_url(detail_url, driver):
    """Extract the final PDF URL from a whitepaper detail page."""
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Look for PDF links in the page
        pdf_link = soup.find("a", href=lambda href: href and href.endswith(".pdf"))
        if pdf_link:
            pdf_url = pdf_link["href"]
            if not pdf_url.startswith("http"):
                pdf_url = f"https://www.allcryptowhitepapers.com{pdf_url}"
            return pdf_url
        
        # Check for external redirects or embedded links
        all_links = soup.find_all("a", href=True)
        for link in all_links:
            href = link["href"]
            if "whitepaper" in href.lower() or href.endswith(".pdf"):
                if not href.startswith("http"):
                    href = f"https://www.allcryptowhitepapers.com{href}"
                # Validate if it’s a PDF by fetching headers
                response = requests.head(href, allow_redirects=True, timeout=5)
                if response.headers.get("content-type") == "application/pdf":
                    return href
        
        logging.warning(f"No PDF found for {detail_url}")
        return None
    except Exception as e:
        logging.error(f"Error fetching PDF URL from {detail_url}: {e}")
        return None

def download_pdf(pdf_url, filename):
    """Download the PDF file."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(pdf_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded: {filepath}")
    except Exception as e:
        logging.error(f"Failed to download {pdf_url}: {e}")

def main():
    driver = setup_selenium()
    try:
        # Step 1: Get all whitepaper detail links
        whitepaper_links = get_whitepaper_links(driver)
        
        # Step 2: Process each link to find and download PDFs
        for i, link in enumerate(tqdm(whitepaper_links, desc="Downloading whitepapers")):
            pdf_url = get_pdf_url(link, driver)
            if pdf_url:
                # Generate a unique filename
                filename = f"whitepaper_{i+1}_{pdf_url.split('/')[-1].replace('/', '_')}"
                if not filename.endswith(".pdf"):
                    filename += ".pdf"
                download_pdf(pdf_url, filename)
              # Rate limiting
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()