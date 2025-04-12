import spacy
from spacy.matcher import PhraseMatcher
from spacy.language import Language
import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import json
from pathlib import Path

# Load NLP model
nlp = spacy.load("en_core_web_lg")
nlp.add_pipe("sentencizer")

# Configuration paths
CONFIG_DIR = Path(__file__).parent / "entity_configs"
KNOWN_ENTITIES_FILE = CONFIG_DIR / "known_entities.json"
BLACKLIST_FILE = CONFIG_DIR / "blacklists.json"

# Load known entities and blacklists
def load_entity_configs():
    """Load predefined entity lists and blacklists"""
    with open(KNOWN_ENTITIES_FILE, "r", encoding="utf-8") as f:
        known_entities = json.load(f)
    
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        blacklists = json.load(f)
    
    return known_entities, blacklists

KNOWN_ENTITIES, BLACKLISTS = load_entity_configs()

# Patterns
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
CRYPTO_ADDRESS_PATTERN = r"\b(0x)?[0-9a-fA-F]{40}\b"
PHONE_PATTERN = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"

class EntityValidator:
    """Strict validation rules with crypto-specific improvements"""
    
    @staticmethod
    def is_valid_person(text: str) -> bool:
        """Validate person names with strict rules"""
        text_lower = text.lower()
        
        # Must have at least 2 words, proper capitalization, no numbers
        conditions = [
            len(text.split()) >= 2,
            text.istitle(),
            not any(c.isdigit() for c in text),
            not any(term in text_lower for term in BLACKLISTS["person_blacklist"]),
            not any(text_lower.endswith(suffix) for suffix in BLACKLISTS["person_suffixes"])
        ]
        
        return all(conditions)
    
    @staticmethod
    def is_valid_org(text: str) -> bool:
        """Validate organization names"""
        text_lower = text.lower()
        
        conditions = [
            3 <= len(text) <= 50,
            text[0].isupper(),
            not any(b in text_lower for b in BLACKLISTS["org_blacklist"]),
            not any(text_lower.endswith(suffix) for suffix in BLACKLISTS["org_suffixes"]),
            not any(text_lower.startswith(prefix) for prefix in BLACKLISTS["org_prefixes"])
        ]
        
        return all(conditions)
    
    @staticmethod
    def is_valid_crypto_project(text: str) -> bool:
        """Validate cryptocurrency projects"""
        text_lower = text.lower()
        
        # Check against known projects first
        if any(proj.lower() == text_lower for proj in KNOWN_ENTITIES["crypto_projects"]):
            return True
            
        # Generic project validation
        conditions = [
            2 <= len(text.split()) <= 4,
            not any(b in text_lower for b in BLACKLISTS["crypto_blacklist"]),
            not any(text_lower.endswith(suffix) for suffix in BLACKLISTS["crypto_suffixes"])
        ]
        
        # Must contain at least one known crypto term
        conditions.append(
            any(term in text_lower for term in KNOWN_ENTITIES["crypto_terms"])
        )
        
        return all(conditions)
    
    @staticmethod
    def is_valid_location(text: str) -> bool:
        """Validate locations against known list"""
        return text.lower() in {loc.lower() for loc in KNOWN_ENTITIES["locations"]}

def setup_matchers(nlp) -> Dict[str, PhraseMatcher]:
    """Create phrase matchers for known entities"""
    matchers = {}
    
    # Crypto project matcher
    crypto_matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp(text) for text in KNOWN_ENTITIES["crypto_projects"]]
    crypto_matcher.add("CRYPTO_PROJECT", patterns)
    matchers["crypto"] = crypto_matcher
    
    # Organization matcher
    org_matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp(text) for text in KNOWN_ENTITIES["organizations"]]
    org_matcher.add("ORG", patterns)
    matchers["org"] = org_matcher
    
    return matchers

MATCHERS = setup_matchers(nlp)

def normalize_entity(entity_type: str, text: str) -> str:
    """Standardize entity formatting"""
    # Apply type-specific normalization
    if entity_type == "person":
        # Standardize name formatting (Title Case)
        return " ".join(word.capitalize() for word in text.split())
    
    elif entity_type in ["crypto_project", "organization"]:
        # Remove common suffixes and standardize casing
        text = re.sub(r'\b(LLC|Inc|Ltd|Foundation|Labs|DAO|DeFi|Network|Protocol)\b', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    return text

def post_process_entities(entities: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """Clean and deduplicate extracted entities"""
    processed = {}
    
    for entity_type, entity_set in entities.items():
        # Normalize each entity
        normalized = {normalize_entity(entity_type, e) for e in entity_set}
        
        # Remove subsumed entities (shorter versions of longer entities)
        final_entities = set()
        for entity in sorted(normalized, key=len, reverse=True):
            if not any(e != entity and entity.lower() in e.lower() for e in final_entities):
                if entity:  # Skip empty strings
                    final_entities.add(entity)
        
        processed[entity_type] = sorted(final_entities)
    
    return processed

def extract_named_entities(text: str) -> Dict[str, List[str]]:
    """Comprehensive entity extraction pipeline"""
    doc = nlp(text)
    entities = defaultdict(set)
    
    # Stage 1: spaCy NER extraction with strict validation
    for ent in doc.ents:
        clean_text = ' '.join(ent.text.strip().split())
        
        if ent.label_ == "PERSON" and EntityValidator.is_valid_person(clean_text):
            entities["person"].add(clean_text)
            
        elif ent.label_ == "ORG":
            if EntityValidator.is_valid_crypto_project(clean_text):
                entities["crypto_project"].add(clean_text)
            elif EntityValidator.is_valid_org(clean_text):
                entities["organization"].add(clean_text)
                
        elif ent.label_ == "GPE" and EntityValidator.is_valid_location(clean_text):
            entities["location"].add(clean_text)
    
    # Stage 2: Phrase matching for known entities
    for match_id, start, end in MATCHERS["crypto"](doc):
        entities["crypto_project"].add(doc[start:end].text)
    
    for match_id, start, end in MATCHERS["org"](doc):
        entities["organization"].add(doc[start:end].text)
    
    # Stage 3: Pattern-based extraction
    entities["email"] = set(re.findall(EMAIL_PATTERN, text))
    entities["crypto_address"] = set(re.findall(CRYPTO_ADDRESS_PATTERN, text))
    
    # Stage 4: Post-processing
    processed_entities = post_process_entities(entities)
    
    return processed_entities

def extract_risk_features(text: str) -> Tuple[Dict[str, List[str]], float]:
    """Enhanced risk term extraction"""
    risk_categories = {
        "regulatory": KNOWN_ENTITIES["risk_terms"]["regulatory"],
        "technical": KNOWN_ENTITIES["risk_terms"]["technical"],
        "financial": KNOWN_ENTITIES["risk_terms"]["financial"],
        "operational": KNOWN_ENTITIES["risk_terms"]["operational"]
    }
    
    found = {k: set() for k in risk_categories}
    doc = nlp(text.lower())
    
    for category, terms in risk_categories.items():
        for term in terms:
            if term.lower() in doc.text:
                found[category].add(term)
    
    # Calculate weighted risk score
    weights = {"regulatory": 1.2, "technical": 1.1, "financial": 1.0, "operational": 0.9}
    score = min(sum(len(v) * 10 * weights[k] for k, v in found.items()), 100)
    
    return {k: sorted(v) for k, v in found.items()}, round(score, 2)