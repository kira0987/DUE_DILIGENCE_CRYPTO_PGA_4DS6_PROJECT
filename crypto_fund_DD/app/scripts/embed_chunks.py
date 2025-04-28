import os
import glob
import numpy as np
import faiss
from tqdm import tqdm
import ollama

# --- Settings ---
CHUNK_DIR = "data/chunks/"             # 🔥 Work directly here
EMBEDDING_DIR = "data/embeddings/"
FAISS_INDEX_PATH = "data/faiss_index.index"
OLLAMA_MODEL = "nomic-embed-text"

os.makedirs(EMBEDDING_DIR, exist_ok=True)

def main():
    # --- Load Chunks ---
    chunk_files = sorted(glob.glob(os.path.join(CHUNK_DIR, "*.txt")))

    if not chunk_files:
        print("🚫 No chunks to embed. Skipping embedding step.")
        return

    # --- Load Existing Embeddings if Available ---
    embeddings = None
    ids = []

    if os.path.exists(os.path.join(EMBEDDING_DIR, "embeddings.npy")) and os.path.exists(os.path.join(EMBEDDING_DIR, "ids.txt")):
        print("🔄 Loading existing embeddings...")
        embeddings = np.load(os.path.join(EMBEDDING_DIR, "embeddings.npy"))
        with open(os.path.join(EMBEDDING_DIR, "ids.txt"), "r", encoding="utf-8") as f:
            ids = f.read().splitlines()
    else:
        print("🆕 No previous embeddings found. Starting fresh.")

    embedded_chunk_ids = set(ids)

    # --- Find Truly New Chunks to Embed ---
    new_texts = []
    new_ids = []

    for file in tqdm(chunk_files, desc="🔍 Scanning chunks"):
        chunk_id = os.path.basename(file)
        if chunk_id not in embedded_chunk_ids:
            with open(file, "r", encoding="utf-8") as f:
                new_texts.append(f.read())
                new_ids.append(chunk_id)

    print(f"✅ Found {len(new_texts)} new chunks to embed.")

    if not new_texts:
        print("🚫 No truly new chunks to embed.")
        return

    # --- Generate Embeddings for New Chunks Only ---
    print("🚀 Generating embeddings with Ollama (nomic-embed-text)...")
    new_embeddings = []

    for text in tqdm(new_texts, desc="Embedding chunks"):
        response = ollama.embeddings(
            model=OLLAMA_MODEL,
            prompt=text
        )
        embedding = response['embedding']
        new_embeddings.append(embedding)

    new_embeddings = np.array(new_embeddings, dtype='float32')

    # --- Normalize New Embeddings ---
    faiss.normalize_L2(new_embeddings)

    # --- Save Updated Embeddings and IDs ---
    if embeddings is not None:
        all_embeddings = np.vstack([embeddings, new_embeddings])
    else:
        all_embeddings = new_embeddings

    all_ids = ids + new_ids

    np.save(os.path.join(EMBEDDING_DIR, "embeddings.npy"), all_embeddings)
    with open(os.path.join(EMBEDDING_DIR, "ids.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(all_ids))

    print(f"✅ Updated embeddings and IDs saved to {EMBEDDING_DIR}")

    # --- Update FAISS Index with Only New Embeddings ---
    if os.path.exists(FAISS_INDEX_PATH):
        print("🔄 Loading existing FAISS index...")
        index = faiss.read_index(FAISS_INDEX_PATH)
    else:
        print("🆕 Creating new FAISS index...")
        dim = new_embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)

    index.add(new_embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)

    print(f"✅ FAISS Index updated and saved to {FAISS_INDEX_PATH}")

    print("🏁 Embedding step complete!")

# --- Main entry ---
if __name__ == "__main__":
    main()
