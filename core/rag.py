# === rag_search.py ===

import numpy as np
import ollama
from pinecone import Pinecone

# Initialize Pinecone API connection
PINECONE_API_KEY = 'pcsk_7E3NLX_FzLbGKM5Z4gg9ijL6juWyqfAsnH1cDuaFKovDy3rUjDLgySBqVDwnGnB9bddNA8'
PINECONE_ENVIRONMENT = 'gcp-starter'

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Connect to your existing index
index_name = "rag-index"
index = pc.Index(index_name)

# Embedding model name for Ollama
OLLAMA_EMBED_MODEL = 'nomic-embed-text:latest'  # ✅ Very precise name you asked for

def embed_with_ollama(text):
    """
    Send text to Ollama and get embedding using nomic-embed-text:latest model.
    """
    response = ollama.embeddings(
        model=OLLAMA_EMBED_MODEL,
        prompt=text
    )
    return response['embedding']

def query_pinecone(prompt, top_k=3):
    """
    Embed a prompt with Ollama and query Pinecone to retrieve top-k text chunks.
    
    Args:
        prompt (str): Input text.
        top_k (int): Number of top results.
    
    Returns:
        List[str]: Retrieved top matching document texts.
    """
    # Step 1: Embed the prompt
    embedded_prompt = embed_with_ollama(prompt)

    # Step 2: Query Pinecone
    search_response = index.query(
        vector=embedded_prompt,
        top_k=top_k,
        include_metadata=True
    )

    # Step 3: Extract matched texts
    top_texts = []
    for match in search_response['matches']:
        metadata = match.get('metadata', {})
        text = metadata.get('text', '')  # Adjust if your metadata uses a different field
        if text:
            top_texts.append(text)

    return top_texts
