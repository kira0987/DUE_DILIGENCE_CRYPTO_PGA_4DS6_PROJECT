# utils/build_vectorstore.py
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
from pathlib import Path
import os

def get_embedding_model():
    return HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def get_cache_path(text):
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_dir = Path("vector_cache")
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{text_hash}"

def build_vector_store(text):
    embeddings = get_embedding_model()
    cache_path = get_cache_path(text)
    
    if cache_path.with_suffix(".pkl").exists():
        return FAISS.load_local(str(cache_path.parent), embeddings, str(cache_path.name))
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    texts = splitter.split_text(text)
    
    db = FAISS.from_texts(texts, embedding=embeddings)
    db.save_local(str(cache_path.parent), str(cache_path.name))
    return db