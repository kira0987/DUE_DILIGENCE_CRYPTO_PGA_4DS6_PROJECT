import faiss
import json
import os
import numpy as np
import spacy

from typing import List, Dict
from core.chunker import chunk_sections, embed_chunks
from core.cleaner import clean_text_and_detect_sections

nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> List[str]:
    doc = nlp(text)
    return list(set(ent.text for ent in doc.ents if ent.label_ in {"ORG", "GPE", "MONEY", "LAW", "DATE", "PRODUCT", "PERCENT"}))

def score_chunk(text: str, entities: List[str]) -> float:
    word_count = len(text.split())
    entity_score = len(entities) / max(1, word_count)
    length_score = min(word_count / 300, 1)
    return round(0.6 * entity_score + 0.4 * length_score, 3)

def tag_chunk(text: str) -> List[str]:
    tags = []
    if "SEC" in text or "KYC" in text or "AML" in text:
        tags.append("compliance")
    if "investment" in text or "portfolio" in text or "performance" in text:
        tags.append("performance")
    if "governance" in text or "voting" in text:
        tags.append("governance")
    if "tokenomics" in text or "supply" in text:
        tags.append("tokenomics")
    return tags or ["general"]

def enrich_chunks(chunks: List[Dict]) -> List[Dict]:
    enriched = []
    for chunk in chunks:
        content = chunk["content"]
        entities = extract_entities(content)
        tags = tag_chunk(content)
        score = score_chunk(content, entities)
        enriched.append({
            **chunk,
            "entities": entities,
            "tags": tags,
            "importance_score": score
        })
    return enriched

def save_chunks_json(chunks: List[Dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"✅ Chunks enrichis sauvegardés dans {path}")

def save_faiss_index(index: faiss.IndexFlatIP, path: str):
    faiss.write_index(index, path)
    print(f"✅ Index FAISS sauvegardé dans {path}")

def create_index_pipeline(txt_path: str, output_chunks_path: str, output_index_path: str):
    with open(txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text, sections = clean_text_and_detect_sections(raw_text)
    base_chunks = chunk_sections(sections)
    enriched_chunks = enrich_chunks(base_chunks)
    embeddings = embed_chunks(enriched_chunks)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    save_chunks_json(enriched_chunks, output_chunks_path)
    save_faiss_index(index, output_index_path)

def load_index(path: str) -> faiss.IndexFlatIP:
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Index FAISS introuvable : {path}")
    print(f"📥 Index FAISS chargé depuis {path}")
    return faiss.read_index(path)

def load_chunks(path: str) -> List[Dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Fichier de chunks introuvable : {path}")
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"📥 Chunks chargés depuis {path}")
    return chunks
