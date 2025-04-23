import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def load_questions(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_chunks(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_faiss_index(index_path: str) -> faiss.IndexFlatIP:
    return faiss.read_index(index_path)

def embed_questions(questions: list, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    model = SentenceTransformer(model_name)
    q_texts = [q["question"] for q in questions]
    return model.encode(q_texts, convert_to_numpy=True, normalize_embeddings=True)

def match_questions_to_chunks(questions_path, chunks_path, index_path, output_path, top_k=5):
    print("🔍 Chargement des données...")
    questions = load_questions(questions_path)
    chunks = load_chunks(chunks_path)
    index = load_faiss_index(index_path)

    print("🔗 Génération des embeddings des questions...")
    q_embeddings = embed_questions(questions)

    print(f"📌 Matching questions avec les {top_k} meilleurs chunks...")
    matches = []
    for idx, q_embed in enumerate(q_embeddings):
        scores, indices = index.search(np.array([q_embed]), top_k)
        matched_chunks = [chunks[i] for i in indices[0]]
        matches.append({
            "question_id": questions[idx]["id"],
            "question": questions[idx]["question"],
            "matched_chunks": [
                {
                    "chunk_id": c["chunk_id"],
                    "score": float(s),
                    "tags": c.get("tags", []),
                    "content": c["content"]
                } for c, s in zip(matched_chunks, scores[0])
            ]
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)
    print(f"✅ Matching sauvegardé dans : {output_path}")
