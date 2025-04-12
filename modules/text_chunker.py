from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Union
import json
import hashlib
from pathlib import Path

class SmartChunker:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk_text(
        self,
        text: str,
        metadata: dict = None
    ) -> List[Dict[str, Union[str, dict]]]:
        """Split text into chunks with metadata"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators
        )
        
        chunks = splitter.split_text(text)
        return [{
            "text": chunk,
            "metadata": {
                "chunk_id": hashlib.md5(chunk.encode()).hexdigest(),
                **metadata
            }
        } for chunk in chunks]

    @staticmethod
    def save_chunks_to_json(
        chunks: List[Dict[str, Union[str, dict]]],
        path: Union[str, Path],
        indent: int = 2
    ) -> None:
        """Save chunks to JSON file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=indent, ensure_ascii=False)

    @staticmethod
    def load_chunks_from_json(path: Union[str, Path]) -> List[Dict[str, Union[str, dict]]]:
        """Load chunks from JSON file"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

if __name__ == "__main__":
    # Test functionality
    chunker = SmartChunker()
    test_text = "This is a test document. " * 50
    chunks = chunker.chunk_text(test_text, {"source": "test"})
    print(f"Generated {len(chunks)} chunks")