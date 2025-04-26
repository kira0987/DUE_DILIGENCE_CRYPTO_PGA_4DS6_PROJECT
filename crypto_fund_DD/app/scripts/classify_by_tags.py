# classify_by_tags.py

import os
import json
import numpy as np
from tqdm import tqdm
import ollama
from sklearn.metrics.pairwise import cosine_similarity

# --- Configuration ---
INPUT_PATH = "data/question_bank.json"
OUTPUT_PATH = "data/classified_questions.json"
EMBED_MODEL = "nomic-embed-text"

# --- Final Professional Tags ---
TAGS = [
    "Legal & Regulatory",
    "AML / KYC",
    "Governance",
    "Financial Health",
    "IP & Contracts",
    "Custody & Asset Security",
    "Technology & Infrastructure",
    "Cybersecurity & Data Privacy",
    "Risk Management",
    "Tokenomics & Trading Integrity",
    "Strategy & Competitive Positioning",
    "ESG & Sustainability",
    "Community & UX"
]

# --- Get Embedding ---
def get_embedding(text):
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return np.array(response['embedding'], dtype='float32')

# --- Embed Tags Once ---
tag_embeddings = [get_embedding(tag) for tag in TAGS]

# --- Load Questions ---
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    questions = json.load(f)

classified = []

# --- Classify Each Question ---
for q in tqdm(questions, desc="🔍 Classifying questions"):
    question_id = q.get("id")
    question_text = q.get("question")
    
    if not question_text.strip():
        continue

    q_emb = get_embedding(question_text).reshape(1, -1)
    similarities = cosine_similarity(q_emb, tag_embeddings)[0]
    best_tag_idx = np.argmax(similarities)
    best_tag = TAGS[best_tag_idx]

    classified.append({
        "id": question_id,
        "question": question_text,
        "tag": best_tag
    })

# --- Save Output ---
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(classified, f, indent=2, ensure_ascii=False)

print(f"✅ Tagged {len(classified)} questions → {OUTPUT_PATH}")
