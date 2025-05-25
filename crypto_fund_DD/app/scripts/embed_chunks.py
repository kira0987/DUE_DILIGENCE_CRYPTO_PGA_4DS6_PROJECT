# --- embed_chunks.py (store list of embeddings per fund) ---
import numpy as np
import ollama
from tqdm import tqdm
from lib.mongo_helpers import get_all_funds_with_chunks, update_fund_field
OLLAMA_MODEL = "nomic-embed-text"

def generate_embedding(text):
    response = ollama.embeddings(
        model=OLLAMA_MODEL,
        prompt=text
    )
    return response["embedding"]

def main():
    print("🔄 Fetching cleaned chunks from MongoDB...")
    funds = get_all_funds_with_chunks()
    print(f"📦 Found {len(funds)} funds with cleaned chunks.")

    for fund in tqdm(funds, desc="🚀 Embedding chunks"):
        fund_name = fund["fund_name"]
        chunks = fund.get("cleaned_chunks", [])

        all_embeddings = []
        for chunk in chunks:
            embedding = generate_embedding(chunk)
            all_embeddings.append(embedding)

        update_fund_field(fund_name, "embeddings", all_embeddings)
        print(f"✅ Stored {len(all_embeddings)} embeddings for {fund_name}")

    print("🏁 All fund embeddings stored in MongoDB.")
if __name__ == "__main__":
    main()
