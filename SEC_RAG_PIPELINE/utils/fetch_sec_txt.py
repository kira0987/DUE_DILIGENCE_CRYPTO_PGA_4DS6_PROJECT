# utils/fetch_sec_txt.py
import requests
import time
import random

def fetch_sec_filing(url, max_retries=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (RAG Platform for Research)',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                wait = (2 ** attempt) + random.random()
                time.sleep(wait)
                continue
            else:
                print(f"⚠️ HTTP {response.status_code} for {url}")
                return None
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)[:100]}...")
            time.sleep(1 + attempt * 2)
    
    print(f"❌ Max retries exceeded for {url}")
    return None