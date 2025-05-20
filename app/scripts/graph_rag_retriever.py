# --- graph_rag_retriever.py (MongoDB version, no local FAISS files) ---

import numpy as np
import faiss
import ollama
from tqdm import tqdm
from lib.mongo_helpers import get_all_funds_with_embeddings

TOP_K_FAISS = 100
TOP_K_FINAL = 15
MAX_TOKENS_CONTEXT = 3500
FAISS_INDEX = None
CHUNK_LOOKUP = {}

# --- Build FAISS Index in-memory from MongoDB ---
def build_faiss_index():
    global FAISS_INDEX, CHUNK_LOOKUP
    print("🔄 Building FAISS index from MongoDB...")
    
    funds = get_all_funds_with_embeddings()
    all_embeddings = []
    all_ids = []

    for fund in funds:
        fund_name = fund["fund_name"]
        chunks = fund.get("cleaned_chunks", [])
        embeddings = fund.get("embeddings", [])

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{fund_name}_chunk_{i+1}"
            all_embeddings.append(emb)
            all_ids.append(chunk_id)
            CHUNK_LOOKUP[chunk_id] = chunk

    if not all_embeddings:
        raise RuntimeError("❌ No embeddings found in MongoDB to build FAISS index.")

    xb = np.array(all_embeddings).astype("float32")
    faiss.normalize_L2(xb)

    index = faiss.IndexFlatIP(xb.shape[1])
    index.add(xb)

    FAISS_INDEX = index
    print(f"✅ FAISS index built with {len(all_ids)} chunks.")
    return all_ids

# --- Retrieve matching chunk IDs from FAISS ---
def semantic_retrieve(question_embedding, all_ids):
    faiss.normalize_L2(question_embedding)
    D, I = FAISS_INDEX.search(question_embedding, TOP_K_FAISS)
    return [all_ids[i] for i in I[0] if i < len(all_ids)]

# --- Trim chunk context to token limit ---
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

    all_ids = build_faiss_index()

    try:
        response = ollama.embeddings(model="nomic-embed-text", prompt=question)
        query_emb = np.array([response["embedding"]], dtype="float32")
    except Exception as e:
        print(f"❌ Failed to embed question: {e}")
        return None

    # Semantic search
    faiss_ids = semantic_retrieve(query_emb, all_ids)
    print(f"🔍 Retrieved {len(faiss_ids)} chunks from FAISS.")

    if source_filter:
        filtered = [cid for cid in faiss_ids if cid.startswith(source_filter)]
        print(f"🛡️ Source Filter: {len(filtered)} remain.")
        if filtered:
            faiss_ids = filtered

    selected_chunks = [CHUNK_LOOKUP[cid] for cid in faiss_ids if cid in CHUNK_LOOKUP]
    context = trim_context(selected_chunks[:TOP_K_FINAL])

    if len(context.strip()) < 30:
        print("⚠️ Final context too small after trimming.")
        return None

    print("\n📚 Final Context Sent to LLM:")
    print("=" * 80)
    print(context)
    print("=" * 80)

    return context
