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
import requests
import numpy as np
from sklearn.preprocessing import StandardScaler
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import hashlib
import time
from itertools import cycle

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_sentence_transformer():
    return SentenceTransformer("all-MiniLM-L6-v2")

def get_spacy_model():
    return spacy.load("en_core_web_trf")

def get_flair_tagger():
    return SequenceTagger.load("flair/ner-english-large")

def get_sentiment_analyzer():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def get_edgar_client():
    return EdgarClient(user_agent="CryptoDueDiligence/1.0")

lemmatizer = WordNetLemmatizer()


# ======================
# Proxy Configuration
# ======================
class ProxyManager:
    def __init__(self):
        self.proxy_cycle = cycle([
            "http://51.158.68.68:8811",
            "http://138.197.157.32:8080",
            "https://45.77.136.215:3128",
            "http://209.97.150.167:3128",
            "socks5://45.76.176.218:1080"
        ])
        self.blacklist = set()
        self.timeout = 5
        self.max_retries = 2

    def get_next_proxy(self):
        while True:
            proxy = next(self.proxy_cycle)
            if proxy not in self.blacklist:
                return proxy

    def mark_failed(self, proxy):
        self.blacklist.add(proxy)
        logging.warning(f"Proxy blacklisted: {proxy}")

    def test_proxy(self, proxy):
        test_urls = [
        "http://httpbin.org/ip",  # Returns your IP
        "http://example.com",      # Standard test
        "http://google.com/favicon.ico"  # Small file
        ]
    
        for test_url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(
                    test_url,
                    proxies={"http": proxy, "https": proxy},
                    timeout=self.timeout
                )
                response_time = time.time() - start_time
            
            # Validate response
                if response.status_code == 200:
                    if test_url == "http://httpbin.org/ip":
                    # Verify proxy is actually changing our IP
                        origin_ip = response.json().get('origin', '')
                        if not origin_ip or origin_ip == requests.get("http://httpbin.org/ip").json().get('origin', ''):
                            return False
                
                # Acceptable response time threshold (2 seconds)
                    if response_time < 2.0:
                        logging.info(f"Proxy {proxy} verified (response: {response_time:.2f}s)")
                        return True
                
            except Exception as e:
                logging.debug(f"Proxy test failed on {test_url}: {str(e)}")
                continue
    
        return False

proxy_manager = ProxyManager()

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

# Proxy Pool for scraping
PROXY_POOL = [
    "http://103.152.112.162:80",
    "socks5://45.94.47.66:8110",
    "http://154.202.123.172:3128",
    "socks4://198.44.255.3:80",
    "http://72.206.181.97:80",
    "socks5://192.111.139.163:4145",
    "http://38.154.227.167:5868",
    "socks4://184.178.172.5:1530"
]

DYNAMIC_WEIGHTS = {
    "state_regulators": BASE_STATE_REGULATORS.copy(),
    "risk_categories": {cat: {} for cat in BASE_RISK_CATEGORIES.keys()},
    "region_terms": {acronym: 0.0 for acronym in REGION_ACRONYMS.values()},
}
LAST_UPDATE = None

def scrape_web_content(url, selector, max_articles=10, use_selenium=False):
    try:
        if use_selenium:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            time.sleep(2)  # Wait for dynamic content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
        else:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            proxies = {"http": np.random.choice(PROXY_POOL)} if PROXY_POOL else None
            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

        # Dynamic selector detection if static selector fails
        articles = soup.select(selector)
        if not articles:
            nlp = get_spacy_model()
            doc = nlp(soup.get_text())
            for sent in doc.sents:
                if any(term in sent.text.lower() for term in ["news", "article", "press release"]):
                    parent = sent._.parent
                    articles = parent.find_all(["article", "div", "section"])[:max_articles]
                    break

        content = []
        for article in articles[:max_articles]:
            text = article.get_text(strip=True)
            link = article.find('a', href=True)
            full_url = urljoin(url, link['href']) if link else url
            content.append({"text": text, "url": full_url})
        return content
    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        return [] if not use_selenium else scrape_web_content(url, selector, max_articles, True)

def extract_cik(text, company_name=None):
    nlp = get_spacy_model()
    doc = nlp(text)
    ciks = []
    for ent in doc.ents:
        if ent.label_ == "NORP" and ent.text.isdigit() and len(ent.text) == 10:
            ciks.append(ent.text)

    if not ciks:
        # Fallback to regex if NLP fails
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

def fetch_dynamic_risk_scores(text, regions, tokenomics_flags, is_whitepaper=False):
    now = datetime.now()
    global DYNAMIC_WEIGHTS, LAST_UPDATE
    if LAST_UPDATE and (now - LAST_UPDATE) < timedelta(hours=12):
        return DYNAMIC_WEIGHTS

    model = get_sentence_transformer()
    dynamic_weights = {
        "state_regulators": BASE_STATE_REGULATORS.copy(),
        "risk_categories": {cat: {} for cat in BASE_RISK_CATEGORIES.keys()},
        "region_terms": {acronym: 0.0 for acronym in REGION_ACRONYMS.values()}
    }

    def fetch_news():
        news_data = []
        risk_mentions = {}
        sentiment_scores = []
        all_terms = []
        for cat, terms in BASE_RISK_CATEGORIES.items():
            all_terms.extend(terms)
        term_embeddings = model.encode(all_terms)
        for source in SCRAPING_SOURCES:
            articles = scrape_web_content(source["url"], source["selector"], use_selenium=source["name"] in ["SEC", "FinCEN"])
            for article in articles:
                text = article["text"].lower()
                news_data.append(text)
                sentiment = get_sentiment_analyzer()(text)[0]
                sentiment_score = 1.0 if sentiment["label"] == "POSITIVE" else -1.0
                sentiment_scores.append(sentiment_score * sentiment["score"])
                text_embedding = model.encode(text)
                similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
                for term, sim in zip(all_terms, similarities):
                    if sim > 0.7:
                        risk_mentions[term] = risk_mentions.get(term, 0) + sim
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
        return risk_mentions, avg_sentiment, news_data

    def fetch_sanctions():
        region_scores = {}
        sanctions_url = "https://www.treasury.gov/resource-center/sanctions/SDN-List/Pages/default.aspx"
        articles = scrape_web_content(sanctions_url, "div", max_articles=5, use_selenium=True)
        for region, acronym in REGION_ACRONYMS.items():
            score = 0.0
            for article in articles:
                text_embedding = model.encode(article["text"].lower())
                region_embedding = model.encode(region.lower())
                sim = util.cos_sim(text_embedding, region_embedding).numpy()[0][0]
                if sim > 0.7:
                    score += sim * (2.0 if acronym.startswith("USA") else 1.0)
            region_scores[acronym] = min(10.0, score * 0.5)
        return region_scores

    def fetch_market():
        market_url = "https://www.coindesk.com/markets"
        articles = scrape_web_content(market_url, "article")
        volatility = 0.1
        for article in articles:
            text_embedding = model.encode(article["text"].lower())
            volatility_embedding = model.encode("market volatility")
            sim = util.cos_sim(text_embedding, volatility_embedding).numpy()[0][0]
            if sim > 0.7:
                volatility += sim * 0.05
        return volatility

    def fetch_cyber_threats():
        cyber_url = "https://www.theblock.co/category/security"
        articles = scrape_web_content(cyber_url, "article")
        threat_score = 0.0
        for article in articles:
            text_embedding = model.encode(article["text"].lower())
            threat_embedding = model.encode("cyber threat")
            sim = util.cos_sim(text_embedding, threat_embedding).numpy()[0][0]
            if sim > 0.7:
                threat_score += sim * 0.2
        return threat_score

    def fetch_regulatory():
        regulatory_score = 0.0
        for source in SCRAPING_SOURCES:
            if source["name"] in ["SEC", "CFTC", "FinCEN", "NYDFS"]:
                articles = scrape_web_content(source["url"], source["selector"], use_selenium=True)
                for article in articles:
                    text_embedding = model.encode(article["text"].lower())
                    regulatory_embedding = model.encode("regulatory action")
                    sim = util.cos_sim(text_embedding, regulatory_embedding).numpy()[0][0]
                    if sim > 0.7:
                        regulatory_score += sim * (0.3 if source["name"] in ["SEC", "FinCEN"] else 0.15)
        return regulatory_score

    def analyze_whitepaper(text):
        issues = {}
        text_lower = text.lower()
        model = get_sentence_transformer()
        whitepaper_terms = list(WHITEPAPER_TERMS)
        term_embeddings = model.encode(whitepaper_terms)
        text_embedding = model.encode(text_lower)
        similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
        for term, sim in zip(whitepaper_terms, similarities):
            if sim > 0.7:
                weight = 2.0 if term in [
                    "unsustainable tokenomics", "opaque allocation", "centralized control",
                    "whitepaper fraud", "rug pull risk", "unrealistic yield"
                ] else 1.0
                issues[term] = sim * weight

        # Tokenomics validation
        staking_yield = re.search(r'staking yield.*?(\d+\.?\d*%)', text_lower)
        if staking_yield and float(staking_yield.group(1).strip('%')) > 50:
            issues["excessive staking yield"] = 2.0
        vesting = re.search(r'vesting.*?(\d+\s*(?:month|year))', text_lower)
        if vesting and int(vesting.group(1).split()[0]) < 6:
            issues["short vesting period"] = 1.5

        # Technical feasibility
        tps = re.search(r'transactions per second.*?(\d+)', text_lower)
        if tps and int(tps.group(1)) > max(BLOCKCHAIN_METRICS["tps"].values()) * 2:
            issues["unrealistic TPS"] = 1.5
        latency = re.search(r'latency.*?(\d+\.?\d*)\s*(?:second|ms)', text_lower)
        if latency and float(latency.group(1)) < min(BLOCKCHAIN_METRICS["latency"].values()) / 2:
            issues["unrealistic latency"] = 1.5

        # Financial projections
        revenue = re.search(r'revenue.*?\$?(\d+\.?\d*)\s*(?:million|billion)', text_lower)
        burn_rate = re.search(r'burn rate.*?\$?(\d+\.?\d*)\s*(?:million|billion)', text_lower)
        if revenue and burn_rate and float(burn_rate.group(1)) > float(revenue.group(1)) * 2:
            issues["unsustainable burn rate"] = 2.0

        # Plagiarism detection
        text_hash = hashlib.sha256(text_lower.encode()).hexdigest()
        known_hashes = []  # Assume a database of known whitepaper hashes
        if text_hash in known_hashes:
            issues["potential plagiarism"] = 3.0

        # Governance inconsistencies
        if "decentralized control" in issues and "centralized control" in issues:
            issues["governance inconsistency"] = 2.0

        # Roadmap clarity
        roadmap_embedding = model.encode("clear roadmap and milestones")
        sim = util.cos_sim(text_embedding, roadmap_embedding).numpy()[0][0]
        if sim < 0.5:
            issues["unclear roadmap"] = 1.5

        return issues

    def fetch_github_analysis(url):
        if not url.startswith("https://github.com"):
            return {}
        try:
            repo_path = url.replace("https://github.com/", "")
            repo_data = scrape_web_content(url, "div", max_articles=1)
            commits = re.search(r'(\d+)\s+commit', repo_data[0]["text"].lower()) if repo_data else None
            issues = re.search(r'(\d+)\s+issue', repo_data[0]["text"].lower()) if repo_data else None
            audit = "audit" in repo_data[0]["text"].lower() if repo_data else False
            score = 0.0
            if commits and int(commits.group(1)) < 10:
                score += 1.0
            if issues and int(issues.group(1)) > 5:
                score += 1.5
            if not audit:
                score += 2.0
            return {"github_risk": score}
        except Exception as e:
            logging.error(f"GitHub analysis failed for {url}: {e}")
            return {}

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(fetch_news),
            executor.submit(fetch_sanctions),
            executor.submit(fetch_market),
            executor.submit(fetch_cyber_threats),
            executor.submit(fetch_regulatory),
            executor.submit(fetch_github_analysis, text.lower()) if "github.com" in text.lower() else None
        ]
        results = [future.result() for future in futures if future]
        news_data, sanctions_data, market_volatility, cyber_score, regulatory_score = results[:5]
        github_data = results[5] if len(results) > 5 else {}

    risk_mentions, avg_sentiment, news_texts = news_data
    for cat, terms in BASE_RISK_CATEGORIES.items():
        for term in terms:
            count = risk_mentions.get(term, 0)
            dynamic_weights["risk_categories"][cat][term] = count * (0.7 if cat == "legal_regulatory" else 0.5)

    dynamic_weights["region_terms"].update(sanctions_data)
    for region in regions:
        region_acronym = REGION_ACRONYMS.get(region, region)
        if region_acronym in dynamic_weights["region_terms"]:
            dynamic_weights["region_terms"][region_acronym] += 3.0 if region_acronym.startswith("USA") else 2.0

    for flag, severity in tokenomics_flags.items():
        dynamic_weights["risk_categories"]["market_risk"][flag] = severity * 2.0

    dynamic_weights["risk_categories"]["market_risk"]["volatility"] = market_volatility * 5.0
    dynamic_weights["risk_categories"]["cyber_resilience"]["cyber_threats"] = cyber_score
    dynamic_weights["risk_categories"]["legal_regulatory"]["regulatory_activity"] = regulatory_score
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
    return dynamic_weights

def extract_entities(text, source_type="text"):
    nlp = get_spacy_model()
    flair_tagger = get_flair_tagger()
    model = get_sentence_transformer()
    doc = nlp(text)
    sentence = Sentence(text)
    flair_tagger.predict(sentence)

    entities = {
        "persons": [],
        "organizations": [],
        "locations": [],
        "products": [],
        "companies": [],
        "region": None,
        "ciks": [],
        "risk_score": {"raw_score": 0.0, "scaled_score": 0.0},
        "tokenomics_flags": {}
    }

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
                if sim > max_sim and sim > 0.7:
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

    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    for email in email_pattern.findall(text):
        try:
            validate_email(email, check_deliverability=False)
            entities["products"].append(email)
        except EmailNotValidError:
            pass

    entities["ciks"] = extract_cik(text, entities["organizations"][0] if entities["organizations"] else None)

    tokenomics_issues = list(WHITEPAPER_TERMS)
    text_embedding = model.encode(text.lower())
    term_embeddings = model.encode(tokenomics_issues)
    similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
    for issue, sim in zip(tokenomics_issues, similarities):
        if sim > 0.7 and issue in [
            "unsustainable tokenomics", "opaque allocation", "centralized control",
            "unrealistic yield", "excessive minting", "unverified burn"
        ]:
            entities["tokenomics_flags"][issue] = sim

    is_whitepaper = source_type == "whitepaper"
    dynamic_weights = fetch_dynamic_risk_scores(
        text, entities["locations"], entities["tokenomics_flags"], is_whitepaper
    )

    raw_score = 0.0
    all_terms = []
    for cat, terms in BASE_RISK_CATEGORIES.items():
        all_terms.extend(terms)
    term_embeddings = model.encode(all_terms)
    text_embedding = model.encode(text.lower())
    similarities = util.cos_sim(text_embedding, term_embeddings).numpy()[0]
    for term, sim in zip(all_terms, similarities):
        if sim > 0.7:
            for cat, terms in BASE_RISK_CATEGORIES.items():
                if term in terms:
                    score = dynamic_weights["risk_categories"][cat].get(term, 0.0)
                    raw_score += score * sim * (1.5 if cat == "legal_regulatory" and term in REGULATIONS else 1.0)
                    break

    for region in entities["locations"]:
        region_acronym = REGION_ACRONYMS.get(region, entities["region"])
        if region_acronym in dynamic_weights["region_terms"]:
            raw_score += dynamic_weights["region_terms"][region_acronym]

    for flag, severity in entities["tokenomics_flags"].items():
        raw_score += severity * 2.0

    for term in HYPE_RED_FLAGS:
        term_embedding = model.encode(term.lower())
        sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
        if sim > 0.7:
            raw_score += sim * 1.5

    for term in VAGUE_TERMS:
        term_embedding = model.encode(term.lower())
        sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
        if sim > 0.7:
            raw_score += sim * 0.5

    for term in MITIGATION_TERMS:
        term_embedding = model.encode(term.lower())
        sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
        if sim > 0.7:
            raw_score -= sim * 1.0

    if is_whitepaper:
        whitepaper_issues = dynamic_weights["risk_categories"].get("whitepaper_risk", {})
        for issue, score in whitepaper_issues.items():
            raw_score += score
        for person in entities["persons"]:
            sanction_check = scrape_web_content(
                "https://www.treasury.gov/resource-center/sanctions/SDN-List/Pages/default.aspx", "div", 1, True
            )
            if sanction_check and person.lower() in sanction_check[0]["text"].lower():
                raw_score += 4.0
        tech_terms = ["infinite scalability", "zero latency", "quantum resistance"]
        for term in tech_terms:
            term_embedding = model.encode(term.lower())
            sim = util.cos_sim(text_embedding, term_embedding).numpy()[0][0]
            if sim > 0.7:
                raw_score += sim * 1.5

    entities["risk_score"]["raw_score"] = raw_score
    entities["risk_score"]["scaled_score"] = min(10.0, max(0.0, raw_score / 5.0))

    return entities

def analyze_sentiment(text):
    analyzer = get_sentiment_analyzer()
    result = analyzer(text)[0]
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


if __name__ == "__main__":
    # Test proxy functionality
    print("Testing proxy rotation...")
    for _ in range(5):
        proxy = proxy_manager.get_next_proxy()
        print(f"Using proxy: {proxy}")
        print(f"Proxy test: {'OK' if proxy_manager.test_proxy(proxy) else 'FAILED'}")