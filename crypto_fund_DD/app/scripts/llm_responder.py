import ollama
import time

# --- Settings ---
LLM_MODEL = "llama3.1"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Standard ask_llm (for Q&A) ---
def ask_llm(question, context):
    if not context.strip():
        return "⚠️ No context available to generate an answer."

    if len(context.strip()) < 50:
        return "⚠️ Context too small to generate an answer."

    system_prompt = f"""
You are a Due Diligence Expert specialized in Crypto Funds.
Answer the question strictly based on the context provided.

Context:
{context}

Question:
{question}

Answer professionally:
"""
    prompt = system_prompt.strip()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional crypto fund due diligence assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['message']['content'].strip()
        except Exception as e:
            time.sleep(RETRY_DELAY)

    return "❌ Failed to get a response from the LLM."

# --- ask_llm_raw (direct prompt) ---
def ask_llm_raw(prompt):
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content'].strip()
    except Exception as e:
        return f"❌ LLM Error: {e}"

# --- Evaluate Answer Function (Detailed) ---
def evaluate_answer(question, context, answer):
    evaluation_prompt = f"""
You are an expert evaluator.
Evaluate the following answer based strictly on the provided context.

Question: {question}

Context: {context}

Answer: {answer}

Respond ONLY in valid JSON format like this, with NO explanations, NO comments:

{{
  "Relevance": 0-10,
  "Completeness": 0-10,
  "Clarity": 0-10,
  "Missing_Points": ["...list of important missing points..."]
}}
"""
    return ask_llm_raw(evaluation_prompt)

# --- Faithfulness Check (no hallucination) ---
def check_faithfulness(question, context, answer):
    faithfulness_prompt = f"""
You are a critical evaluator.
Determine if the following answer stays faithful to the provided context.

Context:
{context}

Question:
{question}

Answer:
{answer}

If the answer uses ONLY information from the context, reply "✅ Faithful".
If it invents or hallucinates, reply "⚠️ Hallucination detected" with a short reason.
"""
    return ask_llm_raw(faithfulness_prompt)

# --- Classify Question ---
def classify_question(question):
    prompt = f"""
You are an expert question classifier.

Classify the following question into one of the four categories:
"Factual"
"Investigative"
"Opinion"
"Missing Context"


Only reply with one word: Factual, Investigative, Opinion, or Missing Context.

Question:
{question}
"""
    return ask_llm_raw(prompt).strip()

# --- NEW: Detect and Structure Gaps ---
def detect_and_structure_gaps(question, context, answer, missing_points):
    """Detect missing information and create structured scraping tasks."""
    if not missing_points:
        return {"Status": "✅ No missing points detected."}

    structured_prompt = f"""
You are a Due Diligence Gap Analyst.
Your job is to transform the missing points into clear, actionable data acquisition tasks.

For each missing point, generate:
Data_Needed: A clear description of the missing information.
Suggested_Search_Query: What to type in Google or Bing to find it.
Best_Sources: Best websites, databases, or public sources to find this information.
Scraper_Instruction: Precise instructions a scraper should follow to retrieve this data.
Importance_Level: High, Medium, or Low (based on how critical it is).


Missing Points:
{missing_points}

Context:
{context}

Question:
{question}

Respond ONLY in valid JSON list format, like this:

[
  {{
    "Data_Needed": "...",
    "Suggested_Search_Query": "...",
    "Best_Sources": ["site1.com", "site2.org"],
    "Scraper_Instruction": "...",
    "Importance_Level": "High"
  }},
  ...
]
"""
    return ask_llm_raw(structured_prompt)
