import re
import numpy as np
import ollama
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
from lib.mongo_helpers import update_fund_field, get_all_funds_with_raw_text


OLLAMA_MODEL = "nomic-embed-text"
SIMILARITY_THRESHOLD = 0.5
CHUNK_TOKEN_LIMIT = 700
MIN_TOKENS = 10  # Minimum tokens to keep a chunk

# --- Functions ---

def split_into_sentences(text):
    """Split text into sentences based on punctuation."""
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]

def get_embeddings(sentences):
    """Generate embeddings for a list of sentences."""
    embeddings = []
    for sentence in sentences:
        response = ollama.embeddings(
            model=OLLAMA_MODEL,
            prompt=sentence
        )
        embeddings.append(response["embedding"])
    return np.array(embeddings, dtype="float32")

def chunk_semantically(sentences, embeddings):
    """Group sentences into chunks based on semantic similarity."""
    if not sentences:
        return []

    chunks = []
    current_chunk = []
    current_tokens = 0

    for i in range(len(sentences)):
        if current_chunk:
            sim = cosine_similarity(
                embeddings[i].reshape(1, -1),
                embeddings[i-1].reshape(1, -1)
            )[0][0]
        else:
            sim = 1.0  # Always start new chunk with 100% similarity

        sentence_tokens = int(len(sentences[i].split()) * 1.3)  # Approximate token count

        if sim < SIMILARITY_THRESHOLD or current_tokens + sentence_tokens > CHUNK_TOKEN_LIMIT:
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.split()) >= MIN_TOKENS:
                    chunks.append(chunk_text)
            current_chunk = []
            current_tokens = 0

        current_chunk.append(sentences[i])
        current_tokens += sentence_tokens

    if current_chunk:
        chunk_text = " ".join(current_chunk)
        if len(chunk_text.split()) >= MIN_TOKENS:
            chunks.append(chunk_text)

    return chunks

def main():
    print("🔄 Fetching documents from MongoDB...")

    funds = get_all_funds_with_raw_text()
    print(f"📄 Found {len(funds)} funds with raw text.")

    for fund in tqdm(funds, desc="🔪 Chunking funds"):
        fund_name = fund["fund_name"]
        text = fund.get("raw_text", "")

        sentences = split_into_sentences(text)
        if not sentences:
            print(f"⚠️ No sentences found in {fund_name}")
            continue

        embeddings = get_embeddings(sentences)
        chunks = chunk_semantically(sentences, embeddings)

        update_fund_field(fund_name, "cleaned_chunks", chunks)
        print(f"✅ Chunks saved for {fund_name}")

# --- Entry Point ---
if __name__ == "__main__":
    main()
