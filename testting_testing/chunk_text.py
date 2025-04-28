import os
import spacy
from utils import extract_entities, analyze_sentiment, BASE_RISK_CATEGORIES, KEYWORDS, lemmatizer
import logging
import re
from concurrent.futures import ProcessPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load SpaCy model once
nlp = spacy.load("en_core_web_trf")

def semantic_chunking(text, target_chunk_size=500):
    """
    Chunk text into segments of approximately 500 words, preserving semantic boundaries (sentences).
    """
    doc = nlp(text)
    chunks = []
    current_chunk = []
    current_word_count = 0
    section_id = 0

    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_word_count = len(sent_text.split())

        # Check for section breaks (e.g., numbered headings like "1. Introduction")
        if re.match(r"^\d+\.\s+.+$", sent_text) and current_chunk:
            # Start a new chunk if we hit a section boundary and have content
            chunks.append((" ".join(current_chunk), f"Section {section_id}"))
            section_id += 1
            current_chunk = [sent_text]
            current_word_count = sent_word_count
        elif current_word_count + sent_word_count > target_chunk_size and current_chunk:
            # If adding this sentence exceeds 500 words, finalize the current chunk
            chunks.append((" ".join(current_chunk), f"Section {section_id}"))
            section_id += 1
            current_chunk = [sent_text]
            current_word_count = sent_word_count
        else:
            # Add sentence to current chunk
            current_chunk.append(sent_text)
            current_word_count += sent_word_count

    # Append the last chunk if it exists
    if current_chunk:
        chunks.append((" ".join(current_chunk), f"Section {section_id}"))

    logging.info(f"Created {len(chunks)} chunks targeting ~{target_chunk_size} words each.")
    return [{"text": chunk, "section": section} for chunk, section in chunks]

def process_chunk(chunk, txt_file, i):
    """
    Process a single chunk: extract entities, analyze sentiment, and build metadata.
    """
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
    """
    Chunk text from a file into ~500-word segments and process them humbly.
    """
    logging.info(f"Chunking text from: {txt_file}")
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Use the target size of 500 words
    chunks = semantic_chunking(text, target_chunk_size=word_limit)
    
    chunk_data = []
    base_name = os.path.splitext(os.path.basename(txt_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_chunks.txt")
    os.makedirs(output_dir, exist_ok=True)
    
    # Write chunks to file
    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(chunk["text"])
            if i < len(chunks) - 1:
                f.write("\n\n")
    
    # Process chunks humbly: single-threaded by default, optional light multiprocessing
    use_multiprocessing = False  # Toggle to True if your system can handle 2 workers
    if use_multiprocessing:
        with ProcessPoolExecutor(max_workers=2) as executor:  # Conservative worker count
            chunk_data = list(executor.map(lambda x: process_chunk(x[1], txt_file, x[0]), enumerate(chunks)))
    else:
        # Single-threaded processing for humility
        for i, chunk in enumerate(chunks):
            chunk_data.append(process_chunk(chunk, txt_file, i))
            logging.debug(f"Processed chunk {i + 1}/{len(chunks)}")

    logging.info(f"Chunks saved to: {output_file}")
    logging.info(f"Average chunk size: {sum(len(c['text'].split()) for c in chunks) / len(chunks):.1f} words")
    return chunk_data, output_file