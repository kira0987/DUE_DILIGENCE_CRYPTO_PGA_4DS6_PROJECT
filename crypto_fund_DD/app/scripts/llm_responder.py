import ollama
import time
import json

# --- Config ---
LLM_MODEL = "llama3.1:latest"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Retry Wrapper ---
def retry_llm(messages, model=LLM_MODEL):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = ollama.chat(
                model=model,
                messages=messages
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Retry {attempt} failed: {e}")
            time.sleep(RETRY_DELAY)
    return "❌ Failed to get a response from the local LLaMA model."


# --- 1. ask_llm: Structured, professional due diligence answer ---
def ask_llm(question, context):
    if not context.strip():
        return "⚠️ No context available to generate an answer."
    if len(context.strip()) < 50:
        return "⚠️ Context too small to generate an answer."

    system_prompt = f"""
You are a Senior Due Diligence Analyst specializing in Crypto Investment Funds.

Your answer must be audit-ready and will be reviewed by legal, compliance, and investment professionals. You must deeply and accurately understand the question and context provided.

OBJECTIVE:
- Provide factual, clear, and professionally structured answers.
- Explicitly identify any missing information required to fully answer the question.
- Conclude with a concise professional summary, strictly based on provided information.

FOCUS AREAS (Always consider these closely):
- Fund legal entity (LLC, corporation, etc.)
- Licensing, registration details, jurisdictions
- Compliance with securities, commodities, financial regulations
- Stakeholders: fund owners, managing partners, advisors
- Governance structure and conflict-of-interest policies
- Risk factors: legal, financial, operational, compliance
- Fund strategies, digital assets management, liquidation mechanisms
- Transparency, public disclosures, regulatory reporting

STRICT RULES (stick to the context):
- DO NOT hallucinate or invent details not explicitly stated.
- DO NOT provide hypothetical scenarios, possible risks, or recommendations unless explicitly stated.
- DO NOT infer governance or compliance structures if they're not described directly in the context.
- DO NOT make assumptions or inferences from vague wording.
- DO NOT use speculative language such as "likely", "possibly", "might be".
- DO NOT provide general recommendations or advice unless explicitly stated in the context.
- DO NOT rely on any prior or external knowledge.

REQUIRED ANSWER STRUCTURE:

1. ✅ Direct Answer:
   Clearly, concisely, and explicitly answer the question using ONLY context information.
   - Clearly identify missing information rather than guessing or speculating

2. 📌 Extracted Facts:
   Bullet points of explicitly verifiable facts quoted or paraphrased directly from the provided context that support your direct answer.

3. ⚖️ Compliance Status (Only if explicitly stated):
   Clearly cite explicit mentions of compliance or non-compliance from the context (licenses, regulatory adherence, filings).

4. ⚠️ Missing Information Detected:
   You MUST always include this section.

   - If critical information is missing to fully answer the question, list each missing data point clearly (e.g., legal entity type, licenses, governance policies, registration details, etc.).
   - If no information is missing, write: "✅ No critical information missing from the provided context."

5. 📝 Conclusion:
   Provide a concise summary strictly based on the provided context. Clearly indicate if the available information is sufficient or insufficient to fully address the question for professional due diligence.

---
Now, carefully analyze and answer the question below using ONLY the provided context.

Context:
{context}

Question:
{question}
"""

    messages = [
        {"role": "system", "content": (
            "You are a highly experienced Crypto Fund Due Diligence Analyst. "
            "Your responses must strictly adhere to the provided context, without hallucinations or assumptions."
        )},
        {"role": "user", "content": system_prompt.strip()}
    ]

    return retry_llm(messages)


# --- 2. ask_llm_raw: Simple freeform prompting ---
def ask_llm_raw(prompt):
    messages = [{"role": "user", "content": prompt}]
    return retry_llm(messages)


# --- 3. evaluate_answer: JSON-based scoring ---
def evaluate_answer(question, context, answer):
    evaluation_prompt = f"""
You are a senior evaluator of crypto due diligence responses.

Evaluate the following answer based ONLY on the context.

Scoring Criteria:
- "Relevance": 0–10
- "Completeness": 0–10
- "Clarity": 0–10
- "Missing_Points": list of important facts missing in the answer

Context:
{context}

Question:
{question}

Answer:
{answer}

Respond ONLY in valid JSON like this:
{{
  "Relevance": 8,
  "Completeness": 9,
  "Clarity": 10,
  "Missing_Points": ["Missing registration number", "Missing tax status"]
}}

NO extra explanation or text.
"""
    result = ask_llm_raw(evaluation_prompt)

    try:
        return json.loads(result)
    except Exception:
        return {
            "Relevance": 0,
            "Completeness": 0,
            "Clarity": 0,
            "Missing_Points": ["❌ Failed to parse evaluation JSON."]
        }


# --- 4. check_faithfulness: Detect hallucinations ---
def check_faithfulness(question, context, answer):
    prompt = f"""
You are a strict due diligence evaluator for a crypto investment fund analysis system.

TASK:
Check whether the answer below is fully faithful to the provided context.

Definitions:
- Faithful = Every fact stated is directly supported by the context.
- Hallucinated = A claim is introduced that cannot be verified from the context.

BUT — we also care about *impact*:
- Harmless = The hallucination is minor, does not change the meaning, or is a reasonable framing of what's already there.
- Harmful = The hallucination adds legal, compliance, or operational claims not supported by the text.

Evaluate as follows:

1. ✅ Faithfulness: "Faithful" / "Hallucination Detected"
2. 🔍 Hallucinated Content: List the exact unsupported parts (if any)
3. 🛡️ Impact Assessment: "Harmless" or "Harmful" — explain briefly why

Now analyze:

Context:
{context}

Question:
{question}

Answer:
{answer}
"""
    return ask_llm_raw(prompt)


# --- 5. classify_question: Identify question type ---
def classify_question(question):
    prompt = f"""
You are a professional classifier.

Classify the following question into ONE of these 4 types:
- "Factual"
- "Investigative"
- "Opinion"
- "Missing Context"

Only reply with the type.

Question:
{question}
"""
    return ask_llm_raw(prompt).strip()


# --- 6. detect_and_structure_gaps: Structured scraping tasks ---
def detect_and_structure_gaps(question, context, answer, missing_points):
    if not missing_points or not isinstance(missing_points, list) or all(mp.strip() == "" for mp in missing_points):
        return json.dumps({"Status": "✅ No missing points detected."})

    structured_prompt = f"""
You are a Due Diligence Gap Analyst.

TASK:
For each missing point, create a structured research task.

Provide:
- "Data_Needed"
- "Suggested_Search_Query"
- "Best_Sources": top 2–3 reliable public websites
- "Scraper_Instruction"
- "Importance_Level": High / Medium / Low

Context:
{context}

Question:
{question}

Answer:
{answer}

Missing Points:
{json.dumps(missing_points)}

Respond ONLY in JSON array format like this:
[
  {{
    "Data_Needed": "...",
    "Suggested_Search_Query": "...",
    "Best_Sources": ["site1.com", "site2.org"],
    "Scraper_Instruction": "...",
    "Importance_Level": "High"
  }}
]
"""
    raw = ask_llm_raw(structured_prompt)

    # Always return the raw string so that the Streamlit side can extract safely
    return raw if isinstance(raw, str) else json.dumps({"error": "❌ LLM did not return a string response."})