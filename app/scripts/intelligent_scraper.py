import requests
from bs4 import BeautifulSoup
import random
import time

SERPER_API_KEY = "798ca12a9c64002017eb705eadd1a09d45360608"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0"
]

def scrape_webpage(url, retries=3):
    """Scrape and clean the text from a webpage."""
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS)  # Randomly choose a User-Agent for each request
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check for successful response
        if response.status_code != 200:
            if response.status_code == 403:
                print(f"Access denied to {url}. Status Code: 403")
            else:
                print(f"Error: Received status code {response.status_code} for URL: {url}")
            return ""
        
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text() for p in paragraphs])
        return text.strip()
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        if retries > 0:
            print(f"Retrying {url} ({retries} attempts left)...")
            time.sleep(2)  # wait before retrying
            return scrape_webpage(url, retries-1)
        else:
            print(f"Failed to retrieve data from {url} after multiple attempts.")
            return ""
        
def serper_search(query, num_results=5):
    """Use Serper.dev API to search."""
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": num_results
    }
    try:
        response = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
        response.raise_for_status()  # Check if the request was successful (status code 200)
        results = response.json()

        links = []
        for r in results.get("organic", []):
            links.append(r.get("link"))
            if len(links) >= num_results:
                break

        return links
    except requests.exceptions.RequestException as e:
        print(f"Error during the Serper API request: {e}")
        return []  # Return an empty list if the request fails

def intelligent_scrape(query, mode="serper", num_results=3):
    """Main function to search and scrape based on mode."""
    if mode == "serper":
        links = serper_search(query, num_results=num_results)
        if not links:
            print(f"No results found for query: {query}")
    else:
        raise ValueError("Invalid mode. Only 'serper' is supported.")

    scraped_texts = []
    for link in links:
        print(f"Scraping {link}...")  # Debugging: See which links are being processed
        text = scrape_webpage(link)
        if text:
            scraped_texts.append(text)
        else:
            print(f"No text found at {link}")

    return scraped_texts

# Testing the scraper
if __name__ == "__main__":
    query = "Crypto Capital Partners compliance"
    results = intelligent_scrape(query, mode="serper", num_results=3)
    print("Scraped results:")
    for result in results:
        print(result)
