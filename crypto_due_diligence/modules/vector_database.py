import faiss
import numpy as np
import json
import ollama  # ✅ Using Ollama for embeddings & chat response

VECTOR_SIZE = 768  # Nomic embedding output size

def generate_embedding(text):
    """Generates Nomic embeddings using Ollama."""
    response = ollama.embeddings(model="nomic-embed-text", prompt=text)  # ✅ Ensure input is a string
 # ✅ Ensure input is a list
    return response["embedding"]

def save_to_faiss(chunks, index_path="test_pdfs/extracted/embeddings.index"):
    """Stores chunk embeddings in a FAISS vector database."""
    embeddings = np.array([generate_embedding(chunk["text"]) for chunk in chunks], dtype=np.float32)

    # ✅ Ensure correct FAISS index handling
    index = faiss.IndexFlatL2(VECTOR_SIZE)
    index.add(embeddings)

    # Save FAISS index
    faiss.write_index(index, index_path)
    print(f"✅ FAISS vector database saved to {index_path}")

    # Save chunk metadata (IDs to text mapping)
    metadata_path = index_path.replace(".index", "_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4)

def load_faiss_index(index_path="test_pdfs/extracted/embeddings.index"):
    """Loads the FAISS vector database."""
    return faiss.read_index(index_path)

def search_faiss(query, k=5, index_path="test_pdfs/extracted/embeddings.index"):
    """Searches FAISS for relevant document chunks and generates an LLM response."""
    index = load_faiss_index(index_path)

    # ✅ Fix query embedding issue
    query_embedding = np.array(generate_embedding(query), dtype=np.float32).reshape(1, -1)

    # ✅ Fix FAISS search dimension mismatch
    if index.ntotal == 0:
        return ["⚠️ No embeddings found in FAISS. Ensure embeddings were generated correctly."]

    # Search for top-k results
    distances, indices = index.search(query_embedding, k)

    # Load metadata to get text chunks
    metadata_path = index_path.replace(".index", "_metadata.json")
    with open(metadata_path, "r") as f:
        chunks = json.load(f)

    # ✅ Fix: Ensure retrieved text is properly formatted into full sentences
    retrieved_chunks = [chunks[i]["text"] for i in indices[0] if i < len(chunks)]
    
    # ✅ Ensure text is joined properly
    context_text = " ".join(retrieved_chunks).replace("\n", " ")  # Ensure smooth formatting

    # ✅ Ensure proper LLM response handling
    response = ollama.chat(
        model="llama3.1",
        messages=[
            {"role": "system", "content": "You are an AI that provides precise answers based on retrieved document content."},
            {"role": "user", "content": f"Here is relevant text from the document:\n\n{context_text}\n\nUser Question: {query}\n\nProvide a clear and structured response:"}
        ]
    )

    return response["message"]["content"]  # ✅ Return the LLM-generated answer
