import json
import requests
from functools import lru_cache
from typing import Dict, Optional

GROQ_API_KEY = "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"
MODEL = "llama3-70b-8192"

@lru_cache(maxsize=100)
def llama_chat(prompt: str, temperature: float = 0.7) -> str:
    """Robust LLM query function with proper error handling"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "temperature": min(max(temperature, 0.1), 1.0),  # Ensure valid range
        "max_tokens": 4000  # Adjust based on your needs
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60  # Increased timeout
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        if not data.get("choices"):
            return "⚠️ Error: No response generated"
            
        return data["choices"][0]["message"]["content"].strip()
        
    except requests.exceptions.HTTPError as http_err:
        return f"⚠️ HTTP Error: {http_err.response.status_code} - {http_err.response.text}"
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def generate_concise_prompt(question: str, context: str, metadata: Dict) -> str:
    """Generate optimized prompt with metadata"""
    return f"""
    [Document: {metadata.get('source', 'Unknown')} | Risk: {metadata.get('risk_score', 'N/A')}]
    Context: {context[:1500]}
    Question: {question}
    Answer concisely and factually:
    """

def evaluate_answer(question: str, answer: str) -> dict:
    """
    Uses LLM to evaluate the quality of an answer.
    Returns:
        dict: {
            "accuracy": int (1-5),
            "completeness": int (1-5),
            "tags": list[str],
            "suggestion": str
        }
    """
    prompt = f"""
    Evaluate this Q&A pair for crypto fund due diligence:

    Question: {question}
    Answer: {answer}

    Provide:
    1. Accuracy score (1-5, where 5=factually perfect)
    2. Completeness score (1-5, where 5=fully addressed)
    3. List of tags (e.g., "hallucination", "incomplete", "needs_sources")
    4. One-sentence improvement suggestion.

    Return as JSON only:
    {{
        "accuracy": int,
        "completeness": int,
        "tags": list[str],
        "suggestion": str
    }}
    """
    
    try:
        response = llama_chat(prompt, temperature=0.1)
        return json.loads(response.strip())
    except Exception as e:
        print(f"Evaluation failed: {str(e)}")
        return {
            "accuracy": 3,
            "completeness": 3,
            "tags": ["evaluation_failed"],
            "suggestion": "Unable to evaluate this response."
        }