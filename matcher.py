import json
import os
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util

MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def load_questions(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def match_question_to_chunks(question: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
    question_embedding = MODEL.encode(question, convert_to_tensor=True)
    chunk_embeddings = [chunk["embedding"] for chunk in chunks]

    # Convertir les embeddings en tenseur
    import torch
    chunk_embeddings_tensor = torch.stack([torch.tensor(embedding) for embedding in chunk_embeddings])
    scores = util.cos_sim(question_embedding, chunk_embeddings_tensor)[0]

    top_results = sorted(
        list(enumerate(scores)),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]

    return [chunks[i] for i, _ in top_results]
q