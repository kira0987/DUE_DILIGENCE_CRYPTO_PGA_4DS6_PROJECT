import os
import numpy as np
import warnings
from pathlib import Path

# Configure numpy for FAISS compatibility
np.float = np.float32
np.int = np.int32

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

try:
    import faiss
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.vectorstores import FAISS
except ImportError as e:
    raise ImportError(
        "Failed to import required packages. Please ensure you have:\n"
        "1. numpy==1.26.2\n"
        "2. faiss-cpu==1.8.0\n"
        "3. langchain-community==0.3.20\n"
        f"Original error: {str(e)}"
    )

class VectorDatabase:
    def __init__(self):
        self.embedding = OllamaEmbeddings(
            model="mistral",
            base_url="http://localhost:11434"
        )
    
    @staticmethod
    def is_trusted_path(path: str) -> bool:
        """Validate that the path is within allowed directories"""
        try:
            path = Path(path).resolve()
            allowed_dir = Path("user_uploads").resolve()
            return allowed_dir in path.parents
        except Exception:
            return False
    
    def save_to_faiss(self, chunks, index_path):
        """Save with version-compatible method"""
        if not self.is_trusted_path(index_path):
            raise ValueError("Untrusted save path detected")
            
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        vectorstore = FAISS.from_texts(
            texts=texts,
            embedding=self.embedding,
            metadatas=metadatas
        )
        vectorstore.save_local(index_path)
    
    def search_faiss(self, query, index_path, k=5):
        """Search with proper error handling"""
        if not self.is_trusted_path(index_path):
            raise ValueError("Untrusted index path detected")
            
        try:
            vectorstore = FAISS.load_local(
                folder_path=index_path,
                embeddings=self.embedding,
                allow_dangerous_deserialization=True
            )
            results = vectorstore.similarity_search_with_score(query, k=k)
            return [{
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            } for doc, score in results]
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")