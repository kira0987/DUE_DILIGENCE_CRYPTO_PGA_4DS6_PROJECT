import os
import json
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util
from core.extractor import extract_text
from core.cleaner import clean_text_and_detect_sections
from core.chunker import chunk_sections, embed_chunks

# Chargement du modèle à l'initialisation
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def generate_answer(question: str, chunks: List[Dict], top_k: int = 5) -> str:
    question_embedding = model.encode(question, convert_to_tensor=True)
    chunk_embeddings = embed_chunks(chunks)

    scores = util.cos_sim(question_embedding, chunk_embeddings)[0]
    top_matches = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    relevant_chunks = [chunks[i]["content"] for i, _ in top_matches]

    answer = f"💬 Réponse basée sur {top_k} passages :\n\n" + "\n---\n".join(relevant_chunks)
    return answer

def answer_all_questions(pdf_path: str, questions_path: str, top_k: int = 5) -> Dict[int, Dict[str, str]]:
    print(f"📄 Lecture du PDF : {pdf_path}")
    raw_text = extract_text(pdf_path)
    cleaned_text, sections = clean_text_and_detect_sections(raw_text)
    chunks = chunk_sections(sections)
    chunk_embeddings = embed_chunks(chunks)

    print(f"🔍 Chargement des questions : {questions_path}")
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    question_texts = [q["question"] for q in questions]
    question_embeddings = model.encode(question_texts, convert_to_tensor=True)

    print("⚡ Calcul des similarités...")
    similarities = util.cos_sim(question_embeddings, chunk_embeddings)

    answers = {}
    for i, q in enumerate(questions):
        top_matches = sorted(
            list(enumerate(similarities[i])),
            key=lambda x: x[1], reverse=True
        )[:top_k]

        relevant_chunks = [chunks[j]["content"] for j, _ in top_matches]
        response = f"💬 Réponse basée sur {top_k} passages :\n\n" + "\n---\n".join(relevant_chunks)

        answers[q["id"]] = {
            "question": q["question"],
            "answer": response
        }

    return answers


def save_answers(answers: Dict[int, Dict[str, str]], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(answers, f, indent=2, ensure_ascii=False)
    print(f"✅ Réponses sauvegardées dans : {output_path}")
