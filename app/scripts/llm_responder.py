import ollama
import time
import json
import re
from scripts.evaluate_investor_risk import evaluate_investor_risk

# --- Config ---
LLM_MODEL = "llama3.1"
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
def evaluate_investor_impact(answer: str) -> str:
    """
    Evaluate if the answer is Positive / Negative / Partial / Missing from an investor's risk perspective.
    """
    return evaluate_investor_risk(answer)

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

# --- New Refine Answer for 3 Buttons ---
def refine_answer(action_type, original_answer, context):
    """
    Refines the answer based on the selected button action (Reformulate, Concise, Regulatory Context).
    """
    if action_type == "reformulate":
        prompt = f"""
You are a Senior Due Diligence Analyst.

🔵 TASK: Reformulate this answer to make it more professional, polished, and clear — without changing the meaning.

Context:
{context}

Answer:
{original_answer}

✅ Only output the reformulated answer. No explanations.
"""
    elif action_type == "concise":
        prompt = f"""
You are a Senior Due Diligence Analyst.

🔵 TASK: Rewrite this due diligence answer to be more concise, clear, and direct for executive-level understanding — without losing important information.

Context:
{context}

Answer:
{original_answer}

✅ Only output the concise version. No explanations.
"""
    elif action_type == "regulatory":
        prompt = f"""
You are a Senior Due Diligence Analyst.

🔵 TASK: Enrich this answer by referencing real-world compliance and regulatory frameworks (e.g., SEC, MiCA, FINMA, FCA) where appropriate.

Context:
{context}

Answer:
{original_answer}

✅ Only output the regulatory-enriched answer. No explanations.
"""
    else:
        return "❌ Invalid refinement type."

    return ask_llm_raw(prompt)
