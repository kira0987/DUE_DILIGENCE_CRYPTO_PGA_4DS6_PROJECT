# scripts/validate_commitments.py

import os
import json
import time
import requests
from googlesearch import search

# --- Load Commitments ---
COMMITMENTS_PATH = "data/commitments.json"
OUTPUT_VALIDATED_PATH = "data/commitments_validated.json"

# --- Helper: Google Search (Professional Wording)
def search_google(query, num_results=5):
    try:
        return list(search(query, num_results=num_results, lang='en'))
    except Exception as e:
        print(f"❌ Google search failed for {query}: {e}")
        return []

# --- Helper: Simple Evidence Detector
def validate_commitment(commitment_text):
    evidence_links = []
    search_queries = [
        commitment_text,
        f"CryptoFundX {commitment_text}",
        f"CryptoFundX fulfillment of {commitment_text}",
        f"CryptoFundX achievement {commitment_text}",
        f"CryptoFundX audit report",  # Special boost for audits
        f"CryptoFundX carbon neutrality"  # Special boost for environmental promises
    ]

    for query in search_queries:
        links = search_google(query)
        evidence_links.extend(links)
        time.sleep(1)  # avoid hitting too fast

    return evidence_links

# --- Main Validation Process ---
def validate_all_commitments():
    if not os.path.exists(COMMITMENTS_PATH):
        print("❌ No commitments.json found!")
        return

    with open(COMMITMENTS_PATH, "r", encoding="utf-8") as f:
        commitments = json.load(f)

    validated = []

    for item in commitments:
        sentence = item["commitment_sentence"]
        print(f"🔎 Validating: {sentence}")
        evidence = validate_commitment(sentence)

        status = "Confirmed" if evidence else "Unconfirmed"

        validated.append({
            "source_file": item["source_file"],
            "commitment_sentence": sentence,
            "validation_status": status,
            "evidence_links": evidence
        })

    # Save Results
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_VALIDATED_PATH, "w", encoding="utf-8") as f:
        json.dump(validated, f, indent=2, ensure_ascii=False)

    print(f"✅ Validation completed. Results saved to {OUTPUT_VALIDATED_PATH}")


if __name__ == "__main__":
    validate_all_commitments()
