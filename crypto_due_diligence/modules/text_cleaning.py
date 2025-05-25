import re
import unicodedata
import spacy

# Load spaCy's stop words
nlp = spacy.load("en_core_web_sm")
STOP_WORDS = nlp.Defaults.stop_words

def clean_text(text):
    """
    Cleans extracted text by removing unnecessary characters, stop words, and formatting.
    
    :param text: Raw extracted text
    :return: Cleaned and preprocessed text
    """
    # Convert to lowercase
    text = text.lower()

    # Remove extra spaces, tabs, and newlines
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove special characters and punctuation (except essential ones)
    text = re.sub(r"[^a-zA-Z0-9,.!?$€%-]", " ", text)

    # Normalize unicode characters (fix encoding issues)
    text = unicodedata.normalize("NFKD", text)

    # Remove multiple spaces again (after cleaning)
    text = re.sub(r'\s+', ' ', text).strip()

    # Tokenize and remove stop words
    words = text.split()
    words = [word for word in words if word not in STOP_WORDS]

    return " ".join(words)

# Test the function
if __name__== "__main__":
    sample_text = "Bitcoin is a decentralized digital currency, but it has been used in fraud cases!"
    cleaned_sample = clean_text(sample_text)
    print("Original Text:", sample_text)
    print("Cleaned Text:", cleaned_sample)