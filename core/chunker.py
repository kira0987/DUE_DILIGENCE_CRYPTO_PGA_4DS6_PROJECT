from typing import List, Dict
from sentence_transformers import SentenceTransformer
import numpy as np

# Paramètres de découpe
CHUNK_SIZE = 300        # nombre de mots par chunk
CHUNK_OVERLAP = 50      # mots de recouvrement
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # modèle SentenceTransformer

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Découpe un texte en chunks avec chevauchement.

    Args:
        text (str): Le texte à découper.
        chunk_size (int): Nombre de mots par chunk.
        overlap (int): Nombre de mots partagés entre deux chunks.

    Returns:
        List[str]: Liste de chunks textuels.
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = words[i:i + chunk_size]
        if chunk:
            chunks.append(" ".join(chunk))

    return chunks

def chunk_sections(sections: Dict[str, str]) -> List[Dict]:
    """
    Découpe toutes les sections détectées en chunks.

    Args:
        sections (Dict[str, str]): Dictionnaire {section_title: texte}

    Returns:
        List[Dict]: Liste de chunks avec informations de section.
    """
    all_chunks = []
    for section_name, content in sections.items():
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "section": section_name.strip(),
                "chunk_id": f"{section_name.strip().upper()}_{i}",
                "content": chunk
            })
    return all_chunks

def embed_chunks(chunks: List[Dict]) -> np.ndarray:
    """
    Génére des embeddings pour chaque chunk.

    Args:
        chunks (List[Dict]): Liste de dictionnaires de chunks.

    Returns:
        np.ndarray: Embeddings numpy array.
    """
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    return np.array(embeddings)
