import spacy
import re
import json
import tiktoken
import ollama  # ✅ Use Ollama API for Nomic embedding
from langchain.text_splitter import RecursiveCharacterTextSplitter
from modules.vector_database import save_to_faiss  # FAISS Vector Database Storage

# Load NLP Model
nlp = spacy.load("en_core_web_lg")

# Define important entities to preserve
IMPORTANT_ENTITIES = {"ORG", "GPE", "MONEY", "LAW", "EVENT", "DATE", "PRODUCT", "PERCENT", "CARDINAL"}

def extract_important_phrases(text):
    """Extracts key entities (company names, laws, financial data) to avoid splitting them."""
    doc = nlp(text)
    return {ent.text for ent in doc.ents if ent.label_ in IMPORTANT_ENTITIES}

def count_tokens(text):
    """Counts tokens using OpenAI tokenizer."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def preprocess_text(text):
    """Prepares text by removing the Table of Contents and normalizing spacing."""
    text = re.sub(r"\s+", " ", text).strip()  # Normalize spaces
    text = re.sub(r"\.{3,}", " ", text)

    # ✅ Remove Table of Contents (ToC) more accurately
    toc_patterns = [
        r"(?i)(?:index|table of contents|contents)[\s\S]+?(?=\n[I1]\.)",  # Matches before section headers
        r"(?i)(?:index|contents)\s*(?:\.\.\.\.+|\d+)+[\s\S]+?(?=\n[I1]\.)"  # Handles ToC with dot leaders
    ]
    for pattern in toc_patterns:
        text = re.sub(pattern, "", text)

    return text

def get_embedding(text):
    """Generates embeddings using the locally installed Nomic Embed model via Ollama."""
    response = ollama.embeddings(model="nomic-embed-text", prompt=text)  # ✅ FIXED
    return response["embedding"]  # ✅ Extract embedding

def smart_chunk_text(text, max_tokens=600):
    """Splits text into meaningful sections while keeping chunks under the token limit."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens, chunk_overlap=50  # Overlap ensures sentence continuity
    )

    chunks = []
    split_texts = splitter.split_text(text)

    for i, chunk in enumerate(split_texts):
        chunks.append({
            "chunk_id": i + 1,
            "text": chunk,
            "tokens": count_tokens(chunk),
            "embedding": get_embedding(chunk)  # ✅ Call Ollama for embedding
        })

    return chunks

def save_chunks_to_json(chunks, filename):
    """Save chunked text into structured JSON."""
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(chunks, json_file, indent=4)
    print(f"✅ Chunks saved to {filename}")

# Example Usage
if __name__ == "__main__":
    # Load extracted text
    with open("test_pdfs/extracted/testpdf.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Preprocess & Chunk Text
    preprocessed_text = preprocess_text(raw_text)
    chunks = smart_chunk_text(preprocessed_text, max_tokens=600)

    # Save to JSON
    save_chunks_to_json(chunks, "test_pdfs/extracted/testpdf_chunks.json")

    # Save to FAISS Vector Database
    save_to_faiss(chunks)

    print(f"✅ Chunking & Embedding complete! {len(chunks)} chunks created.")