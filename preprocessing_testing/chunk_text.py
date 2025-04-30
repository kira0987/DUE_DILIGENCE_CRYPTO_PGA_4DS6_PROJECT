import os
import spacy
from utils import extract_entities, analyze_sentiment, RISK_CATEGORIES, KEYWORDS, lemmatizer
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
nlp = spacy.load("en_core_web_trf")

def semantic_chunking(text, max_chunk_size=500):
    doc = nlp(text)
    chunks = []
    current_chunk = []
    current_length = 0
    sections = {}
    section_id = 0
    
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if re.match(r"^\d+\.\s+.+$", sent_text):  # Detect section headers
            if current_chunk:
                chunks.append((" ".join(current_chunk), f"Section {section_id}"))
                section_id += 1
            current_chunk = [sent_text]
            current_length = len(sent_text.split())
        elif current_length + len(sent_text.split()) > max_chunk_size and current_chunk:
            chunks.append((" ".join(current_chunk), f"Section {section_id}"))
            current_chunk = [sent_text]
            current_length = len(sent_text.split())
        else:
            current_chunk.append(sent_text)
            current_length += len(sent_text.split())
    
    if current_chunk:
        chunks.append((" ".join(current_chunk), f"Section {section_id}"))
    return [{"text": chunk, "section": section} for chunk, section in chunks]

def chunk_text_by_words(txt_file, output_dir, word_limit=500):
    logging.info(f"Chunking text from: {txt_file}")
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    avg_sentence_length = len(text.split()) / len(text.split('.')) if '.' in text else word_limit
    adjusted_word_limit = min(max(int(avg_sentence_length * 5), 200), word_limit)
    chunks = semantic_chunking(text, max_chunk_size=adjusted_word_limit)
    
    chunk_data = []
    base_name = os.path.splitext(os.path.basename(txt_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_chunks.txt")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(chunk["text"])
            if i < len(chunks) - 1:
                f.write("\n\n")
            
            entities, anonymized_chunk = extract_entities(chunk["text"])
            sentiment_data = analyze_sentiment(anonymized_chunk)
            
            metadata = {
                "matched_keywords": [kw for kw in KEYWORDS if kw.lower() in anonymized_chunk.lower()],
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["sentiment_score"],
                "risk_score": entities["risk_score"],
                "categories": {cat: [t for t in terms if t.lower() in anonymized_chunk.lower()] 
                               for cat, terms in RISK_CATEGORIES.items()},
                "entities": entities,
                "source": txt_file,
                "region": entities["region"],
                "content_type": "text",
                "chunk_size": len(anonymized_chunk.split()),
                "section": chunk["section"]
            }
            
            chunk_data.append({
                "chunk_id": i,
                "title": f"Chunk {i + 1}",
                "text": anonymized_chunk,
                "metadata": metadata
            })
    
    logging.info(f"Chunks saved to: {output_file}")
    return chunk_data, output_file