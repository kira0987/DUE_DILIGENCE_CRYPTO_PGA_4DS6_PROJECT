from fastapi import FastAPI, UploadFile, File, HTTPException
from pymongo import MongoClient
import numpy as np
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize with consistent embedding model
EMBEDDING_MODEL = "nomic-embed-text:latest"  # Always use this for both docs and questions
GENERATION_MODEL = "mistral:7b-instruct-q4_0"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = MongoClient("mongodb://localhost:27017/")
db = client["due_dilligence_crypto_fund_rag_database"]
questions_collection = db["questions"]

def get_embeddings(text: str) -> np.ndarray:
    """Get consistent embeddings using the same model"""
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            },
            timeout=60
        )
        response.raise_for_status()
        return np.array(response.json()["embedding"])
    except Exception as e:
        raise HTTPException(500, detail=f"Embedding Error: {str(e)}")

def validate_embedding_dimension(embedding: np.ndarray):
    """Ensure all embeddings have same dimension"""
    expected_dim = 768  # nomic-embed-text produces 768-dim embeddings
    if len(embedding) != expected_dim:
        raise HTTPException(500, detail=f"Invalid embedding dimension. Expected {expected_dim}, got {len(embedding)}")

def retrieve_relevant_questions(embedding: np.ndarray) -> list:
    validate_embedding_dimension(embedding)
    
    try:
        questions = []
        for q in questions_collection.find():
            # Convert stored embedding to numpy array
            q_embedding = np.array(q["embedding"])
            validate_embedding_dimension(q_embedding)
            
            # Calculate similarity
            similarity = np.dot(embedding, q_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(q_embedding)
            )
            questions.append((q["question"], similarity))
        
        # Return top 5 most similar questions
        return [q[0] for q in sorted(questions, key=lambda x: x[1], reverse=True)[:5]]
    
    except Exception as e:
        raise HTTPException(500, detail=f"Database Error: {str(e)}")

@app.post("/analyze_whitepaper")
async def analyze_whitepaper(file: UploadFile = File(...)):
    try:
        content = await file.read()
        logging.debug(f"File content length: {len(content)}")
        
        if file.filename.endswith('.json'):
            whitepaper_text = json.loads(content)
            logging.debug("JSON parsed successfully")
            if isinstance(whitepaper_text, dict):
                whitepaper_text = json.dumps(whitepaper_text)
        else:
            whitepaper_text = content.decode('utf-8')
            logging.debug("Text decoded successfully")
        
        # ... rest of the code
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {str(e)}")
        raise HTTPException(400, detail=f"Invalid JSON: {str(e)}")
    except UnicodeDecodeError as e:
        logging.error(f"Decode error: {str(e)}")
        raise HTTPException(400, detail=f"Invalid file encoding: {str(e)}")