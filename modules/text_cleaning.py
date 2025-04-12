import re
import string
from typing import Union
import unicodedata

def clean_text(text: Union[str, bytes]) -> str:
    """
    Robust text cleaning with multiple normalization steps.
    
    Args:
        text: Input text (string or bytes)
    
    Returns:
        Cleaned and normalized text string
    
    Raises:
        ValueError: If input is not string or bytes
    """
    # Input validation
    if not isinstance(text, (str, bytes)):
        raise ValueError(f"Expected string or bytes, got {type(text)}")
    
    # Convert bytes to string if needed
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')

    # Normalize Unicode (convert special chars to their closest ASCII equivalents)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

    # Remove URLs, emails, phone numbers
    text = re.sub(r"http[s]?://\S+", "", text)  # URLs
    text = re.sub(r"\S+@\S+\.\S+", "", text)    # Emails
    text = re.sub(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "", text)  # Phone numbers

    # Handle crypto-specific patterns
    text = re.sub(r"0x[a-fA-F0-9]{40}", "", text)  # Crypto addresses
    text = re.sub(r"\b[A-Z]{3,10}\b", "", text)    # All-caps tokens (like BTC, ETH)

    # Normalize whitespace (preserve paragraph breaks)
    text = re.sub(r"(?<!\n)\s+", " ", text)  # Collapse multiple spaces
    text = re.sub(r"\n{3,}", "\n\n", text)   # Limit consecutive newlines

    # Advanced punctuation handling (keep some meaningful punctuation)
    kept_punct = "-'"  # Keep hyphens and apostrophes
    text = text.translate(str.maketrans('', '', string.punctuation.replace(kept_punct, '')))

    # Remove control characters and weird unicode
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # Smart stopword removal (preserve crypto terms)
    crypto_terms = {"btc", "eth", "defi", "nft", "dao", "web3"}
    basic_stopwords = {
        "the", "and", "of", "to", "in", "a", "is", "on", "for", 
        "with", "as", "by", "this", "that", "it", "be", "are"
    }
    
    words = text.split()
    words = [
        word for word in words 
        if (word.lower() not in basic_stopwords or word.lower() in crypto_terms)
        and len(word) > 1  # Remove single characters except crypto symbols
    ]

    # Final cleanup
    text = " ".join(words).strip()
    return text if text else ""  # Ensure we never return None

def clean_text_minimal(text: str) -> str:
    """
    Lightweight cleaning for already-normalized text.
    Just removes extra whitespace and control chars.
    """
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)