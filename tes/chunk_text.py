import os
import spacy
from utils import extract_entities, analyze_sentiment, BASE_RISK_CATEGORIES, KEYWORDS, lemmatizer
import logging
import re
from concurrent.futures import ProcessPoolExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

nlp = spacy.load("en_core_web_trf")

def semantic_chunking(text, target_chunk_size=500):
    doc = nlp(text)
    chunks = []
    current_chunk = []
    current_word_count = 0
    section_id = 0
    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_word_count = len(sent_text.split())
        if re.match(r"^\d+\.\s+.+$", sent_text) and current_chunk:
            chunks.append((" ".join(current_chunk), f"Section {section_id}"))
            section_id += 1
            current_chunk = [sent_text]
            current_word_count = sent_word_count
        elif current_word_count + sent_word_count > target_chunk_size and current_chunk:
            chunks.append((" ".join(current_chunk), f"Section {section_id}"))
            section_id += 1
            current_chunk = [sent_text]
            current_word_count = sent_word_count
        else:
            current_chunk.append(sent_text)
            current_word_count += sent_word_count
    if current_chunk:
        chunks.append((" ".join(current_chunk), f"Section {section_id}"))
    logging.info(f"Created {len(chunks)} chunks targeting ~{target_chunk_size} words each.")
    return [{"text": chunk, "section": section} for chunk, section in chunks]

def process_chunk(chunk, txt_file, i):
    entities, anonymized_chunk = extract_entities(chunk["text"])
    sentiment_data = analyze_sentiment(anonymized_chunk)
    metadata = {
        "matched_keywords": [kw for kw in KEYWORDS if kw.lower() in anonymized_chunk.lower()],
        "sentiment": sentiment_data["sentiment"],
        "sentiment_score": sentiment_data["sentiment_score"],
        "risk_score": entities["risk_score"],
        "categories": {cat: [t for t in terms if t.lower() in anonymized_chunk.lower()] 
                       for cat, terms in BASE_RISK_CATEGORIES.items()},
        "entities": entities,
        "source": txt_file,
        "region": entities["region"],
        "content_type": "text",
        "chunk_size": len(anonymized_chunk.split()),
        "section": chunk["section"]
    }
    return {
        "chunk_id": i,
        "title": f"Chunk {i + 1}",
        "text": anonymized_chunk,
        "metadata": metadata
    }

def chunk_text_by_words(txt_file, output_dir, word_limit=500):
    logging.info(f"Chunking text from: {txt_file}")
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = semantic_chunking(text, target_chunk_size=word_limit)
    chunk_data = []
    base_name = os.path.splitext(os.path.basename(txt_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_chunks.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(chunk["text"])
            if i < len(chunks) - 1:
                f.write("\n\n")
    use_multiprocessing = False
    if use_multiprocessing:
        with ProcessPoolExecutor(max_workers=2) as executor:
            chunk_data = list(executor.map(lambda x: process_chunk(x[1], txt_file, x[0]), enumerate(chunks)))
    else:
        for i, chunk in enumerate(chunks):
            chunk_data.append(process_chunk(chunk, txt_file, i))
            logging.debug(f"Processed chunk {i + 1}/{len(chunks)}")
    logging.info(f"Chunks saved to: {output_file}")
    logging.info(f"Average chunk size: {sum(len(c['text'].split()) for c in chunks) / len(chunks):.1f} words")
    return chunk_data, output_file