import spacy
from nltk.stem import WordNetLemmatizer
import nltk
import logging
from flair.data import Sentence
from flair.models import SequenceTagger
import pyap
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from sentence_transformers import SentenceTransformer, util
from sec_edgar_api import EdgarClient
from fuzzywuzzy import fuzz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

model = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("en_core_web_trf")
flair_tagger = SequenceTagger.load("flair/ner-english-large")
lemmatizer = WordNetLemmatizer()
sentiment_analyzer = SentimentIntensityAnalyzer()
edgar_client = EdgarClient(user_agent="CryptoDueDiligence/1.0")

# Term Sets (all preserved, with enhancements)
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
    # Added terms
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
    # Added terms
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
    # Added terms
    "layer 3", "rollups", "zk-rollup", "optimistic rollup", "state channel", "plasma", "crypto bridge hack"
}

RISK_TERMS = set()  # Kept empty as per original; risks are categorized below

ESG_TERMS = {
    "carbon footprint", "sustainability", "green energy", "ESG compliance", "social impact", "human rights",
    "corporate governance", "board diversity", "executive compensation", "shareholder rights", "ethical sourcing",
    "environmental violation", "social responsibility", "governance failure", "climate risk", "sustainable investing",
    "net zero", "CSR", "stakeholder engagement", "transparency", "mining energy consumption",
    "community governance failure", "energy inefficiency", "ecological impact", "decentralized governance dispute",
    "environmental damage", "labor violation", "ethical breach", "social unrest", "governance opacity",
    "ESG reporting failure", "carbon emissions", "renewable energy", "pollution risk", "resource depletion",
    "biodiversity loss", "ethical misconduct", "greenwashing", "social license risk", "community displacement",
    # Added terms
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
    "stack overflow", "format string attack", "race condition", "side-channel attack", "timing attack",
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
    # Added terms
    "crypto phishing", "wallet cloning", "smart contract overflow", "chain impersonation", "node spoofing"
}

RISK_CATEGORIES = {
    "legal_regulatory": {
        "regulatory compliance": 4.0, "compliance officer": 4.0, "due diligence": 4.0, 
        "regulatory reporting": 4.0, "tax compliance": 4.0, "licensing requirement": 4.0, 
        "compliance monitoring": 4.0, "compliance program": 4.0, "crypto licensing": 4.0, 
        "regulatory sandbox": 4.0, "regulatory whitelist": 4.0, "compliance certification": 4.0, 
        "jurisdictional alignment": 4.0,
        "SEC": 5.0, "CFTC": 5.0, "FINRA": 5.0, "AML": 5.0, "KYC": 5.0, "FATCA": 5.0, "OFAC": 5.0, 
        "FINCEN": 5.0, "SOX": 5.0, "Dodd-Frank": 5.0, "BSA": 5.0, "CEA": 5.0, "CCPA": 5.0, 
        "GLBA": 5.0, "PATRIOT Act": 5.0, "CRYPTO Act": 5.0, "Howey Test": 5.0, "Reg D": 5.0, 
        "Reg S": 5.0, "Reg A+": 5.0, "IRS": 5.0, "CFPB": 5.0, "NYDFS": 5.0, "BitLicense": 5.0, 
        "Reg SHO": 5.0, "T+2": 5.0, "legal certainty": 5.0, "dispute resolution": 5.0, 
        "governance framework": 5.0, "rule enforcement": 5.0, "audit failure": 5.0, 
        "compliance breach": 5.0, "data privacy": 5.0, "GDPR": 5.0, "securities law": 5.0, 
        "export control": 5.0, "trade sanction": 5.0, "regulatory audit": 5.0, "civil penalty": 5.0, 
        "disclosure obligation": 5.0, "financial oversight": 5.0, "regulatory gap": 5.0, 
        "legal precedent": 5.0, "anti-money laundering": 5.0, "know your customer": 5.0, 
        "sanctions list": 5.0, "regulatory framework": 5.0, "legal risk": 5.0, "regulatory change": 5.0, 
        "cross-border regulation": 5.0, "financial regulation": 5.0, "consumer protection": 5.0, 
        "data protection": 5.0, "privacy law": 5.0, "securities regulation": 5.0, "financial crime": 5.0, 
        "regulatory oversight": 5.0, "MiCA": 5.0, "Travel Rule": 5.0, "VASPs": 5.0, "FATF": 5.0, 
        "crypto tax reporting": 5.0, "stablecoin regulation": 5.0, "sanctions screening": 5.0, 
        "PEPs": 5.0, "counter-terrorism financing": 5.0, "CTF": 5.0, "blacklist": 5.0, "watchlist": 5.0, 
        "regulatory breach": 5.0, "regulatory investigation": 5.0, "ESMA": 5.0, "BaFin": 5.0, "FCA": 5.0, 
        "MAS": 5.0, "ASIC": 5.0, "contract ambiguity": 5.0, "jurisdictional uncertainty": 5.0, 
        "unenforceable agreement": 5.0, "regulatory violation": 5.0, "compliance audit": 5.0, 
        "legal ambiguity": 5.0, "cross-border legal risk": 5.0, "jurisdictional conflict": 5.0, 
        "legal framework gap": 5.0, "contractual uncertainty": 5.0, "legal clarity issue": 5.0, 
        "compliance gap": 5.0,
        "noncompliance penalty": 5.5, "regulatory fine": 5.5, "sanction violation": 5.5, 
        "noncompliance fine": 5.5, "sanction risk": 5.5, "regulatory penalty": 5.5, 
        "compliance violation": 5.5, "licensing suspension": 5.5, "fines and penalties": 5.5, 
        "compliance lapse": 5.5, "disclosure breach": 5.5, "regulatory whitelist violation": 5.5, 
        "compliance penalty": 5.5,
        "legal action": 6.0, "jurisdictional risk": 6.0, "anti-corruption": 6.0, "FCPA": 6.0, 
        "whistleblower": 6.0, "tax evasion": 6.0, "enforcement action": 6.0, "criminal liability": 6.0, 
        "subpoena": 6.0, "cease and desist": 6.0, "AML/CTF": 6.0, "KYC failure": 6.0, 
        "sanctions evasion": 6.0, "regulatory arbitrage": 6.0, "cross-jurisdictional conflict": 6.0, 
        "legal injunction": 6.0, "regulatory enforcement action": 6.0, "legal dispute risk": 6.0, 
        "lawsuit": 6.0, "sanctions": 6.0, "fraud": 6.0, "money laundering": 6.0, "ponzi": 6.0, 
        "insider trading": 6.0, "unregistered offering": 6.0, "legal noncompliance": 6.0, 
        "settlement uncertainty": 6.0, "contract enforceability": 6.0, "compliance failure": 6.0, 
        "regulatory ban": 6.0, "misrepresentation": 6.0, "financial crime": 6.0, "dispute escalation": 6.0, 
        "litigation risk": 6.0, "arbitration failure": 6.0, "legal enforceability issue": 6.0, 
        "terms violation": 6.0, "legal precedent risk": 6.0, "statutory noncompliance": 6.0, 
        "judicial uncertainty": 6.0, "legal interpretation risk": 6.0, "contractual gap": 6.0, 
        "enforcement uncertainty": 6.0, "legal challenge": 6.0, "dispute resolution failure": 6.0, 
        "binding agreement failure": 6.0, "court ruling risk": 6.0, "legal exposure": 6.0, 
        "contractual noncompliance": 6.0, "legal obligation failure": 6.0, 
        "regulatory interpretation risk": 6.0, "legal standing risk": 6.0, "unenforceable clause": 6.0, 
        "contractual dispute": 6.0, "legal jurisdiction risk": 6.0, "audit noncompliance": 6.0, 
        "regulatory enforcement": 6.0, "terrorist financing": 6.0, "counterfeit transaction": 6.0, 
        "bribery": 6.0, "corruption": 6.0, "money laundering scheme": 6.0, "sanctions circumvention": 6.0, 
        "regulatory blacklist": 6.0, "legal sanction": 6.0, "regulatory crackdown": 6.0, "legal settlement": 6.0
    },
    "cyber_resilience": {
        "phishing": 3.5, "social engineering": 3.5, "vishing": 3.5, "smishing": 3.5, 
        "typosquatting": 3.5, "cyber hygiene": 3.5, "crypto phishing": 3.5,
        "vulnerability assessment": 4.0, "patch management": 4.0, "encryption": 4.0, "firewall": 4.0, 
        "VPN": 4.0, "SIEM": 4.0, "endpoint security": 4.0, "cyber insurance": 4.0, "threat intelligence": 4.0, 
        "system outage": 4.0, "downtime": 4.0, "oracle failure": 4.0, "privacy breach": 4.0, 
        "security flaw": 4.0, "denial of service": 4.0, "service interruption": 4.0, "redundancy failure": 4.0, 
        "failover issue": 4.0, "backup failure": 4.0, "data corruption": 4.0, "availability loss": 4.0, 
        "fault tolerance failure": 4.0, "security lapse": 4.0, "patch delay": 4.0, "unpatched vulnerability": 4.0, 
        "resilience gap": 4.0, "threat detection failure": 4.0, "monitoring lapse": 4.0, 
        "secure configuration failure": 4.0, "attack surface expansion": 4.0, "network resilience": 4.0, 
        "threat mitigation": 4.0, "system hardening": 4.0,
        "data breach": 4.5, "cyberattack": 4.5, "ransomware": 4.5, "DDoS": 4.5, "malware": 4.5, 
        "zero-day": 4.5, "penetration testing": 4.5, "SOC": 4.5, "incident response": 4.5, 
        "GDPR violation": 4.5, "HIPAA violation": 4.5, "dark web": 4.5, "credential stuffing": 4.5, 
        "private key theft": 4.5, "wallet spoofing": 4.5, "sybil resistance failure": 4.5, 
        "node compromise": 4.5, "brute force": 4.5, "SQL injection": 4.5, "XSS": 4.5, "CSRF": 4.5, 
        "malware injection": 4.5, "trojan": 4.5, "worm": 4.5, "spyware": 4.5, "adware": 4.5, "botnet": 4.5, 
        "session hijacking": 4.5, "MITM": 4.5, "eavesdropping": 4.5, "packet sniffing": 4.5, "DoS": 4.5, 
        "exploit kit": 4.5, "rootkit": 4.5, "keylogger": 4.5, "backdoor": 4.5, "RAT": 4.5, "pharming": 4.5, 
        "clickjacking": 4.5, "credential harvesting": 4.5, "password cracking": 4.5, "DNS spoofing": 4.5, 
        "ARP poisoning": 4.5, "buffer overflow": 4.5, "heap overflow": 4.5, "stack overflow": 4.5, 
        "format string attack": 4.5, "race condition": 4.5, "timing attack": 4.5, "cache poisoning": 4.5, 
        "network intrusion": 4.5, "endpoint compromise": 4.5, "IoT vulnerability": 4.5, "API exploit": 4.5, 
        "session fixation": 4.5, "security breach": 4.5, "encryption failure": 4.5, "firewall breach": 4.5, 
        "network outage": 4.5, "traffic attack": 4.5, "consensus exploit": 4.5, "quantum threat": 4.5, 
        "protocol flaw": 4.5, "distributed denial of service": 4.5, "resilience failure": 4.5, 
        "disaster recovery failure": 4.5, "integrity violation": 4.5, "uptime breach": 4.5, 
        "authentication bypass": 4.5, "access control failure": 4.5, "intrusion detection failure": 4.5, 
        "endpoint vulnerability": 4.5, "network breach": 4.5, "security protocol failure": 4.5, 
        "penetration risk": 4.5, "hardening failure": 4.5, "incident response failure": 4.5, 
        "recovery delay": 4.5, "security posture weakness": 4.5, "data integrity breach": 4.5, 
        "system robustness failure": 4.5, "resilience overload": 4.5, "smart contract overflow": 4.5, 
        "chain impersonation": 4.5, "node spoofing": 4.5, "cyber recovery plan": 4.5,
        "double-spend attack": 5.0, "chain rollback": 5.0, "crypto ransomware": 5.0, "locker ransomware": 5.0, 
        "zero-trust failure": 5.0, "insider threat": 5.0, "supply chain attack": 5.0, "firmware exploit": 5.0, 
        "hardware backdoor": 5.0, "cloud breach": 5.0, "authentication bypass": 5.0, "hack recovery": 5.0, 
        "cyber espionage": 5.0, "data exfiltration": 5.0, "ransomware lockdown": 5.0, 
        "malware propagation": 5.0, "zero-day exploitation": 5.0, "crypto jacking": 5.0, "wallet cloning": 5.0,
        "spear phishing": 5.5, "whaling": 5.5, "privilege escalation": 5.5, "side-channel attack": 5.5
    },
    "asset_safeguarding": {
        "custody": 4.0, "private key": 4.0, "multi-signature": 4.0, "cold wallet": 4.0, "vault": 4.0, 
        "HSM": 4.0, "secure enclave": 4.0, "proof of reserve": 4.0, "wallet backup": 4.0, 
        "offline storage": 4.0, "key sharding": 4.0, "hardware wallet": 4.0, "2FA": 4.0, 
        "threshold signature scheme": 4.0, "insurance coverage": 4.0, "access control": 4.0, 
        "recovery protocol": 4.0, "safeguarding keys": 4.0, "digital vault": 4.0, "key recovery": 4.0, 
        "loss prevention": 4.0, "cold storage insurance": 4.0, "tamper resistance": 4.0, 
        "security guarantee": 4.0, "decentralized custody": 4.0, "escrow smart contract": 4.0, 
        "asset tracking": 4.0, "custody audit": 4.0, "key escrow security": 4.0, 
        "fund safeguarding protocol": 4.0,
        "asset theft": 4.5, "custodial loss": 4.5, "wallet breach": 4.5, "unauthorized withdrawal": 4.5, 
        "custody breach": 4.5, "hot wallet hack": 4.5, "asset freeze": 4.5, "asset mismanagement": 4.5, 
        "safekeeping failure": 4.5, "deposit risk": 4.5, "withdrawal delay": 4.5, "asset diversion": 4.5, 
        "custodial insolvency": 4.5, "trust account breach": 4.5, "multi-signature failure": 4.5, 
        "key mismanagement": 4.5, "asset exposure": 4.5, "uninsured loss": 4.5, "customer fund loss": 4.5, 
        "safeguarding breach": 4.5, "asset recovery failure": 4.5, "client asset risk": 4.5, 
        "customer data leak": 4.5, "payment fraud": 4.5, "transaction reversal": 4.5, "token freeze": 4.5, 
        "asset lockout": 4.5, "asset misallocation": 4.5, "key rotation": 4.5,
        "private key leak": 5.0, "fund misappropriation": 5.0, "account takeover": 5.0, "external theft": 5.0, 
        "escrow failure": 5.0, "trust violation": 5.0, "asset seizure": 5.0, "fund freeze": 5.0, 
        "identity theft": 5.0, "custody exploit": 5.0, "fund siphoning": 5.0, "cold storage breach": 5.0, 
        "key escrow failure": 5.0, "custodial fraud": 5.0, "insider theft": 5.0, "key compromise": 5.0, 
        "smart contract freeze": 5.0,
        "rug pull": 5.5, "exit scam": 5.5, "custodial theft": 5.5, "wallet drain": 5.5
    },
    "operational_scale": {
        "scalability": 3.0, "capacity": 3.0, "overload": 3.0, "bottleneck": 3.0, "resource constraint": 3.0, 
        "overprovisioning": 3.0, "underprovisioning": 3.0, "scaling cost overrun": 3.0, 
        "inadequate scaling": 3.0, "load balancing failure": 3.0, "load testing": 3.0, "capacity planning": 3.0,
        "capacity overload": 3.5, "throughput bottleneck": 3.5, "latency spike": 3.5, 
        "resource exhaustion": 3.5, "scaling failure": 3.5, "performance degradation": 3.5, 
        "transaction backlog": 3.5, "bandwidth limitation": 3.5, "queue overflow": 3.5, 
        "processing delay": 3.5, "infrastructure bottleneck": 3.5, "high latency": 3.5, 
        "low throughput": 3.5, "scalability bottleneck": 3.5, "resource contention": 3.5, 
        "service throttling": 3.5, "peak load failure": 3.5, "traffic surge": 3.5, "demand spike": 3.5, 
        "expansion risk": 3.5, "growth limitation": 3.5, "operational ceiling": 3.5, 
        "concurrency issue": 3.5, "dynamic scaling failure": 3.5, "horizontal scaling issue": 3.5, 
        "vertical scaling limit": 3.5, "multi-region failure": 3.5, "geo-scaling risk": 3.5, 
        "node overload": 3.5, "chain congestion": 3.5, "transaction latency": 3.5, 
        "blockchain scalability issue": 3.5, "network saturation": 3.5, "processing bottleneck": 3.5, 
        "scalability audit": 3.5,
        "system overload": 4.0, "system failure": 4.0, "operational disruption": 4.0, 
        "system saturation": 4.0, "parallel processing failure": 4.0, "service degradation": 4.0, 
        "operational failure": 4.0, "system downtime": 4.0, "performance optimization": 4.0
    },
    "interoperability": {
        "integration": 2.5, "compatibility": 2.5, "protocol mismatch": 2.5, "network issue": 2.5, 
        "data exchange failure": 2.5, "middleware failure": 2.5, "connection timeout": 2.5, 
        "integration latency": 2.5, "system linkage failure": 2.5, "interoperability bottleneck": 2.5, 
        "connectivity overload": 2.5, "inter-system latency": 2.5, "integration dependency risk": 2.5, 
        "data interoperability risk": 2.5, "interop testing": 2.5, "protocol alignment": 2.5,
        "integration failure": 3.0, "API breakdown": 3.0, "interface mismatch": 3.0, 
        "protocol incompatibility": 3.0, "data sync failure": 3.0, "interoperability breakdown": 3.0, 
        "cross-chain failure": 3.0, "interoperability risk": 3.0, "connectivity loss": 3.0, 
        "network disconnection": 3.0, "system integration risk": 3.0, "inter-system conflict": 3.0, 
        "communication breakdown": 3.0, "sync delay": 3.0, "interoperability gap": 3.0, 
        "cross-platform failure": 3.0, "data flow interruption": 3.0, "connectivity outage": 3.0, 
        "cross-ledger failure": 3.0, "data transfer failure": 3.0, "interface disruption": 3.0, 
        "cross-network failure": 3.0, "interoperability overload": 3.0, "connection instability": 3.0, 
        "sync disruption": 3.0, "bridge latency": 3.0, "chain isolation": 3.0, "cross-chain validation": 3.0,
        "bridge collapse": 3.5, "cross-chain exploit": 3.5, "interoperability flaw": 3.5, "bridge security": 3.5
    },
    "market_risk": {
        "liquidity": 3.0, "speculation": 3.0, "market inefficiency": 3.0, "arbitrage failure": 3.0, 
        "liquidity provision": 3.0,
        "volatility": 3.5, "bubble": 3.5, "liquidity risk": 3.5, "counterparty risk": 3.5, 
        "overexposure": 3.5, "undercollateralization": 3.5, "token devaluation": 3.5, 
        "market illiquidity": 3.5, "market stress test": 3.5, "market depth": 3.5,
        "market crash": 4.0, "flash crash": 4.0, "liquidity drain": 4.0, "market manipulation": 4.0, 
        "pump and dump": 4.0, "wash trading": 4.0, "market distortion": 4.0, "speculative risk": 4.0, 
        "financial loss": 4.0, "price manipulation": 4.0, "spoofing attack": 4.0, "fake volume": 4.0, 
        "market spoofing": 4.0, "liquidity squeeze": 4.0, "volatility spike": 4.0, "market bubble": 4.0, 
        "speculative bubble": 4.0, "crash risk": 4.0, "market exit scam": 4.0, 
        "liquidity pool collapse": 4.0, "price stability": 4.0
    },
    "general_operational": {
        "delay": 2.0, "error": 2.0, "human error": 2.0, "operational audit": 2.0,
        "default": 2.5, "mismanagement": 2.5, "oversight": 2.5, "disruption": 2.5, 
        "third-party failure": 2.5, "vendor risk": 2.5, "supply chain risk": 2.5, 
        "technology risk": 2.5, "infrastructure risk": 2.5, "false positive": 2.5, 
        "team credibility": 2.5, "financial opacity": 2.5, "dependency risk": 2.5, 
        "vendor lock-in": 2.5, "operational risk": 2.5, "process failure": 2.5, 
        "team vetting": 2.5, "process resilience": 2.5,
        "bankruptcy": 3.0, "reputational risk": 3.0, "stakeholder misunderstanding": 3.0, 
        "unverified claims": 3.0, "conflict of interest": 3.0, "systemic risk": 3.0, 
        "code audit failure": 3.0, "centralization risk": 3.0, "impermanent loss": 3.0, 
        "rebase instability": 3.0, "MEV exploitation": 3.0, "code vulnerability": 3.0, 
        "audit gap": 3.0, "negligence": 3.0, "operational lapse": 3.0, "governance transparency": 3.0,
        "embezzlement": 4.0, "insolvency": 4.0, "fund mismanagement": 4.0, "investor fraud": 4.0, 
        "misconduct": 4.0, "false reporting": 4.0, "executive risk": 4.0, "insider threat": 4.0, 
        "vote manipulation": 4.0, "DAO takeover": 4.0, "team exit risk": 4.0, 
        "liquidity pool rug pull": 4.0, "yield farming collapse": 4.0, "governance token manipulation": 4.0, 
        "reentrancy": 4.0, "unauthorized holdings": 4.0, "trust violation": 4.0, 
        "financial misstatement": 4.0, "collusion": 4.0, "governance breakdown": 4.0, 
        "team incompetence": 4.0, "project abandonment": 4.0,
        "fraudulent intent": 5.0, "rug pull": 5.0, "ponzi scheme": 5.0, "exit scam": 5.0, 
        "pump and dump": 5.0, "fake volume": 5.0, "wash trading": 5.0, "token scam": 5.0, 
        "whitepaper fraud": 5.0, "yield farming scam": 5.0, "liquidity drain": 5.0, "insider rug pull": 5.0
    },
    "esg_risk": {
        # Weight 2.5: Positive or neutral ESG terms
        "sustainability": 2.5, "green energy": 2.5, "social impact": 2.5, "human rights": 2.5,
        "corporate governance": 2.5, "board diversity": 2.5, "shareholder rights": 2.5, 
        "ethical sourcing": 2.5, "social responsibility": 2.5, "sustainable investing": 2.5, 
        "net zero": 2.5, "CSR": 2.5, "stakeholder engagement": 2.5, "transparency": 2.5, 
        "renewable energy": 2.5, "energy audit": 2.5, "carbon offset": 2.5, "ESG scoring": 2.5, 
        "sustainable tokenomics": 2.5, "eco-friendly mining": 2.5,
        # Weight 3.5: Moderate ESG concerns
        "carbon footprint": 3.5, "mining energy consumption": 3.5, "energy inefficiency": 3.5, 
        "ecological impact": 3.5, "decentralized governance dispute": 3.5, "governance opacity": 3.5, 
        "carbon emissions": 3.5, "pollution risk": 3.5, "resource depletion": 3.5, 
        "biodiversity loss": 3.5, "social license risk": 3.5, "community displacement": 3.5,
        # Weight 4.5: Significant ESG violations
        "environmental violation": 4.5, "governance failure": 4.5, "climate risk": 4.5, 
        "environmental damage": 4.5, "labor violation": 4.5, "ethical breach": 4.5, 
        "social unrest": 4.5, "ESG reporting failure": 4.5, "ethical misconduct": 4.5, 
        "greenwashing": 4.5,
        # Weight 5.5: Severe ESG risks
        "ESG compliance": 5.5  # Non-compliance with ESG standards is a severe risk
    }
}

MITIGATION_TERMS = {
    "insured", "insurance policy", "SOC 2", "SOC 1", "ISO 27001",
    "penetration tested", "bug bounty", "audited", "smart contract audit",
    "cold storage", "segregated account", "multi-signature", "compliance team",
    "AML program", "KYC verified", "third-party custody", "firewall", "incident response plan",
    "data encryption", "threat monitoring", "disaster recovery", "regulatory approval",
    "registered with SEC", "regulated by CFTC", "BitLicense", "GDPR compliance", "SOC 2 implemented",
    "under FDIC protection", "compliant with MiCA", "regulated entity",
    # Added terms
    "cyber insurance", "compliance audit", "risk mitigation plan", "secure backup"
}

POSITIVE_TERMS = {
    "revolutionary", "guaranteed", "breakthrough", "unprecedented", "exceptional", "best-in-class",
    "leading", "pioneering", "flawless", "perfect", "assured", "top-tier", "game-changer", "stellar",
    "outstanding", "ultimate", "secure forever", "risk-free", "unmatched", "infallible",
    # Added terms
    "trustworthy", "reliable", "proven", "stable"
}

KEYWORDS = FINANCIAL_TERMS | REGULATIONS | CRYPTO_TERMS | RISK_TERMS | ESG_TERMS | CYBERSECURITY_TERMS

REGION_TERMS = {
    # U.S. and Territories (Low Risk: 2.0)
    "United States": 2.0, "America": 2.0,
    "New York": 2.0, "California": 2.0, "Texas": 2.0,
    "Florida": 2.0, "Illinois": 2.0, "Washington, D.C.": 2.0,
    "Puerto Rico": 2.0, "Guam": 2.0, "American Samoa": 2.0, "Virgin Islands": 2.0,

    # Close Allies with Strong Regulation (Moderate Risk: 2.5–3.5)
    "Canada": 2.5, "United Kingdom": 2.5, "Britain": 2.5,
    "Australia": 2.5, "Japan": 2.5, "Germany": 2.5,
    "France": 2.5, "South Korea": 2.5, "Singapore": 2.5,
    "Switzerland": 2.5, "Netherlands": 2.5, "Sweden": 2.5,
    "Norway": 2.5, "Denmark": 2.5, "New Zealand": 2.5,
    "European Union": 3.5,  # Higher due to regulatory variance

    # Emerging Markets (Higher Risk: 4.0–5.0)
    "India": 4.0, "Brazil": 4.0, "Mexico": 4.0,
    "South Africa": 4.0, "Indonesia": 4.0, "Turkey": 4.0,
    "Argentina": 4.5, "Nigeria": 4.5, "Philippines": 4.5,
    "Thailand": 4.5, "Malaysia": 4.5, "Vietnam": 4.5,
    "China": 5.0, "Hong Kong": 4.0, "Taiwan": 4.0,

    # Sanctioned/Offshore/High-Risk Jurisdictions (Very High Risk: 5.5–7.0)
    "Russia": 6.0, "Iran": 7.0, "North Korea": 7.0,
    "Cuba": 6.0, "Syria": 6.0, "Venezuela": 6.0,
    "Bahamas": 6.0, "Cayman Islands": 6.0, "Bermuda": 6.0,
    "Seychelles": 6.0, "Malta": 5.5, "Gibraltar": 5.5,
    "Panama": 5.5, "Belize": 5.5, "British Virgin Islands": 6.0,

    # Rest of the World (Default Non-U.S.: 4.0 unless specified)
    "Afghanistan": 6.0, "Albania": 4.0, "Algeria": 4.0, "Andorra": 4.0,
    "Angola": 4.5, "Antigua and Barbuda": 5.5, "Armenia": 4.0,
    "Austria": 2.5, "Azerbaijan": 4.0, "Bahrain": 4.0,
    "Bangladesh": 4.5, "Barbados": 5.5, "Belarus": 5.5,
    "Belgium": 2.5, "Benin": 4.5, "Bhutan": 4.0,
    "Bolivia": 4.5, "Bosnia and Herzegovina": 4.0, "Botswana": 4.0,
    "Brunei": 4.0, "Bulgaria": 3.5, "Burkina Faso": 4.5,
    "Burundi": 4.5, "Cambodia": 4.5, "Cameroon": 4.5,
    "Cape Verde": 4.0, "Central African Republic": 4.5, "Chad": 4.5,
    "Chile": 4.0, "Colombia": 4.5, "Comoros": 4.5,
    "Congo": 4.5, "Costa Rica": 4.0, "Croatia": 3.5,
    "Cyprus": 4.0, "Czech Republic": 3.5, "DR Congo": 4.5,
    "Djibouti": 4.5, "Dominica": 5.5, "Dominican Republic": 4.5,
    "Ecuador": 4.5, "Egypt": 4.5, "El Salvador": 4.5,
    "Equatorial Guinea": 4.5, "Eritrea": 4.5, "Estonia": 3.5,
    "Eswatini": 4.5, "Ethiopia": 4.5, "Fiji": 4.0,
    "Finland": 2.5, "Gabon": 4.5, "Gambia": 4.5,
    "Georgia": 4.0, "Ghana": 4.5, "Greece": 3.5,
    "Grenada": 5.5, "Guatemala": 4.5, "Guinea": 4.5,
    "Guinea-Bissau": 4.5, "Guyana": 4.5, "Haiti": 4.5,
    "Honduras": 4.5, "Hungary": 3.5, "Iceland": 2.5,
    "Ireland": 2.5, "Israel": 3.5, "Italy": 3.5,
    "Jamaica": 4.5, "Jordan": 4.0, "Kazakhstan": 4.5,
    "Kenya": 4.5, "Kiribati": 4.0, "Kuwait": 4.0,
    "Kyrgyzstan": 4.5, "Laos": 4.5, "Latvia": 3.5,
    "Lebanon": 4.5, "Lesotho": 4.5, "Liberia": 4.5,
    "Libya": 5.5, "Liechtenstein": 2.5, "Lithuania": 3.5,
    "Luxembourg": 2.5, "Madagascar": 4.5, "Malawi": 4.5,
    "Maldives": 4.0, "Mali": 4.5, "Marshall Islands": 4.0,
    "Mauritania": 4.5, "Mauritius": 4.0, "Micronesia": 4.0,
    "Moldova": 4.0, "Monaco": 4.0, "Mongolia": 4.5,
    "Montenegro": 4.0, "Morocco": 4.5, "Mozambique": 4.5,
    "Myanmar": 5.5, "Namibia": 4.5, "Nauru": 4.0,
    "Nepal": 4.5, "Nicaragua": 4.5, "Niger": 4.5,
    "Oman": 4.0, "Pakistan": 5.0, "Palau": 4.0,
    "Palestine": 4.5, "Papua New Guinea": 4.5, "Paraguay": 4.5,
    "Peru": 4.5, "Poland": 3.5, "Portugal": 3.5,
    "Qatar": 4.0, "Romania": 3.5, "Rwanda": 4.5,
    "Saint Kitts and Nevis": 5.5, "Saint Lucia": 5.5,
    "Saint Vincent and the Grenadines": 5.5, "Samoa": 4.0,
    "San Marino": 4.0, "Sao Tome and Principe": 4.5,
    "Saudi Arabia": 4.5, "Senegal": 4.5, "Serbia": 4.0,
    "Sierra Leone": 4.5, "Slovakia": 3.5, "Slovenia": 3.5,
    "Solomon Islands": 4.0, "Somalia": 5.5, "South Sudan": 5.5,
    "Spain": 3.5, "Sri Lanka": 4.5, "Sudan": 5.5,
    "Suriname": 4.5, "Tajikistan": 4.5, "Tanzania": 4.5,
    "Timor-Leste": 4.5, "Togo": 4.5, "Tonga": 4.0,
    "Trinidad and Tobago": 4.5, "Tunisia": 4.5, "Turkmenistan": 4.5,
    "Tuvalu": 4.0, "Uganda": 4.5, "Ukraine": 5.0,
    "United Arab Emirates": 4.5, "Uruguay": 4.0, "Uzbekistan": 4.5,
    "Vanuatu": 4.0, "Vatican City": 4.0, "Yemen": 5.5,
    "Zambia": 4.5, "Zimbabwe": 5.0
}

STATE_REGULATORS = {
    "New York": (["NYDFS", "BitLicense"], 3.0),
    "California": (["DFPI", "California Department of Financial Protection and Innovation"], 2.5),
    "Texas": (["Texas Department of Banking", "Texas State Securities Board"], 2.0),
    "Florida": (["Florida Office of Financial Regulation"], 2.5),
    "Illinois": (["Illinois Department of Financial and Professional Regulation"], 2.0),
    "Massachusetts": (["Massachusetts Securities Division"], 2.5),
    "New Jersey": (["New Jersey Bureau of Securities"], 2.0),
    "Washington": (["Washington Department of Financial Institutions"], 2.0),
    "Pennsylvania": (["Pennsylvania Department of Banking and Securities"], 2.0),
    "Georgia": (["Georgia Department of Banking and Finance"], 2.0),
    "Michigan": (["Michigan Department of Insurance and Financial Services"], 2.0),
    "Ohio": (["Ohio Division of Securities"], 2.0),
    "Virginia": (["Virginia State Corporation Commission"], 2.0),
    "North Carolina": (["North Carolina Department of the Secretary of State Securities Division"], 2.0),
    "Colorado": (["Colorado Division of Securities"], 2.0),
    "Minnesota": (["Minnesota Department of Commerce"], 2.0),
    "Missouri": (["Missouri Securities Division"], 2.0),
    "Arizona": (["Arizona Corporation Commission Securities Division"], 2.0),
    "Indiana": (["Indiana Securities Division"], 2.0),
    "Oregon": (["Oregon Division of Financial Regulation"], 2.0),
    "Tennessee": (["Tennessee Department of Commerce and Insurance"], 2.0),
    "Wisconsin": (["Wisconsin Department of Financial Institutions"], 2.0),
    "Nevada": (["Nevada Secretary of State Securities Division"], 2.0),
    "Louisiana": (["Louisiana Office of Financial Institutions"], 2.0),
    "Kentucky": (["Kentucky Department of Financial Institutions"], 2.0),
    "Oklahoma": (["Oklahoma Department of Securities"], 2.0),
    "South Carolina": (["South Carolina Attorney General Securities Division"], 2.0),
    "Alabama": (["Alabama Securities Commission"], 2.0),
    "Mississippi": (["Mississippi Secretary of State Securities Division"], 2.0),
    "Arkansas": (["Arkansas Securities Department"], 2.0),
    "New Mexico": (["New Mexico Regulation and Licensing Department"], 2.0),
    "Utah": (["Utah Division of Securities"], 2.0),
    "Iowa": (["Iowa Insurance Division"], 2.0),
    "Kansas": (["Kansas Securities Commissioner"], 2.0),
    "Nebraska": (["Nebraska Department of Banking and Finance"], 2.0),
    "Idaho": (["Idaho Department of Finance"], 2.0),
    "Maine": (["Maine Office of Securities"], 2.0),
    "New Hampshire": (["New Hampshire Bureau of Securities Regulation"], 2.0),
    "Vermont": (["Vermont Department of Financial Regulation"], 2.0),
    "Rhode Island": (["Rhode Island Department of Business Regulation"], 2.0),
    "Delaware": (["Delaware Investor Protection Unit"], 2.0),
    "Montana": (["Montana Securities Department"], 2.0),
    "North Dakota": (["North Dakota Securities Department"], 2.0),
    "South Dakota": (["South Dakota Division of Insurance Securities Regulation"], 2.0),
    "Alaska": (["Alaska Division of Banking and Securities"], 2.0),
    "Hawaii": (["Hawaii Department of Commerce and Consumer Affairs"], 2.0),
    "Wyoming": (["Wyoming Secretary of State Securities Division"], 2.0),
    "West Virginia": (["West Virginia Securities Commission"], 2.0)
}
URL_PATTERN = re.compile(r'(https?://[^\s]+|www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')
CIK_PATTERN = re.compile(r'CIK\s*(\d{10})')



# Utility Functions
def extract_emails(text):
    words = text.split()
    emails = set()
    for word in words:
        try:
            emails.add(validate_email(word, check_deliverability=False).email)
        except EmailNotValidError:
            continue
    return list(emails)

def extract_phone_numbers(text, region="US"):
    numbers = set(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                  for match in phonenumbers.PhoneNumberMatcher(text, region))
    return list(numbers)

def extract_websites(text):
    return list(set(URL_PATTERN.findall(text)))

def extract_addresses(text):
    return [str(address) for address in pyap.parse(text, country="US")]

def extract_cik_numbers(text):
    return CIK_PATTERN.findall(text)

def extract_company_names(text):
    doc = nlp(text)
    companies = set(ent.text for ent in doc.ents if ent.label_ == "ORG")
    for cik in extract_cik_numbers(text):
        try:
            company_info = edgar_client.get_company_info(cik=cik)
            companies.add(company_info["name"])
        except Exception as e:
            logging.debug(f"EDGAR lookup failed for CIK {cik}: {e}")
    return list(companies)

def extract_person_names(text):
    sentence = Sentence(text)
    flair_tagger.predict(sentence)
    return list(set(entity.text for entity in sentence.get_spans("ner") if entity.tag == "PER"))

def extract_financial_terms(text):
    text_lower = text.lower()
    return {
        "financial_terms": [term for term in FINANCIAL_TERMS if term.lower() in text_lower],
        "crypto_terms": [crypto for crypto in CRYPTO_TERMS if crypto.lower() in text_lower],
        "risk_mentions": [risk for category in RISK_CATEGORIES.values() 
                         for risk in category if risk.lower() in text_lower]
    }

def calculate_risk_score(found_risks, sentiment_score, text_length, source_type="text", regions=None, text=""):
    """Calculate raw risk score without 0-10 scaling."""
    raw_score = 0.0
    categories_hit = set()
    regulator_score = 0.0
    mitigation_factor = 1.0

    for risk in found_risks:
        risk_lower = risk.lower()
        for cat, terms in RISK_CATEGORIES.items():
            if risk_lower in terms:
                raw_score += terms[risk_lower]
                categories_hit.add(cat)
                break

    raw_score += len(categories_hit) * 1.5
    sentiment_factor = 1.0 + abs(sentiment_score) if sentiment_score < 0 else max(0.8, 1.0 - (sentiment_score * 0.2))
    raw_score *= sentiment_factor
    source_multiplier = 1.3 if source_type == "web" else 1.0
    raw_score *= source_multiplier
    region_weight = min(REGION_TERMS.get(r, 4.0) for r in regions or ["Unknown"])
    raw_score *= (1 + (region_weight / 10))
    text_lower = text.lower()
    for state, (agencies, weight) in STATE_REGULATORS.items():
        if any(agency.lower() in text_lower for agency in agencies):
            regulator_score += weight
    raw_score += regulator_score
    mitigations = [m for m in MITIGATION_TERMS if m.lower() in text_lower]
    if mitigations:
        mitigation_factor = max(0.5, 1.0 - (len(mitigations) * 0.1))
    raw_score *= mitigation_factor
    return raw_score

def analyze_sentiment(text):
    scores = sentiment_analyzer.polarity_scores(text)
    compound_score = scores["compound"]
    text_lower = text.lower()
    
    risk_count = sum(1 for w in text_lower.split() if any(w in cat for cat in RISK_CATEGORIES.values()))
    mitigation_count = sum(1 for w in text_lower.split() if w in MITIGATION_TERMS)
    positive_count = sum(1 for w in text_lower.split() if w in POSITIVE_TERMS)
    
    if positive_count > risk_count and compound_score > 0:
        compound_score -= 0.4
    if risk_count > mitigation_count and compound_score > 0:
        compound_score -= 0.3
    
    sentiment = "positive" if compound_score >= 0.05 else "negative" if compound_score <= -0.05 else "neutral"
    return {"sentiment": sentiment, "sentiment_score": compound_score}

def anonymize_sensitive_data(text):
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    addresses = pyap.parse(text, country="US")
    for addr in addresses:
        text = text.replace(str(addr), '[ADDRESS]')
    return text

def extract_region(text):
    text_lower = text.lower()
    doc = nlp(text)
    ner_regions = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    term_regions = [region for region in REGION_TERMS.keys() if re.search(r'\b' + re.escape(region.lower()) + r'\b', text_lower)]
    fuzzy_regions = []
    similarity_threshold = 85
    for candidate in ner_regions:
        if candidate.lower() not in text_lower:
            continue
        if candidate in REGION_TERMS:
            fuzzy_regions.append(candidate)
        else:
            for valid_region in REGION_TERMS.keys():
                similarity = fuzz.ratio(candidate.lower(), valid_region.lower())
                if similarity >= similarity_threshold:
                    fuzzy_regions.append(valid_region)
                    break
    combined_regions = list(set(term_regions + fuzzy_regions))
    return combined_regions if combined_regions else ["Unknown"]

def detect_state_risks(text):
    text_lower = text.lower()
    detected = []
    for state, (agencies, weight) in STATE_REGULATORS.items():
        for agency in agencies:
            if agency.lower() in text_lower:
                profile = {"state": state, "agency": agency, "weight": weight, "laws": []}
                if state == "New York":
                    profile["laws"].append("BitLicense")
                elif state == "Texas":
                    profile["laws"].append("Texas Money Services Act")
                detected.append((state, profile))
    return detected

def detect_mitigation_terms(text):
    return [term for term in MITIGATION_TERMS if term.lower() in text.lower()]

risk_embeddings = {cat: model.encode(list(terms)) for cat, terms in RISK_CATEGORIES.items()}

def infer_latent_risks(text, threshold=0.50):
    embedding = model.encode(text)
    detected = []
    for cat, examples in risk_embeddings.items():
        for risk_emb in examples:
            score = util.cos_sim(embedding, risk_emb).item()
            if score > threshold:
                detected.append((cat, score))
    return detected

def extract_entities(chunk_text, source_type="text"):
    doc = nlp(chunk_text)
    sentence = Sentence(chunk_text)
    flair_tagger.predict(sentence)
    
    entities = {
        "emails": extract_emails(chunk_text),
        "companies": extract_company_names(chunk_text),
        "persons": list(set(entity.text for entity in sentence.get_spans("ner") if entity.tag == "PER")),
        "phone_numbers": extract_phone_numbers(chunk_text),
        "addresses": extract_addresses(chunk_text),
        "urls": extract_websites(chunk_text),
        "cik_numbers": extract_cik_numbers(chunk_text),
        "financial_terms": extract_financial_terms(chunk_text)["financial_terms"],
        "crypto_terms": extract_financial_terms(chunk_text)["crypto_terms"],
        "risk_mentions": extract_financial_terms(chunk_text)["risk_mentions"],
        "mitigation_terms": detect_mitigation_terms(chunk_text),
        "latent_risks": infer_latent_risks(chunk_text),
        "state_regulators": [agency for _, agency in detect_state_risks(chunk_text)],
        "state_profile": detect_state_risks(chunk_text),
        "region": extract_region(chunk_text),
        "registration_numbers": re.findall(r"(?:SEC|CFTC)?\s*#\d+[-\d]*", chunk_text),
        "dates": re.findall(r"\d{4}-\d{2}-\d{2}", chunk_text),
        "percentages": re.findall(r"\d+%", chunk_text),
        "quantities": re.findall(r"\d+\s*(million|billion|tokens)", chunk_text),
        "legal_structures": re.findall(r"(LP|LLC|DAO|SPV)", chunk_text)
    }
    
    # Role extraction
    roles = {}
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            for token in ent.sent:
                if token.text.lower() in {"ceo", "founder", "advisor", "cto"}:
                    roles[ent.text] = token.text
    entities["team_roles"] = roles
    
    # Red flags
    entities["missing_disclosures"] = ["KYC" not in chunk_text.lower(), "AML" not in chunk_text.lower()]
    entities["hype_count"] = sum(chunk_text.lower().count(term) for term in POSITIVE_TERMS)
    
    sentiment_data = analyze_sentiment(chunk_text)
    entities["sentiment"] = sentiment_data["sentiment"]
    entities["sentiment_score"] = sentiment_data["sentiment_score"]
    entities["risk_score"] = calculate_risk_score(
        entities["risk_mentions"], sentiment_data["sentiment_score"], 
        len(chunk_text.split()), source_type, entities["region"], chunk_text
    )
    
    anonymized_text = anonymize_sensitive_data(chunk_text)
    return entities, anonymized_text