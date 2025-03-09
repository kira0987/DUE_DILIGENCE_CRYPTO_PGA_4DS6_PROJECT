import spacy
import pyap  # Extracts addresses
import phonenumbers  # Extracts phone numbers
from thefuzz import fuzz  # Fuzzy matching for company names
import regex  # Advanced regex handling for legal text
from email_validator import validate_email, EmailNotValidError  # Validates and extracts emails
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # Sentiment Analysis

# Load NLP Model
nlp = spacy.load("en_core_web_lg")
sentiment_analyzer = SentimentIntensityAnalyzer()  # Load Sentiment Model

# Define financial, regulatory, and risk terms
FINANCIAL_TERMS = {
    "revenue", "profit", "investment", "liability", "assets", "funding", "debt", "equity", "IPO", "derivative"
}
REGULATIONS = {
    "SEC", "AML", "KYC", "FATCA", "OFAC", "FINCEN", "GDPR", "SOX", "Basel III", "MiFID", "MiCA"
}
CRYPTO_TERMS = {
    "Bitcoin", "Ethereum", "Solana", "Chainlink", "Binance", "Tether", "DeFi", "NFT", "DAO", "staking", "hashrate"
}
RISK_TERMS = {"fraud", "scam", "money laundering", "ponzi", "hacked", "insider trading", "lawsuit"}

def extract_emails(text):
    """Extracts valid email addresses using email-validator."""
    words = text.split()
    emails = []
    for word in words:
        try:
            email = validate_email(word, check_deliverability=False).email
            emails.append(email)
        except EmailNotValidError:
            continue
    return list(set(emails))  # Remove duplicates

def extract_phone_numbers(text, region="US"):
    """Extracts phone numbers using Google's phonenumbers library."""
    numbers = []
    for match in phonenumbers.PhoneNumberMatcher(text, region):
        formatted_number = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        numbers.append(formatted_number)
    return list(set(numbers))

def extract_websites(text):
    """Extracts valid website URLs, including 'www.' without 'http'."""
    WEBSITE_REGEX = r"(https?://[^\s]+|www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    found_urls = regex.findall(WEBSITE_REGEX, text)
    return list(set(found_urls))  # Remove duplicates

def extract_addresses(text):
    """Extracts physical addresses using pyap (supports US-based addresses)."""
    addresses = pyap.parse(text, country="US")
    return [str(address) for address in addresses]

def extract_cik_numbers(text):
    """Extracts SEC CIK Numbers (unique identifier for publicly traded companies)."""
    return regex.findall(r"CIK\s*(\d{10})", text)

def extract_company_names(text):
    """Extracts company names using spaCy NLP model."""
    doc = nlp(text)
    return list(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))

def extract_person_names(text):
    """Extracts names of people from the document (CEOs, executives, legal figures)."""
    doc = nlp(text)
    return list(set(ent.text for ent in doc.ents if ent.label_ == "PERSON"))

def extract_financial_terms(text):
    """Identifies financial keywords, regulations, and risk-related mentions."""
    found_terms = [term for term in FINANCIAL_TERMS if term.lower() in text.lower()]
    found_regs = [reg for reg in REGULATIONS if reg in text]
    found_crypto = [crypto for crypto in CRYPTO_TERMS if crypto in text]
    found_risks = [risk for risk in RISK_TERMS if risk in text]

    return {
        "financial_terms": found_terms,
        "regulations": found_regs,
        "crypto_terms": found_crypto,
        "risk_mentions": found_risks,
    }

def calculate_risk_score(found_risks):
    """Assigns a risk score based on risk-related keywords found (scale of 0-10)."""
    return min(10, len(found_risks) * 2)  # Each mention increases score by 2 (max 10)

def analyze_sentiment(text):
    """Analyzes sentiment of extracted text to assess risk perception."""
    sentiment_scores = sentiment_analyzer.polarity_scores(text)
    sentiment_label = "neutral"
    if sentiment_scores["compound"] >= 0.05:
        sentiment_label = "positive"
    elif sentiment_scores["compound"] <= -0.05:
        sentiment_label = "negative"
    
    return {
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_scores["compound"]  # Value between -1 (neg) to +1 (pos)
    }

def extract_entities(text):
    """Extracts structured data from text for crypto due diligence analysis."""
    extracted_data = {
        "company_names": extract_company_names(text),
        "person_names": extract_person_names(text),
        "emails": extract_emails(text),
        "phone_numbers": extract_phone_numbers(text),
        "websites": extract_websites(text),
        "addresses": extract_addresses(text),
        "cik_numbers": extract_cik_numbers(text),
    }

    financial_analysis = extract_financial_terms(text)
    extracted_data.update(financial_analysis)

    # Compute risk score
    extracted_data["risk_score"] = calculate_risk_score(financial_analysis["risk_mentions"])

    # Add Sentiment Analysis
    sentiment_data = analyze_sentiment(text)
    extracted_data.update(sentiment_data)

    return extracted_data

