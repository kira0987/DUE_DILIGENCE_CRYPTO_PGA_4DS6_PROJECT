# scripts/graph_rag_retriever.py

import os
import pickle
import numpy as np
import faiss
import ollama
from tqdm import tqdm

# --- Settings ---
EMBEDDING_DIR = "data/embeddings/"
FAISS_INDEX_PATH = "data/faiss_index.index"
GRAPH_PATH = "data/graph.pkl"
CHUNK_DIR = "data/chunks/"
TOP_K_FAISS = 100
TOP_K_FINAL = 15
MAX_TOKENS_CONTEXT = 3500

# --- Lazy loaded variables ---
index = None
id_list = None
G = None

# --- Loading Functions ---
def load_faiss_and_ids():
    global index, id_list
    if index is None or id_list is None:
        if not (os.path.exists(FAISS_INDEX_PATH) and os.path.exists(os.path.join(EMBEDDING_DIR, "ids.txt"))):
            raise RuntimeError("❌ FAISS index or IDs file not found. Please process documents first.")
        try:
            print("🔄 Loading FAISS index and IDs...")
            index = faiss.read_index(FAISS_INDEX_PATH)
            with open(os.path.join(EMBEDDING_DIR, "ids.txt"), "r", encoding="utf-8") as f:
                id_list = f.read().splitlines()
            print("✅ FAISS and IDs loaded.")
        except Exception as e:
            raise RuntimeError(f"❌ Error loading FAISS/IDs: {e}")

def load_graph():
    global G
    if G is None:
        if not os.path.exists(GRAPH_PATH):
            raise RuntimeError("❌ Knowledge graph not found. Please build it first.")
        try:
            print("🔄 Loading Knowledge Graph...")
            with open(GRAPH_PATH, "rb") as f:
                G = pickle.load(f)
            print("✅ Graph loaded successfully.")
        except Exception as e:
            raise RuntimeError(f"❌ Error loading Graph: {e}")

# --- Helper Functions ---
def semantic_retrieve(query_emb, top_k=TOP_K_FAISS):
    faiss.normalize_L2(query_emb)
    D, I = index.search(query_emb, top_k)
    return [id_list[i] for i in I[0] if i < len(id_list)]

def graph_expand(chunk_ids):
    expanded = set(chunk_ids)
    for chunk_id in chunk_ids:
        if chunk_id in G:
            neighbors = list(G.neighbors(chunk_id))
            expanded.update(neighbors)
    return list(expanded)

def load_chunks(ids):
    texts = []
    for chunk_id in tqdm(ids, desc="📄 Loading chunks"):
        chunk_path = os.path.join(CHUNK_DIR, chunk_id)
        if os.path.exists(chunk_path):
            with open(chunk_path, "r", encoding="utf-8") as f:
                content = f.read()
                if len(content.split()) > 10:  # Ensure quality
                    texts.append(content)
    return texts

def trim_context(chunks, max_tokens=MAX_TOKENS_CONTEXT):
    context = ""
    total_tokens = 0
    for chunk in chunks:
        tokens = len(chunk.split())
        if total_tokens + tokens > max_tokens:
            break
        context += chunk + "\n\n"
        total_tokens += tokens
    return context.strip()

# --- Main Retrieval Function ---
def retrieve_context(question, source_filter=None):
    print(f"\n🔎 Building context for question: {question}")

    load_faiss_and_ids()
    load_graph()

    # Step 1: Embed the question
    try:
        response = ollama.embeddings(model="nomic-embed-text", prompt=question)
        query_emb = np.array([response['embedding']], dtype="float32")
    except Exception as e:
        print(f"❌ Failed to embed question: {e}")
        return None

    # Step 2: Semantic search
    faiss_ids = semantic_retrieve(query_emb)
    print(f"🔍 Retrieved {len(faiss_ids)} chunks from FAISS.")

    # Step 3: Source filter
    if source_filter:
        filtered_ids = [cid for cid in faiss_ids if cid.startswith(source_filter)]
        print(f"🛡️ Source Filter: {len(filtered_ids)} chunks remain after filtering.")
        if filtered_ids:
            faiss_ids = filtered_ids
        else:
            print("⚠️ No chunks after filtering. Falling back to all retrieved chunks.")

    # Step 4: Retry if needed
    if not faiss_ids:
        faiss_ids = semantic_retrieve(query_emb)
    if not faiss_ids:
        print("⚠️ Still no chunks found. Exiting retrieval.")
        return None

    # Step 5: Graph expansion
    expanded_ids = graph_expand(faiss_ids)
    print(f"🕸️ Expanded to {len(expanded_ids)} chunks after graph expansion.")

    # Step 6: Load text chunks
    candidate_chunks = load_chunks(expanded_ids)
    if not candidate_chunks:
        print("⚠️ No valid chunks found after loading from disk.")
        return None

    # Step 7: Top-N selection
    top_chunks = candidate_chunks[:TOP_K_FINAL]

    # Step 8: Trim
    context = trim_context(top_chunks)
    if len(context.strip()) < 30:
        print("⚠️ Final context too small after trimming.")
        return None

    print("\n📚 Final Context Sent to LLM:")
    print("=" * 80)
    print(context)
    print("=" * 80)

    return context
