import re
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import phonenumbers
import pyap
from email_validator import validate_email, EmailNotValidError
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from flair.data import Sentence
from flair.models import SequenceTagger
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import multiprocessing
from tqdm import tqdm
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EDGAR_BASE_URL = "https://www.sec.gov/Archives/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 1000
EMBEDDING_BATCH_SIZE = 32

# Crypto Terms and Risk Categories (from your original code)
CRYPTO_TERMS = {
    "DeFi", "NFT", "DAO", "staking", "blockchain", "smart contract", "token",
    "wallet", "exchange", "stablecoin", "yield farming", "liquidity pool",
    "gas", "mining", "consensus", "fork", "ICO", "IDO", "airdrop", "oracle",
    "cross-chain", "layer 1", "layer 2", "custody", "DEX", "CEX", "Web3",
    "proof of stake", "tokenomics", "minting", "burning", "bridge", "MEV",
    "rug pull", "flash loan", "impermanent loss", "AMM", "front-running",
    "sandwich attack", "multisig", "cold storage", "hot wallet", "private key",
    "public key", "seed phrase", "hardware wallet", "51% attack", "reentrancy",
    "sybil attack", "dusting attack", "phishing", "sim swapping", "wash trading",
    "pump and dump", "exit scam", "honeypot", "mixer", "tumbler", "zk-SNARK",
    "zero-knowledge proof", "validium", "rollup", "sidechain", "sharding"
}

RISK_CATEGORIES = {
    "legal_regulatory": {
        "SEC", "CFTC", "FINRA", "AML", "KYC", "FATCA", "OFAC", "FINCEN",
        "SOX", "Dodd-Frank", "BSA", "CEA", "CCPA", "GLBA", "PATRIOT Act",
        "sanctions", "compliance", "regulation", "enforcement", "lawsuit",
        "subpoena", "investigation", "penalty", "fine", "violation"
    },
    "cyber_security": {
        "hack", "exploit", "breach", "phishing", "malware", "ransomware",
        "DDoS", "zero-day", "vulnerability", "attack", "compromise", "leak",
        "theft", "drain", "spoofing", "injection", "backdoor", "keylogger"
    },
    "financial_risk": {
        "volatility", "liquidity", "insolvency", "bankruptcy", "default",
        "leverage", "margin", "collateral", "undercollateralized", "shortfall",
        "liquidation", "flash crash", "depeg", "bank run", "withdrawal freeze"
    },
    "operational_risk": {
        "downtime", "outage", "scalability", "throughput", "latency",
        "congestion", "bottleneck", "failure", "bug", "glitch", "downtime",
        "upgrade", "fork", "governance", "dispute", "deadlock", "veto"
    }
}

RISK_WEIGHTS = {
    "legal_regulatory": 4.0,
    "cyber_security": 4.5,
    "financial_risk": 3.5,
    "operational_risk": 3.0
}

FORM_WEIGHTS = {
    "10-K": 4.0, "10-Q": 3.5, "8-K": 3.0, "S-1": 4.5,
    "D": 3.0, "6-K": 2.5, "13F": 2.0, "4": 3.0,
    "DEF 14A": 2.5, "20-F": 3.5
}

class SECFilingProcessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.embedding_cache_file = "embedding_cache.json"
        self.embedding_cache = self._load_embedding_cache()
        self.nlp = spacy.load("en_core_web_sm", disable=['parser', 'textcat'])
        self.flair_tagger = SequenceTagger.load("flair/ner-english-large")
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def _load_embedding_cache(self):
        if os.path.exists(self.embedding_cache_file):
            with open(self.embedding_cache_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_embedding_cache(self):
        with open(self.embedding_cache_file, 'w') as f:
            json.dump(self.embedding_cache, f)

    def extract_entities(self, text):
        doc = self.nlp(text[:1000000])
        text_lower = text.lower()
        
        entities = {
            "emails": list(set(re.findall(r'\b[\w.-]+@[\w.-]+\.\w+\b', text))),
            "phone_numbers": self.extract_phone_numbers(text),
            "urls": re.findall(r'(https?://[^\s]+|www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text),
            "addresses": [str(a) for a in pyap.parse(text, country="US")],
            "cik_numbers": re.findall(r'CENTRAL INDEX KEY:\s*(\d{10})', text),
            "crypto_addresses": {
                "ethereum": re.findall(r'\b(0x)?[0-9a-fA-F]{40}\b', text),
                "bitcoin": re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', text)
            },
            "companies": list(set(ent.text for ent in doc.ents if ent.label_ in ("ORG", "COMPANY"))),
            "persons": self.extract_person_names(text),
            "crypto_terms": [term for term in CRYPTO_TERMS if term.lower() in text_lower],
            "risk_mentions": [
                (term, category)
                for category, terms in RISK_CATEGORIES.items()
                for term in terms if term.lower() in text_lower
            ]
        }
        entities["sentiment"] = self.analyze_sentiment(text)
        return entities

    def extract_person_names(self, text):
        sentence = Sentence(text[:100000])
        self.flair_tagger.predict(sentence)
        return list(set(entity.text for entity in sentence.get_spans("ner") if entity.tag == "PER"))

    def analyze_sentiment(self, text):
        scores = self.sentiment_analyzer.polarity_scores(text)
        compound = scores["compound"]
        risk_count = sum(1 for term in CRYPTO_TERMS if term.lower() in text.lower())
        if risk_count > 5 and compound > 0:
            compound = max(-1, compound - 0.2)
        sentiment = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
        return {"sentiment": sentiment, "score": compound}

    def calculate_risk_score(self, risk_mentions, sentiment):
        category_scores = defaultdict(float)
        for term, category in risk_mentions:
            category_scores[category] += RISK_WEIGHTS.get(category, 1.0)
        sentiment_modifier = {"positive": 0.8, "neutral": 1.0, "negative": 1.5}[sentiment]
        return sum(category_scores.values()) * sentiment_modifier

    def process_large_scale(self, file_list_path: str, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        with open(file_list_path, 'r') as f:
            total_files = sum(1 for _ in f)
        
        with open(file_list_path, 'r') as f:
            chunk = []
            for i, line in enumerate(tqdm(f, total=total_files)):
                file_path = line.strip()
                if file_path:
                    chunk.append(file_path)
                
                if len(chunk) >= CHUNK_SIZE or i == total_files - 1:
                    self._process_chunk(chunk, output_dir)
                    chunk = []

    def _process_chunk(self, file_paths: List[str], output_dir: str):
        with multiprocessing.Pool() as pool:
            results = list(tqdm(
                pool.imap(self._process_single_filing, file_paths),
                total=len(file_paths)
            ))
        
        self._save_embedding_cache()
        
        for result in results:
            if result:
                output_path = os.path.join(
                    output_dir,
                    f"{result['accession_number']}.json"
                )
                with open(output_path, 'w') as f:
                    json.dump(result, f)

    def _process_single_filing(self, file_path: str) -> Optional[Dict]:
        try:
            if file_path.startswith('http'):
                filing_text = self.session.get(file_path).text
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    filing_text = f.read()

            metadata = {
                'cik': (re.search(r'CENTRAL INDEX KEY:\s*(\d{10})', filing_text) or [None])[1],
                'accession_number': (re.search(r'ACCESSION NUMBER:\s*(\d{10}-\d{2}-\d{6})', filing_text) or [None])[1],
                'form_type': (re.search(r'<CONFORMED SUBMISSION TYPE>\s*(\w+-?\w*)', filing_text) or [None])[1],
                'filing_date': (re.search(r'<CONFORMED PERIOD OF REPORT>\s*(\d{8})', filing_text) or [None])[1]
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}

            # Generate embedding
            cache_key = metadata.get('accession_number', hash(filing_text[:1000]))
            if cache_key not in self.embedding_cache:
                text_chunks = [filing_text[i:i+10000] for i in range(0, len(filing_text), 10000)]
                chunk_embeddings = self.embedding_model.encode(
                    text_chunks,
                    batch_size=EMBEDDING_BATCH_SIZE,
                    show_progress_bar=False
                )
                doc_embedding = np.mean(chunk_embeddings, axis=0)
                self.embedding_cache[cache_key] = doc_embedding.tolist()

            # Extract entities and calculate risk
            entities = self.extract_entities(filing_text)
            risk_score = self.calculate_risk_score(
                entities["risk_mentions"],
                entities["sentiment"]["sentiment"]
            )
            form_weight = FORM_WEIGHTS.get(metadata.get('form_type'), 1.0)

            return {
                **metadata,
                "file_path": file_path,
                "text_length": len(filing_text),
                "embedding": self.embedding_cache[cache_key],
                "entities": entities,
                "risk_score": risk_score,
                "weighted_risk_score": risk_score * form_weight,
                "form_weight": form_weight
            }

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return None

    def build_embedding_index(self, processed_dir: str, index_file: str):
        embeddings = []
        filenames = []
        metadata = []
        
        for filename in tqdm(os.listdir(processed_dir)):
            if filename.endswith('.json'):
                with open(os.path.join(processed_dir, filename), 'r') as f:
                    data = json.load(f)
                    if 'embedding' in data:
                        embeddings.append(data['embedding'])
                        filenames.append(filename)
                        metadata.append({
                            'cik': data.get('cik'),
                            'accession_number': data.get('accession_number'),
                            'form_type': data.get('form_type'),
                            'risk_score': data.get('risk_score')
                        })
        
        np.savez_compressed(
            index_file,
            embeddings=np.array(embeddings),
            filenames=np.array(filenames),
            metadata=np.array(metadata)
        )
        logger.info(f"Saved embedding index with {len(embeddings)} vectors")

if __name__ == "__main__":
    processor = SECFilingProcessor()
    
    # Process large file list
    processor.process_large_scale(
        file_list_path="all_sec_files.txt",
        output_dir="processed_filings"
    )
    
    # Build searchable index
    processor.build_embedding_index(
        processed_dir="processed_filings",
        index_file="sec_embeddings_index.npz"
    )