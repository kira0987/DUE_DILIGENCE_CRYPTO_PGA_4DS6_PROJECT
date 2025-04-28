<<<<<<< HEAD
# scripts/auto_answer_150_questions.py

=======
# --- Imports ---
>>>>>>> 3ebb5fcb8b9d258d2a7345b2579742fe51918cf1
import os
import json
import pandas as pd
from tqdm import tqdm

<<<<<<< HEAD
# Correct imports
from scripts.graph_rag_retriever import retrieve_context
from scripts.llm_responder import ask_llm
=======
from scripts.graph_rag_retriever import retrieve_context
from scripts.llm_responder import ask_llm, evaluate_answer, check_faithfulness, detect_and_structure_gaps
>>>>>>> 3ebb5fcb8b9d258d2a7345b2579742fe51918cf1

# --- Paths ---
QUESTION_BANK_PATH = "data/question_bank.json"   # Your custom question list
OUTPUT_PATH = "data/auto_answered_questions.csv"
<<<<<<< HEAD
=======
GAPS_OUTPUT_PATH = "data/missing_gaps_to_scrape.json"
>>>>>>> 3ebb5fcb8b9d258d2a7345b2579742fe51918cf1

# --- Load Question Bank ---
print("🔄 Loading question bank...")
with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
    questions = json.load(f)

print(f"✅ Loaded {len(questions)} questions.")

# --- Answer all questions ---
all_results = []
<<<<<<< HEAD
=======
all_gaps = {}
>>>>>>> 3ebb5fcb8b9d258d2a7345b2579742fe51918cf1

for q in tqdm(questions, desc="🧠 Answering Questions"):
    q_id = q.get("id", "")
    q_text = q.get("question", "")

    if not q_text.strip():
        continue

    # Step 1: Retrieve context
    context = retrieve_context(q_text)

    # Step 2: If context found, ask LLM
<<<<<<< HEAD
    if context.strip() and "❌" not in context:
        answer = ask_llm(q_text, context)
        status = "Found"
    else:
        answer = "No answer found based on the provided documents."
=======
    if context and context.strip() and "❌" not in context:
        answer = ask_llm(q_text, context)
        status = "Found"

        # Step 3: Evaluate the answer
        evaluation_result = evaluate_answer(q_text, context, answer)
        
        # Parse evaluation result safely
        try:
            eval_json = json.loads(evaluation_result)
        except Exception as e:
            eval_json = {"Relevance": 0, "Completeness": 0, "Clarity": 0, "Missing_Points": []}

        # Step 4: Check faithfulness
        faithfulness_result = check_faithfulness(q_text, context, answer)

        # Step 5: Detect and structure gaps
        missing_points = eval_json.get("Missing_Points", [])
        if missing_points:
            gaps = detect_and_structure_gaps(q_text, context, answer, missing_points)
            all_gaps[q_id] = gaps
        else:
            all_gaps[q_id] = {"Status": "✅ No missing points detected."}

    else:
        answer = "No answer found based on the provided documents."
        eval_json = {"Relevance": 0, "Completeness": 0, "Clarity": 0, "Missing_Points": []}
        faithfulness_result = "❌ No context"
        gaps = {"Status": "❌ No context to analyze gaps."}
>>>>>>> 3ebb5fcb8b9d258d2a7345b2579742fe51918cf1
        status = "Not Found"

    all_results.append({
        "ID": q_id,
        "Question": q_text,
        "Answer": answer,
<<<<<<< HEAD
        "Status": status
=======
        "Status": status,
        "Relevance": eval_json.get("Relevance", 0),
        "Completeness": eval_json.get("Completeness", 0),
        "Clarity": eval_json.get("Clarity", 0),
        "Faithfulness": faithfulness_result
>>>>>>> 3ebb5fcb8b9d258d2a7345b2579742fe51918cf1
    })

# --- Save Results to CSV ---
df = pd.DataFrame(all_results)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)

<<<<<<< HEAD
print(f"✅ All answers saved to {OUTPUT_PATH}")
=======
# --- Save Missing Gaps for Scraping ---
os.makedirs(os.path.dirname(GAPS_OUTPUT_PATH), exist_ok=True)
with open(GAPS_OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(all_gaps, f, indent=2, ensure_ascii=False)

print(f"✅ All answers and evaluations saved to {OUTPUT_PATH}")
print(f"✅ Missing gaps saved to {GAPS_OUTPUT_PATH}")
>>>>>>> 3ebb5fcb8b9d258d2a7345b2579742fe51918cf1
print("🏁 Auto-answering complete!")
