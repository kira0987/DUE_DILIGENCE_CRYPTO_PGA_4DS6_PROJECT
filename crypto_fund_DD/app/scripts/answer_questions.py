# scripts/auto_answer_150_questions.py

import os
import json
import pandas as pd
from tqdm import tqdm

# Correct imports
from scripts.graph_rag_retriever import retrieve_context
from scripts.llm_responder import ask_llm

# --- Paths ---
QUESTION_BANK_PATH = "data/question_bank.json"   # Your custom question list
OUTPUT_PATH = "data/auto_answered_questions.csv"

# --- Load Question Bank ---
print("🔄 Loading question bank...")
with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
    questions = json.load(f)

print(f"✅ Loaded {len(questions)} questions.")

# --- Answer all questions ---
all_results = []

for q in tqdm(questions, desc="🧠 Answering Questions"):
    q_id = q.get("id", "")
    q_text = q.get("question", "")

    if not q_text.strip():
        continue

    # Step 1: Retrieve context
    context = retrieve_context(q_text)

    # Step 2: If context found, ask LLM
    if context.strip() and "❌" not in context:
        answer = ask_llm(q_text, context)
        status = "Found"
    else:
        answer = "No answer found based on the provided documents."
        status = "Not Found"

    all_results.append({
        "ID": q_id,
        "Question": q_text,
        "Answer": answer,
        "Status": status
    })

# --- Save Results to CSV ---
df = pd.DataFrame(all_results)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)

print(f"✅ All answers saved to {OUTPUT_PATH}")
print("🏁 Auto-answering complete!")
