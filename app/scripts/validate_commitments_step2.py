# scripts/validate_commitments_step2.py

import os
import json
import requests
from bs4 import BeautifulSoup
import time

# --- Paths ---
INPUT_VALIDATED_PATH = "data/commitments_validated.json"
OUTPUT_VALIDATED_STEP2_PATH = "data/commitments_validated_step2.json"

# --- Helper: Download and clean page text ---
def fetch_clean_text(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text.lower()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return ""

# --- Step 2 Validation ---
def validate_step2():
    if not os.path.exists(INPUT_VALIDATED_PATH):
        print("❌ No commitments_validated.json found!")
        return

    with open(INPUT_VALIDATED_PATH, "r", encoding="utf-8") as f:
        commitments = json.load(f)

    final_validations = []

    for item in commitments:
        sentence = item["commitment_sentence"]
        links = item.get("evidence_links", [])
        
        print(f"🔍 Deep validating: {sentence}")

        confirmed = False

        for link in links:
            if not link.startswith("http"):
                continue  # Skip invalid links

            page_text = fetch_clean_text(link)
            if "cryptofundx" in page_text:
                confirmed = True
                break  # No need to check more links once confirmed

            time.sleep(1)  # Be polite to servers

        status = "Confirmed ✅" if confirmed else "Unconfirmed ⚪"

        final_validations.append({
            "source_file": item["source_file"],
            "commitment_sentence": sentence,
            "validation_status_step2": status,
            "original_links": links
        })

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_VALIDATED_STEP2_PATH, "w", encoding="utf-8") as f:
        json.dump(final_validations, f, indent=2, ensure_ascii=False)

    print(f"✅ Step 2 validation completed. Results saved to {OUTPUT_VALIDATED_STEP2_PATH}")

if __name__ == "__main__":
    validate_step2()
