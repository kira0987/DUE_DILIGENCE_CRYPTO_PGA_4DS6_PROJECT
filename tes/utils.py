import spacy
from nltk.stem import WordNetLemmatizer
import nltk
import logging
from flair.data import Sentence
from flair.models import SequenceTagger
import pyap
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from transformers import pipeline
import re
from sentence_transformers import SentenceTransformer, util
from sec_edgar_api import EdgarClient
from fuzzywuzzy import fuzz
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib
import aiohttp
import asyncio
from requests_html import HTMLSession

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cache models globally
_sentence_transformer = None
_spacy_model = None
_flair_tagger = None
_sentiment_analyzer = None
_edgar_client = None

def get_sentence_transformer():
    global _sentence_transformer
    if _sentence_transformer is None:
        _sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2")
    return _sentence_transformer

def get_spacy_model():
    global _spacy_model
    if _spacy_model is None:
        _spacy_model = spacy.load("en_core_web_trf")
    return _spacy_model

def get_flair_tagger():
    global _flair_tagger
    if _flair_tagger is None:
        _flair_tagger = SequenceTagger.load("flair/ner-english-large")
    return _flair_tagger

def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return _sentiment_analyzer

def get_edgar_client():
    global _edgar_client
    if _edgar_client is None:
        _edgar_client = EdgarClient(user_agent="CryptoDueDiligence/1.0")
    return _edgar_client

lemmatizer = WordNetLemmatizer()

FINANCIAL_TERMS = {
    "revenue", "profit", "gross margin", "net income", "investment", "capital", "liability", "assets",
    "funding", "debt", "equity", "IPO", "cash flow", "liquidity", "valuation", "leverage", "portfolio",
    "return", "yield", "expense", "burn rate", "market cap", "dilution", "securities", "treasury",
    "collateral", "EBITDA", "ROI", "ROE", "P&L", "balance sheet", "income statement", "capex", "opex",
    "divestiture", "acquisition", "merger", "hedge", "short", "long", "custodial", "settlement",
    "clearing", "asset protection", "scalability", "default risk", "credit risk", "financial distress",
    "over-leverage", "illiquidity", "escrow", "trustee", "fiduciary", "audit trail", "financial health",
    "insider loan", "loan default", "interest rate", "amortization", "depreciation", "tax liability",
    "working capital", "cash reserve", "leverage ratio", "debt servicing", "financial covenant",
    "asset allocation", "portfolio diversification", "market volatility", "capital adequacy",
    "stress test", "financial exposure", "underfunding", "overfunding", "financial stability",
    "cost structure", "revenue stream", "profitability", "financial leverage", "equity financing",
    "debt financing", "capital expenditure", "operating margin", "cash conversion", "financial instrument",
    "asset-backed", "securitization", "credit rating", "financial projection", "budget deficit",
    "surplus", "financial transparency", "off-balance sheet", "insider trading", "Ponzi scheme",
    "token inflation", "staking yield", "liquidity pool value", "circulating supply", "treasury mismanagement",
    "fund lockup period", "yield manipulation", "capital flight", "asset dilution", "overcollateralization",
    "undercollateralization", "margin call", "liquidation risk", "debt-to-equity", "cash burn",
    "financial misstatement", "accounting fraud", "revenue recognition", "cost overrun", "fund diversion",
    "yield optimization", "portfolio rebalancing", "risk-adjusted return", "financial modeling",
    "capital efficiency", "token vesting", "fund allocation"
}

REGULATIONS = {
    "SEC", "CFTC", "FINRA", "AML", "KYC", "FATCA", "OFAC", "FINCEN", "SOX", "Dodd-Frank", "BSA", "CEA",
    "CCPA", "GLBA", "PATRIOT Act", "CRYPTO Act", "Howey Test", "Reg D", "Reg S", "Reg A+", "IRS", "CFPB",
    "NYDFS", "BitLicense", "Reg SHO", "T+2", "legal certainty", "regulatory compliance", "dispute resolution",
    "governance framework", "rule enforcement", "noncompliance penalty", "regulatory fine", "audit failure",
    "sanction violation", "compliance officer", "due diligence", "regulatory reporting", "legal action",
    "jurisdictional risk", "anti-corruption", "FCPA", "whistleblower", "data privacy", "GDPR", "securities law",
    "tax compliance", "export control", "trade sanction", "licensing requirement", "regulatory audit",
    "enforcement action", "civil penalty", "criminal liability", "disclosure obligation", "financial oversight",
    "regulatory gap", "compliance monitoring", "legal precedent", "anti-money laundering", "know your customer",
    "sanctions list", "regulatory framework", "compliance program", "legal risk", "regulatory change",
    "cross-border regulation", "financial regulation", "consumer protection", "data protection", "privacy law",
    "securities regulation", "tax evasion", "financial crime", "regulatory oversight", "MiCA", "Travel Rule",
    "VASPs", "FATF", "crypto tax reporting", "stablecoin regulation", "sanctions screening", "PEPs",
    "counter-terrorism financing", "CTF", "blacklist", "watchlist", "compliance violation", "regulatory breach",
    "licensing suspension", "fines and penalties", "regulatory investigation", "subpoena", "cease and desist",
    "AML/CTF", "KYC failure", "sanctions evasion", "regulatory arbitrage", "cross-jurisdictional conflict",
    "legal injunction", "compliance lapse", "regulatory enforcement action", "disclosure breach",
    "ESMA", "BaFin", "FCA", "MAS", "ASIC", "crypto licensing", "regulatory sandbox"
}

CRYPTO_TERMS = {
    "DeFi", "NFT", "DAO", "staking", "hashrate", "blockchain", "smart contract", "token", "wallet",
    "exchange", "stablecoin", "yield farming", "liquidity pool", "gas", "mining", "consensus", "fork",
    "ICO", "IDO", "airdrop", "governance", "oracle", "cross-chain", "layer 1", "layer 2", "custody",
    "DEX", "CEX", "Web3", "metaverse", "sharding", "sidechain", "atomic swap", "zk-SNARK", "proof of work",
    "proof of stake", "tokenomics", "minting", "burning", "bridge", "wrapped", "privacy coin", "flash loan",
    "MEV", "51% attack", "digital asset security", "distributed ledger", "interoperability", "connectivity",
    "DAS", "DLT", "smart contract roles", "emergency stop", "token pause", "cross-ledger", "quantum resistance",
    "rug pull", "exit liquidity", "smart contract bug", "bridge exploit", "oracle manipulation", "fund manager",
    "crypto custody", "token sale", "whitepaper fraud", "exchange hack", "multi-signature", "cold storage",
    "hot wallet", "decentralized governance", "protocol upgrade", "chain split", "sybil attack", "dusting attack",
    "replay attack", "token lockup", "vesting schedule", "liquidity lock", "smart contract audit", "block explorer",
    "hash collision", "non-fungible token", "decentralized finance", "crypto asset", "digital currency",
    "block reward", "mining pool", "gas fee", "transaction fee", "crypto exchange", "token standard", "ERC-20",
    "BEP-20", "token burn", "token mint", "cross-chain bridge", "layer 0", "off-chain", "on-chain",
    "crypto wallet", "hardware wallet", "software wallet", "crypto scam", "phishing attack", "wallet security",
    "private key", "public key", "impermanent loss", "liquidity pool rug pull", "rebase instability",
    "yield farming collapse", "front-running", "sandwich attack", "oracle spoofing", "protocol rollback",
    "chain reorganization", "double-spend", "reentrancy attack", "flash crash", "pump and dump", "wash trading",
    "exit scam", "spoofing", "fake volume", "rugpull", "honeypot", "dark pool", "slippage", "whale manipulation",
    "token delisting", "chain fork", "protocol exploit", "gas war", "MEV bot", "blockchain forensics",
    "transaction tracing", "crypto laundering", "mixer", "tumbler", "privacy layer", "zero-knowledge proof",
    "layer 3", "rollups", "zk-rollup", "optimistic rollup", "state channel", "plasma", "crypto bridge hack"
}

RISK_TERMS = set()

ESG_TERMS = {
    "carbon footprint", "sustainability", "green energy", "ESG compliance", "social impact", "human rights",
    "corporate governance", "board diversity", "executive compensation", "shareholder rights", "ethical sourcing",
    "environmental violation", "social responsibility", "governance failure", "climate risk", "sustainable investing",
    "net zero", "CSR", "stakeholder engagement", "transparency", "mining energy consumption",
    "community governance failure", "energy inefficiency", "ecological impact", "decentralized governance dispute",
    "environmental damage", "labor violation", "ethical breach", "social unrest", "governance opacity",
    "ESG reporting failure", "carbon emissions", "renewable energy", "pollution risk", "resource depletion",
    "biodiversity loss", "ethical misconduct", "greenwashing", "social license risk", "community displacement",
    "energy audit", "carbon offset", "ESG scoring", "sustainable tokenomics", "eco-friendly mining"
}

CYBERSECURITY_TERMS = {
    "data breach", "cyberattack", "phishing", "ransomware", "DDoS", "malware", "zero-day", "encryption",
    "firewall", "VPN", "penetration testing", "vulnerability assessment", "SOC", "SIEM", "endpoint security",
    "identity theft", "credential stuffing", "social engineering", "patch management", "cyber insurance",
    "incident response", "GDPR violation", "HIPAA violation", "dark web", "threat intelligence", "cyber hygiene",
    "private key theft", "wallet spoofing", "double-spend attack", "chain rollback", "sybil resistance failure",
    "node compromise", "brute force", "SQL injection", "XSS", "CSRF", "malware injection", "trojan", "worm",
    "spyware", "adware", "botnet", "privilege escalation", "session hijacking", "MITM", "eavesdropping",
    "packet sniffing", "DoS", "exploit kit", "rootkit", "keylogger", "backdoor", "RAT", "pharming",
    "clickjacking", "credential harvesting", "password cracking", "spear phishing", "whaling", "vishing",
    "smishing", "typosquatting", "DNS spoofing", "ARP poisoning", "buffer overflow", "heap overflow",
    "stack overflow", "format string attack", "race condition", "side-channel attack", "cryptographic attack",
    "cache poisoning", "crypto ransomware", "locker ransomware", "network intrusion", "zero-trust failure",
    "endpoint compromise", "insider threat", "supply chain attack", "firmware exploit", "hardware backdoor",
    "IoT vulnerability", "cloud breach", "API exploit", "authentication bypass", "session fixation", "cybersecurity",
    "ransomware", "phishing", "malware", "SOC", "encryption", "DDoS", "zero-day", "rootkit", "keylogger",
    "session hijacking", "trojan", "backdoor", "SQL injection", "XSS", "CSRF", "brute force", "botnet",
    "denial of service", "supply chain attack", "APT", "firewall", "SIEM", "vulnerability scanning",
    "patch management", "data exfiltration", "hacking", "penetration testing", "incident response",
    "network intrusion", "insider threat", "endpoint protection", "zero trust", "IAM", "privilege escalation",
    "crypto jacking", "API abuse", "token theft", "smart contract exploit", "wallet drain", "exploit kit",
    "social engineering", "cloud breach", "key rotation", "attack surface", "unauthorized access",
    "threat intelligence", "sandbox evasion", "logic bomb", "DNS hijack", "session replay", "MITM",
    "certificate spoofing", "replay attack", "hardware trojan", "fuzzing",
    "crypto phishing", "wallet cloning", "smart contract overflow", "chain impersonation", "node spoofing"
}

WHITEPAPER_TERMS = {
    "tokenomics", "vesting schedule", "token allocation", "staking yield", "circulating supply",
    "total supply", "burn mechanism", "minting policy", "liquidity pool", "governance model",
    "decentralized control", "centralized control", "team credibility", "technical feasibility",
    "scalability solution", "security protocol", "audit report", "bug bounty", "whitepaper fraud",
    "unrealistic yield", "opaque allocation", "unverified burn", "excessive minting",
    "unsustainable tokenomics", "hype language", "vague claims", "revolutionary technology",
    "guaranteed returns", "unprecedented opportunity", "quantum resistance", "infinite scalability",
    "zero latency", "team background", "advisory board", "partnership claims", "roadmap clarity",
    "milestone delivery", "prototype status", "testnet performance", "mainnet launch",
    "smart contract security", "cross-chain compatibility", "regulatory compliance",
    "KYC implementation", "AML policy", "fund lockup", "escrow mechanism", "proof of reserve",
    "custody solution", "multi-signature wallet", "cold storage policy", "hot wallet risk",
    "exit strategy", "rug pull risk", "pump and dump scheme", "insider allocation",
    "token dilution", "inflation risk", "deflation mechanism", "staking lockup",
    "liquidity provision", "market making", "exchange listing", "decentralized exchange",
    "centralized exchange", "oracle integration", "data feed reliability", "consensus mechanism",
    "proof of stake", "proof of work", "delegated proof of stake", "byzantine fault tolerance",
    "sharding implementation", "layer 2 solution", "sidechain integration", "privacy feature",
    "anonymity risk", "regulatory scrutiny", "sanction exposure", "jurisdictional clarity",
    "legal framework", "compliance roadmap", "audit frequency", "third-party validation",
    "open-source code", "proprietary technology", "patent status", "intellectual property",
    "community governance", "DAO structure", "voting power", "token holder rights",
    "incentive alignment", "economic model", "revenue model", "fee structure",
    "transaction cost", "gas optimization", "energy consumption", "carbon footprint",
    "sustainable mining", "ESG alignment", "social impact", "ethical considerations"
}

BASE_RISK_CATEGORIES = {
    "legal_regulatory": {
        "regulatory compliance", "compliance officer", "due diligence", "regulatory reporting", "tax compliance",
        "licensing requirement", "compliance monitoring", "compliance program", "crypto licensing",
        "regulatory sandbox", "regulatory whitelist", "compliance certification", "jurisdictional alignment",
        "SEC", "CFTC", "FINRA", "AML", "KYC", "FATCA", "OFAC", "FINCEN", "SOX", "Dodd-Frank", "BSA", "CEA",
        "CCPA", "GLBA", "PATRIOT Act", "CRYPTO Act", "Howey Test", "Reg D", "Reg S", "Reg A+", "IRS", "CFPB",
        "NYDFS", "BitLicense", "Reg SHO", "T+2", "legal certainty", "dispute resolution", "governance framework",
        "rule enforcement", "audit failure", "compliance breach", "data privacy", "GDPR", "securities law",
        "export control", "trade sanction", "regulatory audit", "civil penalty", "disclosure obligation",
        "financial oversight", "regulatory gap", "legal precedent", "anti-money laundering", "know your customer",
        "sanctions list", "regulatory framework", "legal risk", "regulatory change", "cross-border regulation",
        "financial regulation", "consumer protection", "data protection", "privacy law", "securities regulation",
        "financial crime", "regulatory oversight", "MiCA", "Travel Rule", "VASPs", "FATF", "crypto tax reporting",
        "stablecoin regulation", "sanctions screening", "PEPs", "counter-terrorism financing", "CTF", "blacklist",
        "watchlist", "regulatory breach", "regulatory investigation", "ESMA", "BaFin", "FCA", "MAS", "ASIC",
        "contract ambiguity", "jurisdictional uncertainty", "unenforceable agreement", "regulatory violation",
        "compliance audit", "legal ambiguity", "cross-border legal risk", "jurisdictional conflict",
        "legal framework gap", "contractual uncertainty", "legal clarity issue", "compliance gap",
        "noncompliance penalty", "regulatory fine", "sanction violation", "noncompliance fine", "sanction risk",
        "regulatory penalty", "compliance violation", "licensing suspension", "fines and penalties",
        "compliance lapse", "disclosure breach", "regulatory whitelist violation", "compliance penalty",
        "legal action", "jurisdictional risk", "anti-corruption", "FCPA", "whistleblower", "tax evasion",
        "enforcement action", "criminal liability", "subpoena", "cease and desist", "AML/CTF", "KYC failure",
        "sanctions evasion", "regulatory arbitrage", "cross-jurisdictional conflict", "legal injunction",
        "regulatory enforcement action", "legal dispute risk", "lawsuit", "sanctions", "fraud", "money laundering",
        "ponzi", "insider trading", "unregistered offering", "legal noncompliance", "settlement uncertainty",
        "contract enforceability", "compliance failure", "regulatory ban", "misrepresentation", "financial crime",
        "dispute escalation", "litigation risk", "arbitration failure", "legal enforceability issue",
        "terms violation", "legal precedent risk", "statutory noncompliance", "judicial uncertainty",
        "legal interpretation risk", "contractual gap", "enforcement uncertainty", "legal challenge",
        "dispute resolution failure", "binding agreement failure", "court ruling risk", "legal exposure",
        "contractual noncompliance", "legal obligation failure", "regulatory interpretation risk",
        "legal standing risk", "unenforceable clause", "contractual dispute", "legal jurisdiction risk",
        "audit noncompliance", "regulatory enforcement", "terrorist financing", "counterfeit transaction",
        "bribery", "corruption", "money laundering scheme", "sanctions circumvention", "regulatory blacklist",
        "legal sanction", "regulatory crackdown", "legal settlement"
    },
    "cyber_resilience": {
        "phishing", "social engineering", "vishing", "smishing", "typosquatting", "cyber hygiene", "crypto phishing",
        "vulnerability assessment", "patch management", "encryption", "firewall", "VPN", "SIEM", "endpoint security",
        "cyber insurance", "threat intelligence", "system outage", "downtime", "oracle failure", "privacy breach",
        "security flaw", "denial of service", "service interruption", "redundancy failure", "failover issue",
        "backup failure", "data corruption", "availability loss", "fault tolerance failure", "security lapse",
        "patch delay", "unpatched vulnerability", "resilience gap", "threat detection failure", "monitoring lapse",
        "secure configuration failure", "attack surface expansion", "network resilience", "threat mitigation",
        "system hardening", "data breach", "cyberattack", "ransomware", "DDoS", "malware", "zero-day",
        "penetration testing", "SOC", "incident response", "GDPR violation", "HIPAA violation", "dark web",
        "credential stuffing", "private key theft", "wallet spoofing", "sybil resistance failure", "node compromise",
        "brute force", "SQL injection", "XSS", "CSRF", "malware injection", "trojan", "worm", "spyware", "adware",
        "botnet", "session hijacking", "MITM", "eavesdropping", "packet sniffing", "DoS", "exploit kit", "rootkit",
        "keylogger", "backdoor", "RAT", "pharming", "clickjacking", "credential harvesting", "password cracking",
        "DNS spoofing", "ARP poisoning", "buffer overflow", "heap overflow", "stack overflow", "format string attack",
        "race condition", "timing attack", "cache poisoning", "network intrusion", "endpoint compromise",
        "IoT vulnerability", "API exploit", "session fixation", "security breach", "encryption failure",
        "firewall breach", "network outage", "traffic attack", "consensus exploit", "quantum threat", "protocol flaw",
        "distributed denial of service", "resilience failure", "disaster recovery failure", "integrity violation",
        "uptime breach", "authentication bypass", "access control failure", "intrusion detection failure",
        "endpoint vulnerability", "network breach", "security protocol failure", "penetration risk",
        "hardening failure", "incident response failure", "recovery delay", "security posture weakness",
        "data integrity breach", "system robustness failure", "resilience overload", "smart contract overflow",
        "chain impersonation", "node spoofing", "cyber recovery plan", "double-spend attack", "chain rollback",
        "crypto ransomware", "locker ransomware", "zero-trust failure", "insider threat", "supply chain attack",
        "firmware exploit", "hardware backdoor", "cloud breach", "authentication bypass", "hack recovery",
        "cyber espionage", "data exfiltration", "ransomware lockdown", "malware propagation", "zero-day exploitation",
        "crypto jacking", "wallet cloning", "spear phishing", "whaling", "privilege escalation", "side-channel attack"
    },
    "asset_safeguarding": {
        "custody", "private key", "multi-signature", "cold wallet", "vault", "HSM", "secure enclave",
        "proof of reserve", "wallet backup", "offline storage", "key sharding", "hardware wallet", "2FA",
        "threshold signature scheme", "insurance coverage", "access control", "recovery protocol",
        "safeguarding keys", "digital vault", "key recovery", "loss prevention", "cold storage insurance",
        "tamper resistance", "security guarantee", "decentralized custody", "escrow smart contract",
        "asset tracking", "custody audit", "key escrow security", "fund safeguarding protocol",
        "asset theft", "custodial loss", "wallet breach", "unauthorized withdrawal", "custody breach",
        "hot wallet hack", "asset freeze", "asset mismanagement", "safekeeping failure", "deposit risk",
        "withdrawal delay", "asset diversion", "custodial insolvency", "trust account breach",
        "multi-signature failure", "key mismanagement", "asset exposure", "uninsured loss", "customer fund loss",
        "safeguarding breach", "asset recovery failure", "client asset risk", "customer data leak",
        "payment fraud", "transaction reversal", "token freeze", "asset lockout", "asset misallocation",
        "key rotation", "private key leak", "fund misappropriation", "account takeover", "external theft",
        "escrow failure", "trust violation", "asset seizure", "fund freeze", "identity theft", "custody exploit",
        "fund siphoning", "cold storage breach", "key escrow failure", "custodial fraud", "insider theft",
        "key compromise", "smart contract freeze", "rug pull", "exit scam", "custodial theft", "wallet drain"
    },
    "operational_scale": {
        "scalability", "capacity", "overload", "bottleneck", "resource constraint", "overprovisioning",
        "underprovisioning", "scaling cost overrun", "inadequate scaling", "load balancing failure",
        "load testing", "capacity planning", "capacity overload", "throughput bottleneck", "latency spike",
        "resource exhaustion", "scaling failure", "performance degradation", "transaction backlog",
        "bandwidth limitation", "queue overflow", "processing delay", "infrastructure bottleneck",
        "high latency", "low throughput", "scalability bottleneck", "resource contention", "service throttling",
        "peak load failure", "traffic surge", "demand spike", "expansion risk", "growth limitation",
        "operational ceiling", "concurrency issue", "dynamic scaling failure", "horizontal scaling issue",
        "vertical scaling limit", "multi-region failure", "geo-scaling risk", "node overload", "chain congestion",
        "transaction latency", "blockchain scalability issue", "network saturation", "processing bottleneck",
        "scalability audit", "system overload", "system failure", "operational disruption", "system saturation",
        "parallel processing failure", "service degradation", "operational failure", "system downtime",
        "performance optimization"
    },
    "interoperability": {
        "integration", "compatibility", "protocol mismatch", "network issue", "data exchange failure",
        "middleware failure", "connection timeout", "integration latency", "system linkage failure",
        "interoperability bottleneck", "connectivity overload", "inter-system latency",
        "integration dependency risk", "data interoperability risk", "interop testing", "protocol alignment",
        "integration failure", "API breakdown", "interface mismatch", "protocol incompatibility",
        "data sync failure", "interoperability breakdown", "cross-chain failure", "interoperability risk",
        "connectivity loss", "network disconnection", "system integration risk", "inter-system conflict",
        "communication breakdown", "sync delay", "interoperability gap", "cross-platform failure",
        "data flow interruption", "connectivity outage", "cross-ledger failure", "data transfer failure",
        "interface disruption", "cross-network failure", "interoperability overload", "connection instability",
        "sync disruption", "bridge latency", "chain isolation", "cross-chain validation", "bridge collapse",
        "cross-chain exploit", "interoperability flaw", "bridge security"
    },
    "market_risk": {
        "liquidity", "speculation", "market inefficiency", "arbitrage failure", "liquidity provision",
        "volatility", "bubble", "liquidity risk", "counterparty risk", "overexposure", "undercollateralization",
        "token devaluation", "market illiquidity", "market stress test", "market depth", "market crash",
        "flash crash", "liquidity drain", "market manipulation", "pump and dump", "wash trading",
        "market distortion", "speculative risk", "financial loss", "price manipulation", "spoofing attack",
        "fake volume", "market spoofing", "liquidity squeeze", "volatility spike", "market bubble",
        "speculative bubble", "crash risk", "market exit scam", "liquidity pool collapse", "price stability"
    },
    "general_operational": {
        "delay", "error", "human error", "operational audit", "default", "mismanagement", "oversight",
        "disruption", "third-party failure", "vendor risk", "supply chain risk", "technology risk",
        "infrastructure risk", "false positive", "team credibility", "financial opacity", "dependency risk",
        "vendor lock-in", "operational risk", "process failure", "team vetting", "process resilience",
        "bankruptcy", "reputational risk", "stakeholder misunderstanding", "unverified claims",
        "conflict of interest", "systemic risk", "code audit failure", "centralization risk",
        "impermanent loss", "rebase instability", "MEV exploitation", "code vulnerability", "audit gap",
        "negligence", "operational lapse", "governance transparency", "embezzlement", "insolvency",
        "fund mismanagement", "investor fraud", "misconduct", "false reporting", "executive risk",
        "insider threat", "vote manipulation", "DAO takeover", "team exit risk", "liquidity pool rug pull",
        "yield farming collapse", "governance token manipulation", "reentrancy", "unauthorized holdings",
        "trust violation", "financial misstatement", "collusion", "governance breakdown", "team incompetence",
        "project abandonment", "fraudulent intent", "rug pull", "ponzi scheme", "exit scam", "pump and dump",
        "fake volume", "wash trading", "token scam", "whitepaper fraud", "yield farming scam", "liquidity drain",
        "insider rug pull"
    },
    "esg_risk": {
        "sustainability", "green energy", "social impact", "human rights", "corporate governance",
        "board diversity", "shareholder rights", "ethical sourcing", "social responsibility",
        "sustainable investing", "net zero", "CSR", "stakeholder engagement", "transparency",
        "renewable energy", "energy audit", "carbon offset", "ESG scoring", "sustainable tokenomics",
        "eco-friendly mining", "carbon footprint", "mining energy consumption", "energy inefficiency",
        "ecological impact", "decentralized governance dispute", "governance opacity", "carbon emissions",
        "pollution risk", "resource depletion", "biodiversity loss", "social license risk",
        "community displacement", "environmental violation", "governance failure", "climate risk",
        "environmental damage", "labor violation", "ethical breach", "social unrest", "ESG reporting failure",
        "ethical misconduct", "greenwashing", "ESG compliance"
    },
    "whitepaper_risk": WHITEPAPER_TERMS
}

MITIGATION_TERMS = {
    "insured", "insurance policy", "SOC 2", "SOC 1", "ISO 27001",
    "penetration tested", "bug bounty", "audited", "smart contract audit",
    "cold storage", "segregated account", "multi-signature", "compliance team",
    "AML program", "KYC verified", "third-party custody", "firewall", "incident response plan",
    "data encryption", "threat monitoring", "disaster recovery", "regulatory approval",
    "registered with SEC", "regulated by CFTC", "BitLicense", "GDPR compliance", "SOC 2 implemented",
    "under FDIC protection", "compliant with MiCA", "regulated entity",
    "cyber insurance", "compliance audit", "risk mitigation plan", "secure backup"
}

POSITIVE_TERMS = {
    "revolutionary", "guaranteed", "breakthrough", "unprecedented", "exceptional", "best-in-class",
    "leading", "pioneering", "flawless", "perfect", "assured", "top-tier", "game-changer", "stellar",
    "outstanding", "ultimate", "secure forever", "risk-free", "unmatched", "infallible",
    "trustworthy", "reliable", "proven", "stable"
}

HYPE_RED_FLAGS = {
    "guaranteed returns", "risk-free investment", "revolutionary breakthrough", "unprecedented opportunity",
    "assured profits", "game-changing technology", "flawless execution", "perfect solution",
    "unmatched potential", "infallible strategy", "secure forever", "top-tier forever",
    "ultimate wealth", "stellar performance guaranteed", "proven without risk"
}

VAGUE_TERMS = {
    "innovative", "disruptive", "next-generation", "cutting-edge", "world-class", "transformative",
    "game-changing", "revolutionary", "paradigm shift", "future-proof", "scalable solution",
    "robust ecosystem", "dynamic platform", "holistic approach", "synergistic"
}

KEYWORDS = (
    FINANCIAL_TERMS | REGULATIONS | CRYPTO_TERMS | RISK_TERMS | ESG_TERMS | 
    CYBERSECURITY_TERMS | WHITEPAPER_TERMS
)

REGION_ACRONYMS = {
    "United States": "USA", "America": "USA", "New York": "USA-NY", "California": "USA-CA",
    "Texas": "USA-TX", "Florida": "USA-FL", "Illinois": "USA-IL", "Washington, D.C.": "USA-DC",
    "Puerto Rico": "USA-PR", "Guam": "USA-GU", "American Samoa": "USA-AS", "Virgin Islands": "USA-VI",
    "Canada": "CAN", "United Kingdom": "UK", "Britain": "UK", "Australia": "AUS", "Japan": "JPN",
    "Germany": "DEU", "France": "FRA", "South Korea": "KOR", "Singapore": "SGP", "Switzerland": "CHE",
    "Netherlands": "NLD", "Sweden": "SWE", "Norway": "NOR", "Denmark": "DNK", "New Zealand": "NZL",
    "European Union": "EU", "India": "IND", "Brazil": "BRA", "Mexico": "MEX", "South Africa": "ZAF",
    "Indonesia": "IDN", "Turkey": "TUR", "Argentina": "ARG", "Nigeria": "NGA", "Philippines": "PHL",
    "Thailand": "THA", "Malaysia": "MYS", "Vietnam": "VNM", "China": "CHN", "Hong Kong": "HKG",
    "Taiwan": "TWN", "Russia": "RUS", "Iran": "IRN", "North Korea": "PRK", "Cuba": "CUB", "Syria": "SYR",
    "Venezuela": "VEN", "Bahamas": "BHS", "Cayman Islands": "CYM", "Bermuda": "BMU", "Seychelles": "SYC",
    "Malta": "MLT", "Gibraltar": "GIB", "Panama": "PAN", "Belize": "BLZ", "British Virgin Islands": "VGB",
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "Andorra": "AND", "Angola": "AGO",
    "Antigua and Barbuda": "ATG", "Armenia": "ARM", "Austria": "AUT", "Azerbaijan": "AZE",
    "Bahrain": "BHR", "Bangladesh": "BGD", "Barbados": "BRB", "Belarus": "BLR", "Belgium": "BEL",
    "Benin": "BEN", "Bhutan": "BTN", "Bolivia": "BOL", "Bosnia and Herzegovina": "BIH",
    "Botswana": "BWA", "Brunei": "BRN", "Bulgaria": "BGR", "Burkina Faso": "BFA", "Burundi": "BDI",
    "Cambodia": "KHM", "Cameroon": "CMR", "Cape Verde": "CPV", "Central African Republic": "CAF",
    "Chad": "TCD", "Chile": "CHL", "Colombia": "COL", "Comoros": "COM", "Congo": "COG",
    "Costa Rica": "CRI", "Croatia": "HRV", "Cyprus": "CYP", "Czech Republic": "CZE", "DR Congo": "COD",
    "Djibouti": "DJI", "Dominica": "DMA", "Dominican Republic": "DOM", "Ecuador": "ECU", "Egypt": "EGY",
    "El Salvador": "SLV", "Equatorial Guinea": "GNQ", "Eritrea": "ERI", "Estonia": "EST",
    "Eswatini": "SWZ", "Ethiopia": "ETH", "Fiji": "FJI", "Finland": "FIN", "Gabon": "GAB",
    "Gambia": "GMB", "Georgia": "GEO", "Ghana": "GHA", "Greece": "GRC", "Grenada": "GRD",
    "Guatemala": "GTM", "Guinea": "GIN", "Guinea-Bissau": "GNB", "Guyana": "GUY", "Haiti": "HTI",
    "Honduras": "HND", "Hungary": "HUN", "Iceland": "ISL", "Ireland": "IRL", "Israel": "ISR",
    "Italy": "ITA", "Jamaica": "JAM", "Jordan": "JOR", "Kazakhstan": "KAZ", "Kenya": "KEN",
    "Kiribati": "KIR", "Kuwait": "KWT", "Kyrgyzstan": "KGZ", "Laos": "LAO", "Latvia": "LVA",
    "Lebanon": "LBN", "Lesotho": "LSO", "Liberia": "LBR", "Libya": "LBY", "Liechtenstein": "LIE",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Madagascar": "MDG", "Malawi": "MWI", "Maldives": "MDV",
    "Mali": "MLI", "Marshall Islands": "MHL", "Mauritania": "MRT", "Mauritius": "MUS",
    "Micronesia": "FSM", "Moldova": "MDA", "Monaco": "MCO", "Mongolia": "MNG", "Montenegro": "MNE",
    "Morocco": "MAR", "Mozambique": "MOZ", "Myanmar": "MMR", "Namibia": "NAM", "Nauru": "NRU",
    "Nepal": "NPL", "Nicaragua": "NIC", "Niger": "NER", "Oman": "OMN", "Pakistan": "PAK",
    "Palau": "PLW", "Palestine": "PSE", "Papua New Guinea": "PNG", "Paraguay": "PRY", "Peru": "PER",
    "Poland": "POL", "Portugal": "PRT", "Qatar": "QAT", "Romania": "ROU", "Rwanda": "RWA",
    "Saint Kitts and Nevis": "KNA", "Saint Lucia": "LCA", "Saint Vincent and the Grenadines": "VCT",
    "Samoa": "WSM", "San Marino": "SMR", "Sao Tome and Principe": "STP", "Saudi Arabia": "SAU",
    "Senegal": "SEN", "Serbia": "SRB", "Sierra Leone": "SLE", "Slovakia": "SVK", "Slovenia": "SVN",
    "Solomon Islands": "SLB", "Somalia": "SOM", "South Sudan": "SSD", "Spain": "ESP",
    "Sri Lanka": "LKA", "Sudan": "SDN", "Suriname": "SUR", "Tajikistan": "TJK", "Tanzania": "TZA",
    "Timor-Leste": "TLS", "Togo": "TGO", "Tonga": "TON", "Trinidad and Tobago": "TTO",
    "Tunisia": "TUN", "Turkmenistan": "TKM", "Tuvalu": "TUV", "Uganda": "UGA", "Ukraine": "UKR",
    "United Arab Emirates": "ARE", "Uruguay": "URY", "Uzbekistan": "UZB", "Vanuatu": "VUT",
    "Vatican City": "VAT", "Yemen": "YEM", "Zambia": "ZMB", "Zimbabwe": "ZWE"
}

BASE_STATE_REGULATORS = {
    "New York": ["NYDFS", "BitLicense"],
    "California": ["DFPI", "California Department of Financial Protection and Innovation"],
    "Texas": ["Texas Department of Banking", "Texas State Securities Board"],
    "Florida": ["Florida Office of Financial Regulation"],
    "Illinois": ["Illinois Department of Financial and Professional Regulation"],
    "Massachusetts": ["Massachusetts Securities Division"],
    "New Jersey": ["New Jersey Bureau of Securities"],
    "Washington": ["Washington Department of Financial Institutions"],
    "Pennsylvania": ["Pennsylvania Department of Banking and Securities"],
    "Georgia": ["Georgia Department of Banking and Finance"],
    "Michigan": ["Michigan Department of Insurance and Financial Services"],
    "Ohio": ["Ohio Division of Securities"],
    "Virginia": ["Virginia State Corporation Commission"],
    "North Carolina": ["North Carolina Department of the Secretary of State Securities Division"],
    "Colorado": ["Colorado Division of Securities"],
    "Minnesota": ["Minnesota Department of Commerce"],
    "Missouri": ["Missouri Securities Division"],
    "Arizona": ["Arizona Corporation Commission Securities Division"],
    "Indiana": ["Indiana Securities Division"],
    "Oregon": ["Oregon Division of Financial Regulation"],
    "Tennessee": ["Tennessee Department of Commerce and Insurance"],
    "Wisconsin": ["Wisconsin Department of Financial Institutions"],
    "Nevada": ["Nevada Secretary of State Securities Division"],
    "Louisiana": ["Louisiana Office of Financial Institutions"],
    "Kentucky": ["Kentucky Department of Financial Institutions"],
    "Oklahoma": ["Oklahoma Department of Securities"],
    "South Carolina": ["South Carolina Attorney General Securities Division"],
    "Alabama": ["Alabama Securities Commission"],
    "Mississippi": ["Mississippi Secretary of State Securities Division"],
    "Arkansas": ["Arkansas Securities Department"],
    "New Mexico": ["New Mexico Regulation and Licensing Department"],
    "Utah": ["Utah Division of Securities"],
    "Iowa": ["Iowa Insurance Division"],
    "Kansas": ["Kansas Securities Commissioner"],
    "Nebraska": ["Nebraska Department of Banking and Finance"],
    "Idaho": ["Idaho Department of Finance"],
    "Maine": ["Maine Office of Securities"],
    "New Hampshire": ["New Hampshire Bureau of Securities Regulation"],
    "Vermont": ["Vermont Department of Financial Regulation"],
    "Rhode Island": ["Rhode Island Department of Business Regulation"],
    "Delaware": ["Delaware Investor Protection Unit"],
    "Montana": ["Montana Securities Department"],
    "North Dakota": ["North Dakota Securities Department"],
    "South Dakota": ["South Dakota Division of Insurance Securities Regulation"],
    "Alaska": ["Alaska Division of Banking and Securities"],
    "Hawaii": ["Hawaii Department of Commerce and Consumer Affairs"],
    "Wyoming": ["Wyoming Secretary of State Securities Division"],
    "West Virginia": ["West Virginia Securities Commission"]
}

# Blockchain metrics for technical feasibility validation
BLOCKCHAIN_METRICS = {
    "tps": {"bitcoin": 7, "ethereum": 15, "solana": 65000, "cardano": 1000, "polkadot": 1000},
    "latency": {"bitcoin": 600, "ethereum": 12, "solana": 0.4, "cardano": 20, "polkadot": 6},
    "energy_per_tx": {"bitcoin": 700, "ethereum": 0.03, "solana": 0.0001, "cardano": 0.0005, "polkadot": 0.001}
}

URL_PATTERN = re.compile(r'(https?://[^\s]+|www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')

# Scraping sources with U.S. bias
SCRAPING_SOURCES = [
    {"name": "SEC", "url": "https://www.sec.gov/news/pressreleases", "selector": ".field-content"},
    {"name": "CFTC", "url": "https://www.cftc.gov/PressRoom/PressReleases", "selector": ".views-row"},
    {"name": "FinCEN", "url": "https://www.fincen.gov/news-room/press-releases", "selector": ".views-row"},
    {"name": "NYDFS", "url": "https://www.dfs.ny.gov/news_and_media/press_releases", "selector": "article"},
    {"name": "CoinDesk", "url": "https://www.coindesk.com", "selector": "article"},
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com", "selector": ".post-card"},
    {"name": "TheBlock", "url": "https://www.theblock.co", "selector": ".article"},
    {"name": "ESMA", "url": "https://www.esma.europa.eu/press-news/esma-news", "selector": ".news-item"},
    {"name": "FCA", "url": "https://www.fca.org.uk/news", "selector": ".news-item"},
    {"name": "MAS", "url": "https://www.mas.gov.sg/news", "selector": ".news-item"}
]

# Local cache for scraped content
SCRAPE_CACHE_FILE = "scrape_cache.json"
SCRAPE_CACHE = {}

def load_scrape_cache():
    global SCRAPE_CACHE
    if os.path.exists(SCRAPE_CACHE_FILE):
        try:
            with open(SCRAPE_CACHE_FILE, "r", encoding="utf-8") as f:
                SCRAPE_CACHE = json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load scrape cache: {e}")

def save_scrape_cache():
    try:
        with open(SCRAPE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(SCRAPE_CACHE, f, indent=4)
    except Exception as e:
        logging.warning(f"Failed to save scrape cache: {e}")

def clear_scrape_cache():
    global SCRAPE_CACHE
    SCRAPE_CACHE = {}
    if os.path.exists(SCRAPE_CACHE_FILE):
        os.remove(SCRAPE_CACHE_FILE)
    logging.info("Scrape cache cleared")

clear_scrape_cache()

async def scrape_web_content_async(url, selector, max_articles=5, retries=4, use_js_rendering=False):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in SCRAPE_CACHE:
        logging.info(f"Using cached content for {url}")
        return SCRAPE_CACHE[cache_key]
    
    articles_fetched = 0
    if use_js_rendering:
        try:
            session = HTMLSession()
            response = session.get(url)
            response.html.render(timeout=10, sleep=1)
            html = response.html.html
            session.close()
        except Exception as e:
            logging.error(f"JS rendering failed for {url}: {e}")
            html = None
    else:
        async with aiohttp.ClientSession() as session:
            for attempt in range(retries):
                try:
                    async with session.get(url, headers=headers, timeout=7) as response:
                        if response.status != 200:
                            logging.error(f"HTTP {response.status} for {url}")
                            raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status)
                        html = await response.text()
                        break
                except Exception as e:
                    logging.error(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2 ** attempt * 1.5)
                    else:
                        html = None

    if not html:
        if "sec.gov" in url:
            try:
                edgar = get_edgar_client()
                filings = edgar.get_company_filings(form="8-K", limit=5)
                content = [{"text": f["title"], "url": url} for f in filings.get("filings", [])[:max_articles]]
                articles_fetched = len(content)
                SCRAPE_CACHE[cache_key] = content
                save_scrape_cache()
                logging.info(f"Fetched {articles_fetched} articles via SEC EDGAR API")
                return content
            except Exception as e:
                logging.error(f"SEC EDGAR API failed: {e}")
                SCRAPE_CACHE[cache_key] = []
                save_scrape_cache()
                return []
        SCRAPE_CACHE[cache_key] = []
        save_scrape_cache()
        logging.info(f"Fetched 0 articles for {url}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.select(selector)
    if not articles:
        fallback_selectors = ['article', 'div[class*="news"]', 'div[class*="story"]', 'section', 'p']
        for fallback in fallback_selectors:
            articles = soup.select(fallback)
            if articles:
                break
        if not articles:
            nlp = get_spacy_model()
            doc = nlp(soup.get_text())
            for sent in doc.sents:
                if any(term in sent.text.lower() for term in ["news", "article", "press release", "crypto"]):
                    parent = sent._.parent
                    articles = parent.find_all(["article", "div", "section"])[:max_articles]
                    break
    content = []
    for article in articles[:max_articles]:
        text = article.get_text(strip=True)
        if len(text) < 50:
            continue
        link = article.find('a', href=True)
        full_url = urljoin(url, link['href']) if link else url
        content.append({"text": text, "url": full_url})
        articles_fetched += 1
    if not content:
        body = soup.find('body')
        if body:
            text = body.get_text(strip=True)[:1000]
            if len(text) >= 50:
                content.append({"text": text, "url": url})
                articles_fetched += 1
    
    SCRAPE_CACHE[cache_key] = content
    save_scrape_cache()
    logging.info(f"Fetched {articles_fetched} articles for {url}")
    return content

def scrape_web_content(url, selector, max_articles=5, use_js_rendering=False):
    return asyncio.run(scrape_web_content_async(url, selector, max_articles, use_js_rendering=use_js_rendering))

def extract_cik(text, company_name=None):
    nlp = get_spacy_model()
    doc = nlp(text)
    ciks = []
    for ent in doc.ents:
        if ent.label_ == "NORP" and ent.text.isdigit() and len(ent.text) == 10:
            ciks.append(ent.text)
    if not ciks:
        pattern = re.compile(r'\b\d{10}\b')
        ciks = pattern.findall(text)
    validated_ciks = []
    edgar = get_edgar_client()
    for cik in ciks:
        try:
            company_info = edgar.get_company_info(cik=cik)
            if company_info and (not company_name or fuzz.ratio(company_name.lower(), company_info["name"].lower()) > 80):
                validated_ciks.append(cik)
        except Exception as e:
            logging.warning(f"CIK {cik} validation failed: {e}")
    return validated_ciks

# Initialize global variables
DYNAMIC_WEIGHTS = None
LAST_UPDATE = None
TERM_CLUSTERS = None

def fetch_dynamic_risk_scores(text, regions, tokenomics_flags, is_whitepaper=False):
    now = datetime.now()
    global DYNAMIC_WEIGHTS, LAST_UPDATE, TERM_CLUSTERS
    if LAST_UPDATE and (now - LAST_UPDATE) < timedelta(hours=12):
        return DYNAMIC_WEIGHTS

    model = get_sentence_transformer()
    dynamic_weights = {
        "state_regulators": BASE_STATE_REGULATORS.copy(),
        "risk_categories": {cat: {} for cat in BASE_RISK_CATEGORIES.keys()},
        "region_terms": {acronym: 0.0 for acronym in REGION_ACRONYMS.values()}
    }

    def cluster_terms(terms, embeddings):
        if not terms or len(terms) < 2:
            return {term: [term] for term in terms}
        db = DBSCAN(eps=0.3, min_samples=2, metric="cosine").fit(embeddings)
        clusters = {}
        for idx, label in enumerate(db.labels_):
            if label == -1:
                clusters[terms[idx]] = [terms[idx]]
            else:
                cluster_name = f"cluster_{label}"
                if cluster_name not in clusters:
                    clusters[cluster_name] = []
                clusters[cluster_name].append(terms[idx])
        return clusters

    # Precompute term clusters
    all_terms = list(set.union(*[terms for terms in BASE_RISK_CATEGORIES.values()]) | WHITEPAPER_TERMS)
    term_embeddings = model.encode(all_terms, batch_size=32)
    TERM_CLUSTERS = cluster_terms(all_terms, term_embeddings)

    async def fetch_news_async():
        news_data = []
        risk_mentions = {}
        sentiment_scores = []
        for source in SCRAPING_SOURCES:
            use_js = source["name"] in ["CoinDesk", "CoinTelegraph", "TheBlock"]
            articles = await scrape_web_content_async(source["url"], source["selector"], max_articles=5, use_js_rendering=use_js)
            for article in articles:
                text = article["text"].lower()[:512]
                news_data.append(text)
                sentiment = get_sentiment_analyzer()(text)[0]
                sentiment_score = 1.0 if sentiment["label"] == "POSITIVE" else -1.0
                sentiment_scores.append(sentiment_score * sentiment["score"])
                text_embedding = model.encode(text)
                similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
                for term, sim in zip(all_terms, similarities):
                    if sim > 0.2:
                        for cluster_key, clustered_terms in TERM_CLUSTERS.items():
                            if term in clustered_terms:
                                for cluster_term in clustered_terms:
                                    risk_mentions[cluster_term] = risk_mentions.get(cluster_term, 0) + sim
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
        return risk_mentions, avg_sentiment, news_data

    async def fetch_sanctions_async():
        region_scores = {}
        sanctions_url = "https://www.treasury.gov/resource-center/sanctions/SDN-List/Pages/default.aspx"
        articles = await scrape_web_content_async(sanctions_url, "div[class*='sanctions']", 5)
        region_embeddings = model.encode([region.lower() for region in REGION_ACRONYMS], batch_size=32)
        for idx, (region, acronym) in enumerate(REGION_ACRONYMS.items()):
            score = 0.0
            for article in articles:
                text = article["text"].lower()[:512]
                text_embedding = model.encode(text)
                sim = util.cos_sim(text_embedding, region_embeddings[idx]).numpy()[0][0]
                if sim > 0.2:
                    score += sim * (2.0 if acronym.startswith("USA") else 1.0)
            region_scores[acronym] = min(10.0, score * 0.5)
        return region_scores

    async def fetch_market_async():
        market_url = "https://www.coindesk.com/markets"
        articles = await scrape_web_content_async(market_url, "div[class*='article']", 5, use_js_rendering=True)
        volatility = 0.3
        volatility_embedding = model.encode("market volatility crypto")
        for article in articles:
            text = article["text"].lower()[:512]
            text_embedding = model.encode(text)
            sim = util.cos_sim(text_embedding, volatility_embedding).numpy()[0][0]
            if sim > 0.2:
                volatility += sim * 0.15
        return volatility

    async def fetch_cyber_threats_async():
        cyber_url = "https://www.theblock.co/category/security"
        articles = await scrape_web_content_async(cyber_url, "article", 5)
        threat_score = 0.3
        threat_embedding = model.encode("crypto cyber threat hack")
        for article in articles:
            text = article["text"].lower()[:512]
            text_embedding = model.encode(text)
            sim = util.cos_sim(text_embedding, threat_embedding).numpy()[0][0]
            if sim > 0.2:
                threat_score += sim * 0.4
        return threat_score

    async def fetch_regulatory_async():
        regulatory_score = 0.3
        regulatory_embedding = model.encode("crypto regulatory action compliance")
        for source in SCRAPING_SOURCES:
            if source["name"] in ["SEC", "CFTC", "FinCEN"]:
                articles = await scrape_web_content_async(source["url"], source["selector"], 5)
                for article in articles:
                    text = article["text"].lower()[:512]
                    text_embedding = model.encode(text)
                    sim = util.cos_sim(text_embedding, regulatory_embedding).numpy()[0][0]
                    if sim > 0.2:
                        regulatory_score += sim * (0.6 if source["name"] in ["SEC", "FinCEN"] else 0.3)
        return regulatory_score

    async def fetch_github_analysis(url):
        if not url.startswith("https://github.com"):
            return {}
        articles = await scrape_web_content_async(url, "div[class*='repo']", 1)
        if not articles:
            return {}
        repo_data = articles[0]
        commits = re.search(r'(\d+)\s+commit', repo_data["text"].lower())
        issues = re.search(r'(\d+)\s+issue', repo_data["text"].lower())
        audit = "audit" in repo_data["text"].lower()
        score = 0.3
        if commits and int(commits.group(1)) < 10:
            score += 2.0
        if issues and int(issues.group(1)) > 5:
            score += 2.5
        if not audit:
            score += 3.0
        return {"github_risk": score}

    async def analyze_whitepaper(text):
        issues = {}
        text_lower = text.lower()
        model = get_sentence_transformer()
        whitepaper_terms = list(WHITEPAPER_TERMS)
        term_embeddings = model.encode(whitepaper_terms, batch_size=32)
        text_embedding = model.encode(text_lower[:512])
        similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
        for term, sim in zip(whitepaper_terms, similarities):
            if sim > 0.2:
                weight = 3.0 if term in [
                    "unsustainable tokenomics", "opaque allocation", "centralized control",
                    "whitepaper fraud", "rug pull risk", "unrealistic yield"
                ] else 2.0
                for cluster_key, clustered_terms in TERM_CLUSTERS.items():
                    if term in clustered_terms:
                        for cluster_term in clustered_terms:
                            issues[cluster_term] = sim * weight
        staking_yield = re.search(r'staking yield.*?(\d+\.?\d*%)', text_lower)
        if staking_yield and float(staking_yield.group(1).strip('%')) > 50:
            issues["excessive staking yield"] = 3.0
        vesting = re.search(r'vesting.*?(\d+\s*(?:month|year))', text_lower)
        if vesting and int(vesting.group(1).split()[0]) < 6:
            issues["short vesting period"] = 2.5
        tps = re.search(r'transactions per second.*?(\d+)', text_lower)
        if tps and int(tps.group(1)) > max(BLOCKCHAIN_METRICS["tps"].values()) * 2:
            issues["unrealistic TPS"] = 2.5
        latency = re.search(r'latency.*?(\d+\.?\d*)\s*(?:second|ms)', text_lower)
        if latency and float(latency.group(1)) < min(BLOCKCHAIN_METRICS["latency"].values()) / 2:
            issues["unrealistic latency"] = 2.5
        revenue = re.search(r'revenue.*?\$?(\d+\.?\d*)\s*(?:million|billion)', text_lower)
        burn_rate = re.search(r'burn rate.*?\$?(\d+\.?\d*)\s*(?:million|billion)', text_lower)
        if revenue and burn_rate and float(burn_rate.group(1)) > float(revenue.group(1)) * 2:
            issues["unsustainable burn rate"] = 3.0
        text_hash = hashlib.sha256(text_lower.encode()).hexdigest()
        known_hashes = []
        if text_hash in known_hashes:
            issues["potential plagiarism"] = 4.0
        if "decentralized control" in issues and "centralized control" in issues:
            issues["governance inconsistency"] = 3.0
        roadmap_embedding = model.encode("clear roadmap and milestones")
        sim = util.cos_sim(text_embedding, roadmap_embedding).numpy()[0][0]
        if sim < 0.2:
            issues["unclear roadmap"] = 2.5
        return issues

    async def fetch_all():
        tasks = [
            fetch_news_async(),
            fetch_sanctions_async(),
            fetch_market_async(),
            fetch_cyber_threats_async(),
            fetch_regulatory_async()
        ]
        if "github.com" in text.lower():
            tasks.append(fetch_github_analysis(text.lower()))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    results = asyncio.run(fetch_all())
    news_data = results[0] if not isinstance(results[0], Exception) else ({}, 0.0, [])
    sanctions_data = results[1] if not isinstance(results[1], Exception) else {}
    market_volatility = results[2] if not isinstance(results[2], Exception) else 0.3
    cyber_score = results[3] if not isinstance(results[3], Exception) else 0.3
    regulatory_score = results[4] if not isinstance(results[4], Exception) else 0.3
    github_data = results[5] if len(results) > 5 and not isinstance(results[5], Exception) else {}

    risk_mentions, avg_sentiment, news_texts = news_data
    for cat, terms in BASE_RISK_CATEGORIES.items():
        for term in terms:
            count = risk_mentions.get(term, 0)
            dynamic_weights["risk_categories"][cat][term] = count * (1.2 if cat == "legal_regulatory" else 0.8)
        if not dynamic_weights["risk_categories"][cat]:
            dynamic_weights["risk_categories"][cat] = {term: 0.3 for term in terms}

    dynamic_weights["region_terms"].update(sanctions_data)
    for region in regions:
        region_acronym = REGION_ACRONYMS.get(region, region)
        if region_acronym in dynamic_weights["region_terms"]:
            dynamic_weights["region_terms"][region_acronym] += 5.0 if region_acronym.startswith("USA") else 4.0
        else:
            dynamic_weights["region_terms"][region_acronym] = 0.3

    for flag, severity in tokenomics_flags.items():
        dynamic_weights["risk_categories"]["market_risk"][flag] = severity * 4.0

    dynamic_weights["risk_categories"]["market_risk"]["volatility"] = market_volatility * 8.0
    dynamic_weights["risk_categories"]["cyber_resilience"]["cyber_threats"] = cyber_score * 3.0
    dynamic_weights["risk_categories"]["legal_regulatory"]["regulatory_activity"] = regulatory_score * 3.0
    dynamic_weights["risk_categories"]["general_operational"].update(github_data)

    if is_whitepaper:
        whitepaper_issues = analyze_whitepaper(text)
        for issue, score in whitepaper_issues.items():
            dynamic_weights["risk_categories"]["whitepaper_risk"][issue] = score

    scaler = StandardScaler()
    for cat in dynamic_weights["risk_categories"]:
        scores = list(dynamic_weights["risk_categories"][cat].values())
        if scores:
            scaled_scores = scaler.fit_transform(np.array(scores).reshape(-1, 1)).flatten()
            dynamic_weights["risk_categories"][cat] = {
                k: min(10.0, max(0.0, v)) for k, v in zip(
                    dynamic_weights["risk_categories"][cat].keys(), scaled_scores
                )
            }

    DYNAMIC_WEIGHTS = dynamic_weights
    LAST_UPDATE = now
    logging.info(f"Dynamic weights: {json.dumps(dynamic_weights, indent=2)}")
    return dynamic_weights

def extract_entities(text, source_type="whitepaper"):  # Assume whitepaper for PDFs
    if not text or len(text.strip()) < 10:
        logging.warning("Input text is empty or too short")
        return {
            "persons": [], "organizations": [], "locations": [], "products": [], "companies": [],
            "region": None, "ciks": [], "risk_score": {"raw_score": 0.5, "scaled_score": 0.1},
            "tokenomics_flags": {}
        }, text

    nlp = get_spacy_model()
    flair_tagger = get_flair_tagger()
    model = get_sentence_transformer()
    doc = nlp(text)
    sentence = Sentence(text)
    flair_tagger.predict(sentence)

    entities = {
        "persons": [], "organizations": [], "locations": [], "products": [], "companies": [],
        "region": None, "ciks": [], "risk_score": {"raw_score": 0.0, "scaled_score": 0.0},
        "tokenomics_flags": {}
    }

    anonymized_text = text
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "ORG"]:
            anonymized_text = anonymized_text.replace(ent.text, f"[REDACTED_{ent.label_}]")
    for match in phonenumbers.PhoneNumberMatcher(text, "US"):
        phone = match.number.national_number
        anonymized_text = anonymized_text.replace(phone, "[REDACTED_PHONE]")
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    for email in email_pattern.findall(text):
        anonymized_text = anonymized_text.replace(email, "[REDACTED_EMAIL]")

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["persons"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["organizations"].append(ent.text)
        elif ent.label_ == "GPE":
            entities["locations"].append(ent.text)
            region_embedding = model.encode(ent.text.lower())
            max_sim = 0.0
            best_region = ent.text
            for region in REGION_ACRONYMS:
                reg_embedding = model.encode(region.lower())
                sim = util.cos_sim(region_embedding, reg_embedding).numpy()[0][0]
                if sim > 0.2:
                    max_sim = sim
                    best_region = REGION_ACRONYMS[region]
            entities["region"] = best_region
        elif ent.label_ == "PRODUCT":
            entities["products"].append(ent.text)

    for ent in sentence.get_spans("ner"):
        if ent.tag == "ORG":
            entities["companies"].append(ent.text)

    addresses = pyap.parse(text, country="US")
    if addresses:
        entities["locations"].extend([str(addr) for addr in addresses])

    for match in phonenumbers.PhoneNumberMatcher(text, "US"):
        entities["products"].append(match.number.national_number)

    for email in email_pattern.findall(text):
        try:
            validate_email(email, check_deliverability=False)
            entities["products"].append(email)
        except EmailNotValidError:
            pass

    entities["ciks"] = extract_cik(text, entities["organizations"][0] if entities["organizations"] else None)

    tokenomics_issues = list(WHITEPAPER_TERMS)
    text_embedding = model.encode(text.lower()[:512], batch_size=32)
    term_embeddings = model.encode(tokenomics_issues, batch_size=32)
    similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
    for term, sim in zip(tokenomics_issues, similarities):
        if sim > 0.2 and term in [
            "unsustainable tokenomics", "opaque allocation", "centralized control",
            "unrealistic yield", "excessive minting", "unverified burn"
        ]:
            for cluster_key, clustered_terms in TERM_CLUSTERS.items():
                if term in clustered_terms:
                    for cluster_term in clustered_terms:
                        entities["tokenomics_flags"][cluster_term] = sim

    is_whitepaper = source_type == "whitepaper"
    dynamic_weights = fetch_dynamic_risk_scores(
        text, entities["locations"], entities["tokenomics_flags"], is_whitepaper
    )

    raw_score = 0.0
    score_components = []
    text_embedding = model.encode(text.lower()[:512], batch_size=32)
    crypto_density = sum(1 for term in CRYPTO_TERMS if term.lower() in text.lower()) / max(1, len(text.split()))
    baseline_score = max(0.5, crypto_density * 7.0)
    raw_score += baseline_score
    score_components.append(f"baseline.crypto_density: {baseline_score:.2f}")
    all_terms = list(set.union(*[terms for terms in BASE_RISK_CATEGORIES.values()]) | WHITEPAPER_TERMS)
    similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
    for term, sim in zip(all_terms, similarities):
        if sim > 0.2:
            for cat, terms in BASE_RISK_CATEGORIES.items():
                if term in terms:
                    score = dynamic_weights["risk_categories"][cat].get(term, 0.3)
                    contribution = score * sim * (2.5 if cat == "legal_regulatory" and term in REGULATIONS else 2.0)
                    raw_score += contribution
                    score_components.append(f"{cat}.{term}: {contribution:.2f}")
                    break

    for region in entities["locations"]:
        region_acronym = REGION_ACRONYMS.get(region, entities["region"])
        if region_acronym in dynamic_weights["region_terms"]:
            contribution = dynamic_weights["region_terms"][region_acronym]
            raw_score += contribution
            score_components.append(f"region.{region_acronym}: {contribution:.2f}")

    for flag, severity in entities["tokenomics_flags"].items():
        contribution = severity * 4.0
        raw_score += contribution
        score_components.append(f"tokenomics.{flag}: {contribution:.2f}")

    for term in HYPE_RED_FLAGS:
        term_embedding = model.encode(term.lower())
        sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
        if sim > 0.2:
            contribution = sim * 2.5
            raw_score += contribution
            score_components.append(f"hype.{term}: {contribution:.2f}")

    for term in VAGUE_TERMS:
        term_embedding = model.encode(term.lower())
        sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
        if sim > 0.2:
            contribution = sim * 0.8
            raw_score += contribution
            score_components.append(f"vague.{term}: {contribution:.2f}")

    for term in MITIGATION_TERMS:
        term_embedding = model.encode(term.lower())
        sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
        if sim > 0.2:
            contribution = -sim * 2.0
            raw_score += contribution
            score_components.append(f"mitigation.{term}: {contribution:.2f}")

    if is_whitepaper:
        whitepaper_issues = dynamic_weights["risk_categories"].get("whitepaper_risk", {})
        for issue, score in whitepaper_issues.items():
            raw_score += score
            score_components.append(f"whitepaper.{issue}: {score:.2f}")
        for person in entities["persons"]:
            sanction_articles =  scrape_web_content_async(
                "https://www.treasury.gov/resource-center/sanctions/SDN-List/Pages/default.aspx", "div[class*='sanctions']", 1
            )
            if sanction_articles and person.lower() in sanction_articles[0]["text"].lower():
                contribution = 6.0
                raw_score += contribution
                score_components.append(f"sanction.{person}: {contribution:.2f}")
        tech_terms = ["infinite scalability", "zero latency", "quantum resistance", "unhackable"]
        for term in tech_terms:
            term_embedding = model.encode(term.lower())
            sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
            if sim > 0.2:
                contribution = sim * 2.5
                raw_score += contribution
                score_components.append(f"tech.{term}: {contribution:.2f}")

    if raw_score < 0.5:
        raw_score = 0.5
        score_components.append("default: 0.5")

    entities["risk_score"]["raw_score"] = raw_score
    entities["risk_score"]["scaled_score"] = min(10.0, max(0.0, raw_score / 5.0))
    logging.info(f"Risk score components: {score_components}")
    return entities, anonymized_text

def analyze_sentiment(text):
    analyzer = get_sentiment_analyzer()
    result = analyzer(text[:512])[0]
    sentiment = "positive" if result["label"] == "POSITIVE" else "negative"
    return {
        "sentiment": sentiment,
        "sentiment_score": result["score"] if sentiment == "positive" else -result["score"]
    }

def optimize_thresholds(embeddings, initial_eps, initial_threshold):
    if len(embeddings) < 2:
        return initial_eps, initial_threshold
    cos_sim = util.cos_sim(embeddings, embeddings).numpy()
    np.fill_diagonal(cos_sim, 0)
    avg_sim = np.mean(cos_sim[cos_sim > 0])
    optimized_eps = initial_eps * (1 - avg_sim)
    optimized_threshold = initial_threshold * (1 - avg_sim)
    return max(0.1, optimized_eps), max(0.1, optimized_threshold)