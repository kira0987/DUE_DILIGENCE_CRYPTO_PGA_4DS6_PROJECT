import ollama
import time
import json
import re
from scripts.evaluate_investor_risk import evaluate_investor_risk

# --- Config ---
LLM_MODEL = "llama3.1"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Retry Wrapper ---P
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
    
# --- Entity Detector ---
def detect_entity_name(question, context):
    candidates = []
    patterns = [
        r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\sFund)",
        r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\sCapital)",
        r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\sPartners)",
        r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\sInvestments?)"
    ]
    for pattern in patterns:
        matches = re.findall(pattern, context)
        candidates.extend(matches)
    if not candidates:
        for pattern in patterns:
            matches = re.findall(pattern, question)
            candidates.extend(matches)
    if candidates:
        return candidates[0]
    return "Unknown Entity"

# --- ask_llm: Ultra professional structured due diligence answer ---
def ask_llm(question, context):
    if not context.strip():
        return "⚠️ No context available to generate an answer."
    if len(context.strip()) < 50:
        return "⚠️ Context too small to generate an answer."

    system_prompt = f"""
You are a Senior Crypto Fund Due Diligence Analyst specializing in audit-grade reports.

🔵 TASK:
Analyze the Question and Context provided. Generate a strictly professional structured answer.

🎯 REQUIRED STRUCTURE:

✅ Direct Answer:
- Provide a short, direct answer based ONLY on the provided context.
- If missing, explicitly state: "❌ No direct answer found in provided context."

📌 Extracted Facts:
- Bullet points of verifiable facts directly from the context.
- Whenever possible, mention where the fact comes from (e.g., "as stated in the Risk Management section").
- If no facts found, explicitly state: "❌ No verifiable facts found."

⚖️ Compliance Status:
- If licenses, registrations, compliance frameworks are mentioned, summarize them.
- If none found, explicitly state: "❌ No compliance information available."

⚠️ Missing Information Detected:
- Identify major missing pieces critical for due diligence (e.g., missing AML policies, audited financials, registration details).
- If context seems complete, write: "✅ No critical information missing."

📝 Conclusion:
- If information is sufficient:  
  "Based on the provided context, the information is sufficient to professionally answer the question."
- If insufficient:  
  "The document does not provide enough information to fully assess this topic based on the provided context."

🚨 STRICT RULES:
- ❌ No assumptions or speculation.
- ❌ No hallucination.
- ✔️ Stick 100% to context.
- ✔️ Professional audit-grade style.

Context:
{context}

Question:
{question}
"""
    messages = [
        {"role": "system", "content": "You are an AI specialized in Crypto Fund Due Diligence reports."},
        {"role": "user", "content": system_prompt.strip()}
    ]
    return retry_llm(messages)

# --- ask_llm_raw: Simple freeform prompting ---
def ask_llm_raw(prompt):
    messages = [{"role": "user", "content": prompt}]
    return retry_llm(messages)
# --- Investor Risk Impact Evaluator ---
def evaluate_investor_risk(answer: str) -> str:
    """
    Use LLM to classify the investor risk level of this answer.
    Possible values: Positive, Partial, Negative, or Missing.
    """
    from scripts.llm_utils import call_llm_strict  # Replace with your LLM calling method

    prompt = f"""
You are a professional investment analyst conducting due diligence on a crypto fund.
Your job is to classify the following answer based on its risk implications for an investor.

Evaluate the answer and return one of:
- Positive: The answer demonstrates strong investor protection, transparency, or compliance.
- Partial: The answer provides some relevant points, but lacks completeness or clarity.
- Negative: The answer reveals risk, lack of safeguards, or troubling signals.
- Missing: The answer is irrelevant, empty, or does not address the question.

Use professional judgment and return ONLY the classification word.

Answer:
\"\"\"{answer}\"\"\"
    """

    return call_llm_strict(prompt).strip()


# --- detect_and_structure_gaps: Ultra professional dynamic gap generation ---
def detect_and_structure_gaps(question, context, answer):
    entity_name = detect_entity_name(question, context)

    required_keywords = {
        "AML policies and procedures": ["aml", "anti-money laundering"],
        "Fund Registration / Legal Status": ["registration", "incorporated", "entity", "license", "jurisdiction"],
        "KYC Compliance": ["kyc", "know your customer"],
        "Audited Financials": ["audit", "audited financials", "financial report"],
        "Custody of Assets": ["custody", "custodian", "assets security"],
        "Fund Governance Structure": ["governance", "board of directors", "general partner", "management team"],
        "Risk Management Framework": ["risk management", "risk policy", "operational risks"],
        "Investor Protection Measures": ["investor protection", "fiduciary duty", "safeguard"],
    }

    missing_fields = []
    context_lower = context.lower()

    for field_name, keywords in required_keywords.items():
        if not any(keyword in context_lower for keyword in keywords):
            missing_fields.append(field_name)

    if not missing_fields:
        return json.dumps([{"Status": "✅ No missing information detected."}], indent=2)

    structured_tasks = []
    for missing in missing_fields:
        dynamic_info = generate_dynamic_gap_info(missing, entity_name, context, answer)

        task = {
            "Entity_Concerned": entity_name,
            "Risk_Domain": detect_risk_domain(missing),
            "Data_Needed": missing,
            "Suggested_Search_Query": dynamic_info.get("Suggested_Search_Query", f"{entity_name} {missing}"),
            "Best_Sources": dynamic_info.get("Best_Sources", ["official website", "regulatory filings"]),
            "Scraper_Instruction": dynamic_info.get("Scraper_Instruction", f"Search for '{missing}' in trusted financial portals."),
            "Importance_Level": "High"
        }
        structured_tasks.append(task)

    return json.dumps(structured_tasks, indent=2, ensure_ascii=False)

# --- Dynamic LLM generation for search hints ---
def generate_dynamic_gap_info(missing_data, entity_name, context, answer):
    prompt = f"""
You are a Senior Due Diligence Analyst.

🔵 TASK:
For the missing data point "{missing_data}" regarding entity "{entity_name}",
generate the following:

- A realistic Google search query.
- 2-3 best sources (official site, regulators, trusted crypto news).
- Clear scraper instruction.

Context:
{context}

Answer:
{answer}

Format your reply strictly in JSON:
{{
  "Suggested_Search_Query": "...",
  "Best_Sources": ["...", "..."],
  "Scraper_Instruction": "..."
}}

No extra text. No explanations.
"""
    try:
        raw = ask_llm_raw(prompt)
        data = json.loads(raw)
        return data
    except Exception as e:
        print(f"⚠️ Dynamic gap info generation failed: {e}")
        return {}

# --- Risk Domain Mapper ---
def detect_risk_domain(missing_field):
    if "AML" in missing_field or "KYC" in missing_field:
        return "Compliance"
    if "Registration" in missing_field or "Legal" in missing_field:
        return "Legal"
    if "Custody" in missing_field or "Assets" in missing_field:
        return "Technical Infrastructure"
    if "Governance" in missing_field:
        return "Governance"
    if "Risk Management" in missing_field:
        return "Risk Management"
    if "Investor Protection" in missing_field:
        return "Investor Protection"
    if "Audited Financials" in missing_field:
        return "Financial Health"
    return "General"

def apply_feedback_to_answer(feedback_type, question, answer):
    VALID_FEEDBACK = ["Reformulate this", "Make it more concise", "Add regulatory context"]

    if feedback_type not in VALID_FEEDBACK:
        return "⚠️ Invalid feedback type."

    if feedback_type == "Reformulate this":
        instruction = "Please reformulate the following answer to make it clearer."
    elif feedback_type == "Make it more concise":
        instruction = "Please rewrite the answer in a more concise form while preserving the key message."
    elif feedback_type == "Add regulatory context":
        instruction = "Please add relevant regulatory context to the answer if possible."

    prompt = f"{instruction}\n\nQuestion: {question}\n\nAnswer: {answer}"

    messages = [
        {"role": "system", "content": "You are a professional Crypto Fund Due Diligence Analyst."},
        {"role": "user", "content": prompt}
    ]
    return retry_llm(messages)
def platform_assistant_answer(question: str) -> str:
    """
    Specialized Assistant that ONLY answers questions about the DueXpert Platform: who we are, features, services, and values.
    No general answers allowed. Professional and friendly tone.
    """
    system_prompt = """
You are an AI Support Assistant for the platform "DueXpert".

🎯 YOUR SCOPE:
- You ONLY answer questions related to DueXpert (company overview, features, services, risk scoring, document upload, pricing, benefits, values).
- If the user's question is outside of this scope (e.g., unrelated topics like sports, politics, general crypto advice), politely respond: "I'm sorry, I can only assist with questions about the DueXpert platform."

🎯 TONE AND STYLE:
- Maintain a professional, courteous, and helpful tone.
- Keep answers clear, informative, and concise — avoid overly long paragraphs.
- Naturally mention "DueXpert" by name where appropriate.
- NEVER hallucinate information — if the answer is not known, politely refuse.

🧠 EXAMPLES OF GOOD ANSWERS:
- "DueXpert is a specialized platform focused on crypto fund due diligence and investment risk analysis."
- "With DueXpert, users can upload documents, perform automated risk scoring, and generate executive-ready reports."
- "I'm sorry, I can only answer questions related to the DueXpert platform."

✅ ALWAYS double-check that your answer fits strictly within the DueXpert platform context before replying.
    """

    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": question}
    ]
    return retry_llm(messages)

def platform_assistant_safe_answer(question: str) -> str:
    """
    Safely answer user input: if the question is empty, respond nicely; otherwise, call platform_assistant_answer().
    """
    if not question.strip():
        return "❓ Please type a question related to the DueXpert platform so I can assist you!"
    return platform_assistant_answer(question)
def followup_assistant(original_question: str, original_answer: str, followup_message: str) -> str:
    """
    Handle follow-up interactions strictly related to a specific original question and answer.
    If the follow-up is off-topic, politely guide the user back.
    """
    system_prompt = f"""
You are a Senior Due Diligence Assistant specializing in providing professional follow-up support.

🎯 CONTEXT:
- Original Question: {original_question}
- Original Answer: {original_answer}

🔒 RULES:
- ONLY provide clarifications, expansions, reformulations, format improvements, or more detailed explanations about the above Q&A.
- If the user's message is unrelated (e.g., asking about another topic), politely respond:
  "I'm here to assist you specifically regarding the above question and answer. Kindly keep your inquiry related to them."

🧠 STYLE REQUIREMENTS:
- Professional yet approachable.
- Responses must be clear, structured, and concise.
- Never fabricate new facts not already present or reasonably inferred from the original Q&A.
- Uphold the credibility and audit-grade quality of DueXpert.

✅ KEY PRINCIPLES:
- Stay fully anchored to the original Q&A.
- Avoid general opinions or unrelated suggestions.
- Enhance user understanding while maintaining accuracy.

Always carefully analyze the follow-up in the context of the original Q&A before replying.
    """

    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": followup_message}
    ]

    return retry_llm(messages)
def detect_commitments(extracted_folder: str):
    """
    Improved professional version.
    Scans all extracted text files and detects commitments, promises, pledges, and guarantees.
    Returns a list of detected commitment sentences.
    """

    commitments = []

    # --- Define stronger patterns ---
    keywords = [
        "promise", "commit", "pledge", "guarantee", "undertake", "ensure", "dedicated to", 
        "strive to", "we will", "we are committed to", "we pledge to", "we guarantee", 
        "we aim to", "our mission is to", "our goal is to", "we ensure", "we undertake", 
        "we are dedicated to", "we strive to", "committed to", "we target to"
    ]

    # Build a large regex (case insensitive)
    keyword_pattern = re.compile(r'(' + '|'.join(re.escape(k) for k in keywords) + r')', re.IGNORECASE)

    # --- Scan all extracted text files ---
    for file in os.listdir(extracted_folder):
        if file.endswith("_cleaned.txt"):
            with open(os.path.join(extracted_folder, file), "r", encoding="utf-8") as f:
                text = f.read()

                # Split into sentences smartly
                sentences = re.split(r'(?<=[.!?])\s+', text)

                for sentence in sentences:
                    if len(sentence.strip()) < 10:
                        continue  # Skip very small sentences

                    if keyword_pattern.search(sentence):
                        commitments.append({
                            "source_file": file,
                            "commitment_sentence": sentence.strip()
                        })

    return commitments

def detect_commitments_in_text(text: str, source_file: str = "unknown") -> list:
    """
    Detects commitments, promises, guarantees from a given text.
    Returns a list of dictionaries: {"source_file": ..., "commitment_sentence": ...}
    """

    if not text.strip():
        return []

    system_prompt = """
You are a professional due diligence analyst specialized in crypto investment funds.

Your task is:
- Carefully read the provided fund documentation text.
- Extract ONLY the sentences that contain a **promise**, **commitment**, **pledge**, or **guarantee**.
- Return each promise as a SEPARATE short sentence (no explanations, no reformulations).
- Focus only on real commitments made by the fund (e.g., "we commit to...", "we guarantee...", "we promise...", "we pledge...").

Format your output as a JSON list like:
[
  {"commitment_sentence": "..."},
  {"commitment_sentence": "..."}
]
ONLY output this JSON list and nothing else.
If you find no commitment sentences, output [].
""".strip()

    user_prompt = f"""
Here is the fund text to analyze:
{text}
""".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        from scripts.llm_responder import retry_llm  # your existing function
        response_text = retry_llm(messages)
        extracted = json.loads(response_text)

        if isinstance(extracted, list):
            return [{"source_file": source_file, "commitment_sentence": item.get("commitment_sentence", "")} for item in extracted]
        else:
            return []
    except Exception as e:
        print(f"Error extracting commitments: {e}")
        return []
    # --- Evaluate Answer Quality (Completeness, Accuracy, Clarity) 

import json
import re
from scripts.llm_responder import ask_llm_raw  # Make sure you import correctly

# --- Evaluate Answer Quality (Completeness, Accuracy, Clarity)
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


    # --- Faithfulness Checker
# scripts/llm_responder.py

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

# --- Load Embedding Model (do it only once)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, fast, good accuracy

def check_faithfulness(context, answer, similarity_threshold=0.7):
    """
    Checks if the answer is faithful to the provided context by embedding both and comparing cosine similarity.
    Args:
        context (str): The original extracted document content.
        answer (str): The generated LLM answer.
        similarity_threshold (float): Threshold above which the answer is considered faithful.
    Returns:
        dict: { 'status': 'Faithful' or 'Not Faithful', 'similarity': float, 'explanation': str }
    """

    if not context.strip() or not answer.strip():
        return {
            'status': 'Not Faithful',
            'similarity': 0.0,
            'explanation': "❌ No sufficient context or answer provided."
        }

    # Compute embeddings
    context_embedding = embedding_model.encode([context], normalize_embeddings=True)
    answer_embedding = embedding_model.encode([answer], normalize_embeddings=True)

    # Compute cosine similarity
    similarity_score = cosine_similarity(context_embedding, answer_embedding)[0][0]

    # Decide based on threshold
    if similarity_score >= similarity_threshold:
        return {
            'status': 'Faithful',
            'similarity': similarity_score,
            'explanation': f"✅ This answer is faithful. It matches the document context with high similarity ({similarity_score:.2f})."
        }
    else:
        return {
            'status': 'Not Faithful',
            'similarity': similarity_score,
            'explanation': f"❌ This answer is not faithful enough. Similarity is only ({similarity_score:.2f}). Likely generated by LLM without enough support."
        }
