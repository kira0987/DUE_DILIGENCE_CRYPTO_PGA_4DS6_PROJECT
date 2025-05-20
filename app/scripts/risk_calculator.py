import spacy
import numpy as np
import pandas as pd
from collections import defaultdict

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Due diligence criteria for analysis
DUE_DILIGENCE_CRITERIA = {
    "AML / KYC": ["AML policies", "KYC procedures", "compliance measures", "regulatory adherence"],
    "Community & UX": ["user engagement", "platform usability", "community transparency", "feedback mechanisms"],
    "Custody & Asset Security": ["asset storage", "multi-signature wallets", "asset ownership verification", "insurance coverage"],
    "Cybersecurity & Data Privacy": ["blockchain technology", "cybersecurity measures", "two-factor authentication", "data protection policy"],
    "ESG & Sustainability": ["sustainability practices", "energy consumption", "environmental impact", "sustainability audits"],
    "Financial Health": ["financial statements", "cash flow projections", "tax disputes", "annual auditing"],
    "Governance": ["board of directors", "conflict of interest policies", "external audits", "succession planning"],
    "IP & Contracts": ["intellectual property assets", "IP infringement", "smart contract audits", "major contracts"],
    "Legal & Regulatory": ["licenses and permits", "international law compliance", "sanctions monitoring", "regulatory filings"],
    "Risk Management": ["risk management strategies", "market volatility", "business continuity plan", "operational resilience"],
    "Strategy & Competitive Positioning": ["market positioning", "competitor analysis", "investment strategies", "growth strategies"],
    "Technology & Infrastructure": ["scalability plans", "security measures", "blockchain technology", "infrastructure upgrades"],
    "Tokenomics & Trading Integrity": ["securities compliance", "trade surveillance", "valuation consistency", "code reviews"],
    "Future Outlook": ["stablecoin compliance", "AI integration", "institutional adoption", "quantum resistance"]
}

# Importance weights for each category
IMPORTANCE_WEIGHTS = {
    "AML / KYC": 1.0,
    "Legal & Regulatory": 1.0,
    "Cybersecurity & Data Privacy": 0.8,
    "Custody & Asset Security": 0.8,
    "Financial Health": 0.64,
    "Governance": 0.48,
    "Risk Management": 0.48,
    "Tokenomics & Trading Integrity": 0.36,
    "Community & UX": 0.24,
    "ESG & Sustainability": 0.16,
    "IP & Contracts": 0.16,
    "Strategy & Competitive Positioning": 0.16,
    "Technology & Infrastructure": 0.24,
    "Future Outlook": 0.08
}

def detect_negative_sentiment(text):
    """Detect negative sentiment in text based on predefined indicators."""
    doc = nlp(text.lower())
    negative_indicators = ["not mentioned", "lacking", "insufficient", "unavailable", "no details", "unknown", "weak", "incomplete"]
    return any(indicator in text.lower() for indicator in negative_indicators)

def analyze_tag_text(tag, findings, issues):
    """Analyze text for a tag to calculate completeness based on criteria."""
    tag_text = " ".join(findings) + " " + " ".join(issues)
    criteria = DUE_DILIGENCE_CRITERIA.get(tag, [])
    doc = nlp(tag_text.lower())
    found_criteria = []
    for criterion in criteria:
        criterion_doc = nlp(criterion.lower())
        similarity = doc.similarity(criterion_doc)
        keyword_match = criterion.lower() in tag_text.lower()
        if similarity >= 0.7 or keyword_match:
            found_criteria.append(criterion)
    found_criteria = list(set(found_criteria))
    completeness = len(found_criteria) / len(criteria) * 100 if criteria else 0
    missing = [c for c in criteria if c not in found_criteria]
    if detect_negative_sentiment(tag_text):
        completeness *= 0.8
    return {
        "completeness": completeness,
        "found": found_criteria,
        "missing": missing
    }

def calculate_question_risk(row, tag, tag_weight):
    """Calculate risk score for a single question based on metrics."""
    metrics = ["relevance", "completeness", "clarity", "faithfulness"]
    metric_scores = [float(row[m]) if pd.notna(row[m]) and np.isfinite(row[m]) else 0.0 for m in metrics]
    avg_metric = np.mean(metric_scores)
    answer_score = 0.5  # Fallback score
    combined_score = (avg_metric + answer_score) / 2
    risk = (1 - combined_score) * tag_weight * 100
    if detect_negative_sentiment(row["answer"]):
        risk *= 1.2
    final_risk = float(min(risk, 100))
    return final_risk

def calculate_risk_score(analysis, df, classified):
    """Calculate tag-level risk scores, incorporating question-level risks."""
    risk_scores = {}
    tag_map = {q["question"]: q["tag"] for q in classified}
    df["tag"] = df["question"].map(tag_map)
    
    for tag in analysis:
        tag_df = df[df["tag"] == tag].copy()
        weight = IMPORTANCE_WEIGHTS.get(tag, 0.5)
        completeness = analysis[tag]["completeness"] / 100
        
        question_risks = []
        for _, row in tag_df.iterrows():
            question_risk = calculate_question_risk(row, tag, weight)
            question_risks.append(question_risk)
        
        tag_risk = (1 - completeness) * weight * 100
        if question_risks:
            avg_question_risk = np.mean(question_risks)
            tag_risk = (tag_risk + avg_question_risk) / 2
        if len(analysis[tag]["missing"]) > len(analysis[tag]["found"]):
            tag_risk *= 1.2
        risk_scores[tag] = min(tag_risk, 100)
    
    return risk_scores