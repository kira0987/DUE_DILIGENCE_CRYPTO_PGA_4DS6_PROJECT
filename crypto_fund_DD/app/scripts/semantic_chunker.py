# scripts/semantic_chunker.py

import os
import glob
import shutil
import re
import numpy as np
import ollama
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity

# --- Settings ---
INPUT_DIR = "data/new_extracted/"
OUTPUT_DIR = "data/chunks/"            # ✅ save chunks directly in data/chunks/
ARCHIVE_DIR = "data/extracted_data/"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

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

def process_file(file_path):
    """Process a single extracted file into semantic chunks."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        sentences = split_into_sentences(text)
        if not sentences:
            print(f"⚠️ Warning: No valid sentences found in {file_path}")
            return

        embeddings = get_embeddings(sentences)
        chunks = chunk_semantically(sentences, embeddings)

        base_name = os.path.basename(file_path).replace(".txt", "")
        for idx, chunk in enumerate(chunks):
            chunk_path = os.path.join(OUTPUT_DIR, f"{base_name}_chunk_{idx+1}.txt")
            with open(chunk_path, "w", encoding="utf-8") as f_out:
                f_out.write(chunk)
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

def main():
    """Main pipeline: Process all new extracted files."""
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.txt")))
    print(f"📝 Found {len(files)} new extracted files to chunk.")

    if not files:
        print("⚠️ No new extracted files found!")
        return

    for file_path in tqdm(files, desc="🔪 Chunking files"):
        process_file(file_path)

    print(f"✅ All files chunked. Chunks saved to {OUTPUT_DIR}")

    for file_path in files:
        shutil.move(file_path, os.path.join(ARCHIVE_DIR, os.path.basename(file_path)))

    print(f"📦 Moved processed extracted files to {ARCHIVE_DIR}")

# --- Entry Point ---
if __name__ == "__main__":
    main()
