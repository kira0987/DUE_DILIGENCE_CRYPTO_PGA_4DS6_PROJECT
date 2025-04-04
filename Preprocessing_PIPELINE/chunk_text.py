import os
from fuzzywuzzy import fuzz
import logging
from utils import KEYWORDS, lemmatizer, extract_entities, extract_region, RISK_CATEGORIES, analyze_sentiment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fuzzy_match_keyword(text, keyword, threshold=85):
    """Check if a keyword fuzzily matches any word in the text."""
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    text_words = [lemmatizer.lemmatize(word) for word in text_lower.split()]
    keyword_root = lemmatizer.lemmatize(keyword_lower)
    return any(fuzz.ratio(word, keyword_root) >= threshold for word in text_words)

def categorize_terms(text):
    """Categorize text based on predefined risk terms."""
    text_lower = text.lower()
    categories = {cat: [] for cat in RISK_CATEGORIES}
    for category, terms in RISK_CATEGORIES.items():
        for term in terms:
            if fuzzy_match_keyword(text_lower, term):
                categories[category].append(term)
    return categories

def chunk_text_by_words(txt_file, output_dir, word_limit=500):
    """Chunk text file into segments and enrich with metadata."""
    logging.info(f"Chunking text from: {txt_file}")
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    words = text.split()
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for word in words:
        current_chunk.append(word)
        current_word_count += 1
        
        if current_word_count >= word_limit:
            chunk_text = " ".join(current_chunk)
            period_idx = chunk_text.find('.', len(" ".join(current_chunk[:word_limit])))
            if period_idx != -1:
                chunk_text = chunk_text[:period_idx + 1]
                remaining_text = chunk_text[period_idx + 1:].strip()
                chunks.append({"title": f"Chunk {len(chunks) + 1}", "text": chunk_text})
                current_chunk = remaining_text.split() if remaining_text else []
                current_word_count = len(current_chunk)
            else:
                chunks.append({"title": f"Chunk {len(chunks) + 1}", "text": chunk_text})
                current_chunk = []
                current_word_count = 0
    
    if current_chunk:
        chunks.append({"title": f"Chunk {len(chunks) + 1}", "text": " ".join(current_chunk)})
    
    chunk_data = []
    base_name = os.path.splitext(os.path.basename(txt_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_chunks.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            chunk_text = chunk["text"]
            f.write(chunk_text)
            if i < len(chunks) - 1:
                f.write("\n\n")
            
            matched_keywords = [kw for kw in KEYWORDS if fuzzy_match_keyword(chunk_text, kw)]
            entities = extract_entities(chunk_text)
            categories = categorize_terms(chunk_text)
            sentiment_data = analyze_sentiment(chunk_text)
            
            metadata = {
                "matched_keywords": matched_keywords,
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["sentiment_score"],
                "risk_score": entities["risk_score"],
                "categories": categories,
                "entities": entities,
                "source": txt_file,
                "region": extract_region(chunk_text),
                "content_type": "text"
            }
            
            chunk_data.append({
                "chunk_id": i,
                "title": chunk["title"],
                "text": chunk_text,
                "metadata": metadata
            })
    
    logging.info(f"Chunks saved to: {output_file}")
    return chunk_data, output_file