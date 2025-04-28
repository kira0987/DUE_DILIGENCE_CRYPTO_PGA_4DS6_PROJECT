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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Download required NLTK data
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

# Initialize NLP tools
model = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("en_core_web_lg")
flair_tagger = SequenceTagger.load("flair/ner-english-large")
lemmatizer = WordNetLemmatizer()
sentiment_analyzer = SentimentIntensityAnalyzer()

# Expanded Term Sets (unchanged)
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
    "financial misstatement", "accounting fraud", "revenue recognition", "cost overrun", "fund diversion"
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
    "legal injunction", "compliance lapse", "regulatory enforcement action", "disclosure breach"
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
    "transaction tracing", "crypto laundering", "mixer", "tumbler", "privacy layer", "zero-knowledge proof"
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
    "biodiversity loss", "ethical misconduct", "greenwashing", "social license risk", "community displacement"
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
    "certificate spoofing", "replay attack", "hardware trojan", "fuzzing"
}

RISK_CATEGORIES = {
    "legal_regulatory": REGULATIONS | {
        "contract ambiguity", "legal dispute risk", "jurisdictional uncertainty", "unenforceable agreement",
        "regulatory violation", "compliance breach", "noncompliance fine", "sanction risk", "fraud",
        "money laundering", "ponzi", "insider trading", "lawsuit", "tax evasion", "unregistered offering",
        "legal noncompliance", "settlement uncertainty", "contract enforceability", "compliance failure",
        "sanctions", "blacklist", "regulatory penalty", "legal dispute", "contract breach", "compliance audit",
        "regulatory ban", "legal ambiguity", "misrepresentation", "financial crime", "dispute escalation",
        "litigation risk", "arbitration failure", "legal enforceability issue", "terms violation",
        "legal precedent risk", "statutory noncompliance", "judicial uncertainty", "legal interpretation risk",
        "contractual gap", "enforcement uncertainty", "legal challenge", "dispute resolution failure",
        "cross-border legal risk", "jurisdictional conflict", "legal framework gap", "contractual uncertainty",
        "binding agreement failure", "legal clarity issue", "court ruling risk", "legal exposure",
        "contractual noncompliance", "legal obligation failure", "regulatory interpretation risk",
        "legal standing risk", "unenforceable clause", "contractual dispute", "legal jurisdiction risk",
        "audit noncompliance", "regulatory enforcement", "compliance gap", "terrorist financing",
        "counterfeit transaction", "bribery", "corruption", "money laundering scheme", "sanctions circumvention",
        "regulatory blacklist", "legal sanction", "compliance penalty", "regulatory crackdown"
    },
    "cyber_resilience": CYBERSECURITY_TERMS | {
        "system outage", "downtime", "security breach", "encryption failure", "firewall breach",
        "network outage", "traffic attack", "oracle failure", "consensus exploit", "quantum threat",
        "hack recovery", "protocol flaw", "privacy breach", "security flaw", "denial of service",
        "distributed denial of service", "service interruption", "resilience failure", "redundancy failure",
        "failover issue", "disaster recovery failure", "backup failure", "data corruption",
        "integrity violation", "availability loss", "uptime breach", "fault tolerance failure",
        "security lapse", "authentication bypass", "access control failure", "intrusion detection failure",
        "endpoint vulnerability", "network breach", "security protocol failure", "penetration risk",
        "hardening failure", "patch delay", "unpatched vulnerability", "incident response failure",
        "recovery delay", "resilience gap", "security posture weakness", "threat detection failure",
        "monitoring lapse", "secure configuration failure", "data integrity breach", "system robustness failure",
        "attack surface expansion", "resilience overload", "cyber espionage", "data exfiltration",
        "ransomware lockdown", "malware propagation", "zero-day exploitation", "crypto jacking"
    },
    "asset_safeguarding": {
        "asset theft", "custodial loss", "wallet breach", "private key leak", "fund misappropriation",
        "account takeover", "unauthorized withdrawal", "custody breach", "hot wallet hack", "rug pull",
        "exit scam", "custodial theft", "asset freeze", "asset mismanagement", "safekeeping failure",
        "deposit risk", "withdrawal delay", "asset diversion", "custodial insolvency", "trust account breach",
        "multi-signature failure", "key mismanagement", "asset exposure", "uninsured loss",
        "customer fund loss", "safeguarding breach", "asset recovery failure", "client asset risk",
        "insider theft", "external theft", "escrow failure", "trust violation", "asset seizure",
        "fund freeze", "customer data leak", "identity theft", "payment fraud", "transaction reversal",
        "token freeze", "wallet drain", "custody exploit", "fund siphoning", "asset misallocation",
        "cold storage breach", "key escrow failure", "asset lockout", "custodial fraud", "custody",
        "private key", "multi-signature", "cold wallet", "vault", "HSM", "secure enclave",
        "proof of reserve", "wallet backup", "offline storage", "key sharding", "hardware wallet", "2FA",
        "threshold signature scheme", "custody breach", "wallet drain", "rug pull", "exit scam",
        "key leakage", "secure custody", "asset control", "safekeeping failure", "insurance coverage",
        "custody exploit", "fund mismanagement", "access control", "recovery protocol", "safeguarding keys",
        "digital vault", "key recovery", "identity theft", "asset lock", "smart contract freeze",
        "unauthorized withdrawal", "loss prevention", "key compromise", "fraud detection",
        "cold storage insurance", "custodian misbehavior", "tamper resistance", "token freeze",
        "key rotation", "escrow failure", "security guarantee", "decentralized custody", "escrow smart contract"
    },
    "operational_scale": {
        "capacity overload", "throughput bottleneck", "latency spike", "resource exhaustion",
        "scaling failure", "performance degradation", "system overload", "transaction backlog",
        "system failure", "operational disruption", "scalability failure", "bandwidth limitation",
        "queue overflow", "processing delay", "infrastructure bottleneck", "load balancing failure",
        "high latency", "low throughput", "scalability bottleneck", "overprovisioning", "underprovisioning",
        "resource contention", "service throttling", "peak load failure", "traffic surge", "demand spike",
        "expansion risk", "growth limitation", "operational ceiling", "system saturation", "concurrency issue",
        "parallel processing failure", "scaling cost overrun", "inadequate scaling", "dynamic scaling failure",
        "horizontal scaling issue", "vertical scaling limit", "multi-region failure", "geo-scaling risk",
        "service degradation", "operational failure", "system downtime", "node overload", "chain congestion",
        "transaction latency", "blockchain scalability issue", "network saturation", "processing bottleneck"
    },
    "interoperability": {
        "integration failure", "API breakdown", "interface mismatch", "protocol incompatibility",
        "data sync failure", "interoperability breakdown", "cross-chain failure", "bridge collapse",
        "interoperability risk", "connectivity loss", "network disconnection", "system integration risk",
        "data exchange failure", "middleware failure", "inter-system conflict", "communication breakdown",
        "sync delay", "interoperability gap", "cross-platform failure", "connection timeout",
        "data flow interruption", "integration latency", "system linkage failure", "interoperability bottleneck",
        "connectivity outage", "cross-ledger failure", "protocol mismatch", "data transfer failure",
        "interface disruption", "connectivity overload", "inter-system latency", "integration dependency risk",
        "cross-network failure", "interoperability overload", "connection instability", "data interoperability risk",
        "sync disruption", "bridge latency", "cross-chain exploit", "interoperability flaw", "chain isolation"
    },
    "market_risk": {
        "volatility", "market crash", "flash crash", "liquidity drain", "market manipulation",
        "pump and dump", "wash trading", "market distortion", "speculative risk", "liquidity risk",
        "counterparty risk", "market inefficiency", "overexposure", "undercollateralization", "financial loss",
        "price manipulation", "spoofing attack", "fake volume", "market spoofing", "liquidity squeeze",
        "volatility spike", "market bubble", "speculative bubble", "crash risk", "market exit scam",
        "token devaluation", "liquidity pool collapse", "arbitrage failure", "market illiquidity"
    },
    "general_operational": {
        "default", "bankruptcy", "embezzlement", "insolvency", "reputational risk",
        "stakeholder misunderstanding", "fund mismanagement", "investor fraud", "operational risk",
        "third-party failure", "vendor risk", "supply chain risk", "technology risk", "infrastructure risk",
        "misconduct", "false reporting", "executive risk", "team credibility", "financial opacity",
        "unverified claims", "conflict of interest", "insider threat", "systemic risk", "dependency risk",
        "vendor lock-in", "false positive", "vote manipulation", "DAO takeover", "team exit risk",
        "code audit failure", "centralization risk", "impermanent loss", "liquidity pool rug pull",
        "rebase instability", "yield farming collapse", "MEV exploitation", "governance token manipulation",
        "code vulnerability", "reentrancy", "unauthorized holdings", "audit gap", "trust violation",
        "financial misstatement", "collusion", "negligence", "operational lapse", "process failure",
        "human error", "governance breakdown", "team incompetence", "project abandonment", "fraudulent intent",
        "rug pull", "ponzi scheme", "exit scam", "pump and dump", "fake volume", "wash trading",
        "token scam", "whitepaper fraud", "yield farming scam", "liquidity drain", "insider rug pull"
    }
}

MITIGATION_TERMS = {
    "insured", "insurance policy", "SOC 2", "SOC 1", "ISO 27001",
    "penetration tested", "bug bounty", "audited", "smart contract audit",
    "cold storage", "segregated account", "multi-signature", "compliance team",
    "AML program", "KYC verified", "third-party custody", "firewall", "incident response plan",
    "data encryption", "threat monitoring", "disaster recovery", "regulatory approval",
    "registered with SEC", "regulated by CFTC", "BitLicense", "GDPR compliance", "SOC 2 implemented",
    "under FDIC protection", "compliant with MiCA", "regulated entity"
}

POSITIVE_TERMS = {
    "revolutionary", "guaranteed", "breakthrough", "unprecedented", "exceptional", "best-in-class",
    "leading", "pioneering", "flawless", "perfect", "assured", "top-tier", "game-changer", "stellar",
    "outstanding", "ultimate", "secure forever", "risk-free", "unmatched", "infallible"
}

KEYWORDS = FINANCIAL_TERMS | REGULATIONS | CRYPTO_TERMS | RISK_TERMS | ESG_TERMS | CYBERSECURITY_TERMS

REGION_TERMS = {
    "USA": 2.0, "United States": 2.0, "America": 2.0, "US": 2.0, "EU": 3.0, "European Union": 3.0,
    "UK": 2.5, "United Kingdom": 2.5, "Britain": 2.5, "Canada": 2.0, "CA": 2.0, "Australia": 2.0,
    "AU": 2.0, "Japan": 2.0, "JP": 2.0, "China": 4.0, "CN": 4.0, "India": 3.5, "IN": 3.5,
    "Singapore": 1.5, "SG": 1.5, "Hong Kong": 3.0, "HK": 3.0, "Switzerland": 1.5, "CH": 1.5,
    "Russia": 5.0, "RU": 5.0, "Brazil": 4.0, "BR": 4.0, "South Africa": 4.0, "ZA": 4.0,
    "New York": 2.5, "NY": 2.5, "California": 2.0, "London": 2.5, "Tokyo": 2.0, "Beijing": 4.0,
    "Delhi": 3.5, "Sydney": 2.0, "Texas": 2.0, "TX": 2.0, "Florida": 2.5, "FL": 2.5,
    "Illinois": 2.0, "IL": 2.0, "Ontario": 2.0, "Quebec": 2.0, "Shanghai": 4.0, "Mumbai": 3.5,
    "Washington, D.C.": 2.0, "Dubai": 3.0, "UAE": 3.0, "Cayman Islands": 4.5, "Bermuda": 4.5,
    "Malta": 3.5, "Gibraltar": 3.5, "Seychelles": 5.0, "Bahamas": 6.0
}

STATE_REGULATORS = {
    "NY": (["NYDFS", "BitLicense"], 3.0),
    "CA": (["DFPI", "California Department of Financial Protection and Innovation"], 2.5),
    "TX": (["Texas Department of Banking", "TX State Securities Board"], 2.0),
    "FL": (["Florida Office of Financial Regulation", "Florida OFR"], 2.5),
    "IL": (["Illinois Department of Financial and Professional Regulation"], 2.0),
    "MA": (["Massachusetts Securities Division"], 2.5),
    "NJ": (["New Jersey Bureau of Securities"], 2.0),
    "WA": (["Washington Department of Financial Institutions"], 2.0),
    "PA": (["Pennsylvania Department of Banking and Securities"], 2.0),
    "GA": (["Georgia Department of Banking and Finance"], 2.0),
    "MI": (["Michigan Department of Insurance and Financial Services"], 2.0),
    "OH": (["Ohio Division of Securities"], 2.0),
    "VA": (["Virginia State Corporation Commission"], 2.0),
    "NC": (["North Carolina Department of the Secretary of State Securities Division"], 2.0),
    "CO": (["Colorado Division of Securities"], 2.0),
    "MN": (["Minnesota Department of Commerce"], 2.0),
    "MO": (["Missouri Securities Division"], 2.0),
    "AZ": (["Arizona Corporation Commission Securities Division"], 2.0),
    "IN": (["Indiana Securities Division"], 2.0),
    "OR": (["Oregon Division of Financial Regulation"], 2.0),
    "TN": (["Tennessee Department of Commerce and Insurance"], 2.0),
    "WI": (["Wisconsin Department of Financial Institutions"], 2.0),
    "NV": (["Nevada Secretary of State Securities Division"], 2.0),
    "LA": (["Louisiana Office of Financial Institutions"], 2.0),
    "KY": (["Kentucky Department of Financial Institutions"], 2.0),
    "OK": (["Oklahoma Department of Securities"], 2.0),
    "SC": (["South Carolina Attorney General Securities Division"], 2.0),
    "AL": (["Alabama Securities Commission"], 2.0),
    "MS": (["Mississippi Secretary of State Securities Division"], 2.0),
    "AR": (["Arkansas Securities Department"], 2.0),
    "NM": (["New Mexico Regulation and Licensing Department"], 2.0),
    "UT": (["Utah Division of Securities"], 2.0),
    "IA": (["Iowa Insurance Division"], 2.0),
    "KS": (["Kansas Securities Commissioner"], 2.0),
    "NE": (["Nebraska Department of Banking and Finance"], 2.0),
    "ID": (["Idaho Department of Finance"], 2.0),
    "ME": (["Maine Office of Securities"], 2.0),
    "NH": (["New Hampshire Bureau of Securities Regulation"], 2.0),
    "VT": (["Vermont Department of Financial Regulation"], 2.0),
    "RI": (["Rhode Island Department of Business Regulation"], 2.0),
    "DE": (["Delaware Investor Protection Unit", "Delaware Department of Justice"], 2.0),
    "MT": (["Montana Securities Department"], 2.0),
    "ND": (["North Dakota Securities Department"], 2.0),
    "SD": (["South Dakota Division of Insurance Securities Regulation"], 2.0),
    "AK": (["Alaska Division of Banking and Securities"], 2.0),
    "HI": (["Hawaii Department of Commerce and Consumer Affairs"], 2.0),
    "WY": (["Wyoming Secretary of State Securities Division"], 2.0),
    "WV": (["West Virginia Securities Commission"], 2.0)
}

URL_PATTERN = re.compile(r'(https?://[^\s]+|www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')
CIK_PATTERN = re.compile(r'CIK\s*(\d{10})')

RISK_WEIGHTS = {
    "legal_regulatory": 5.0,
    "cyber_resilience": 4.5,
    "asset_safeguarding": 4.0,
    "market_risk": 3.5,
    "operational_scale": 3.0,
    "interoperability": 2.5,
    "general_operational": 2.0
}

# Entity Extraction Functions (unchanged except for extract_region)
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
    return list(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))

def extract_person_names(text):
    sentence = Sentence(text)
    flair_tagger.predict(sentence)
    return list(set(entity.text for entity in sentence.get_spans("ner") if entity.tag == "PER"))

def extract_financial_terms(text):
    text_lower = text.lower()
    return {
        "financial_terms": [term for term in FINANCIAL_TERMS if term.lower() in text_lower],
        "crypto_terms": [crypto for crypto in CRYPTO_TERMS if crypto in text],
        "risk_mentions": [risk for category in RISK_CATEGORIES.values() for risk in category if risk.lower() in text_lower]
    }

def calculate_risk_score(found_risks, sentiment_score, text_length, source_type="text", region="Unknown", text=""):
    raw_score = 0.0
    categories_hit = set()
    regulator_score = 0.0

    for risk in found_risks:
        risk_lower = risk.lower()
        if risk_lower in RISK_CATEGORIES["legal_regulatory"]:
            raw_score += RISK_WEIGHTS["legal_regulatory"]
            categories_hit.add("legal_regulatory")
        elif risk_lower in RISK_CATEGORIES["cyber_resilience"]:
            raw_score += RISK_WEIGHTS["cyber_resilience"]
            categories_hit.add("cyber_resilience")
        elif risk_lower in RISK_CATEGORIES["asset_safeguarding"]:
            raw_score += RISK_WEIGHTS["asset_safeguarding"]
            categories_hit.add("asset_safeguarding")
        elif risk_lower in RISK_CATEGORIES["operational_scale"]:
            raw_score += RISK_WEIGHTS["operational_scale"]
            categories_hit.add("operational_scale")
        elif risk_lower in RISK_CATEGORIES["interoperability"]:
            raw_score += RISK_WEIGHTS["interoperability"]
            categories_hit.add("interoperability")
        elif risk_lower in RISK_CATEGORIES["market_risk"]:
            raw_score += RISK_WEIGHTS["market_risk"]
            categories_hit.add("market_risk")
        else:
            raw_score += RISK_WEIGHTS["general_operational"]
            categories_hit.add("general_operational")

    category_count = len(categories_hit)
    raw_score += category_count * 1.5

    sentiment_factor = 1.0 + abs(sentiment_score) if sentiment_score < 0 else 1.0 - (sentiment_score * 0.5)
    raw_score *= sentiment_factor

    source_multiplier = 1.3 if source_type == "web" else 1.0
    raw_score *= source_multiplier

    # Use the first detected region's weight if multiple; default to 2.0 if "Unknown"
    region_weight = REGION_TERMS.get(region if isinstance(region, str) else region[0] if region else "Unknown", 2.0)
    raw_score *= (1 + (region_weight / 10))

    for state, (agencies, weight) in STATE_REGULATORS.items():
        if any(agency.lower() in text.lower() for agency in agencies):
            regulator_score += weight
    raw_score += regulator_score

    max_possible = (sum(RISK_WEIGHTS.values()) * 2 + 10 * 1.5 + max(REGION_TERMS.values()) + max(w for _, w in STATE_REGULATORS.values())) * 2
    normalized_score = min((raw_score / max_possible) * 10, 10)
    return normalized_score

def analyze_sentiment(text):
    scores = sentiment_analyzer.polarity_scores(text)
    compound_score = scores["compound"]
    risk_count = len([w for w in text.lower().split() if w in RISK_CATEGORIES["legal_regulatory"] or w in RISK_CATEGORIES["cyber_resilience"]])
    mitigation_count = len([w for w in text.lower().split() if w in {"mitigate", "solution", "control", "compliance", "robust"}])
    positive_count = len([w for w in text.lower().split() if w in POSITIVE_TERMS])

    if positive_count > 0 and risk_count > mitigation_count and compound_score > 0:
        compound_score -= 0.4
        logging.debug(f"False positivity detected: Reduced sentiment score by 0.4 due to {positive_count} positive terms near {risk_count} risks")

    if risk_count > mitigation_count and compound_score > 0:
        compound_score -= 0.3

    sentiment = "positive" if compound_score >= 0.05 else "negative" if compound_score <= -0.05 else "neutral"
    return {"sentiment": sentiment, "sentiment_score": compound_score}

# Enhanced Region Extraction with NLP
def extract_region(text):
    """
    Extract all regions/countries involved in the text using spaCy NER and REGION_TERMS.
    Returns a list of detected regions; empty list if none found.
    """
    text_lower = text.lower()
    
    # Step 1: Use spaCy NER to detect geopolitical entities (GPE)
    doc = nlp(text)
    ner_regions = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    
    # Step 2: Cross-reference with REGION_TERMS for consistency
    term_regions = [region for region in REGION_TERMS.keys() if region.lower() in text_lower]
    
    # Step 3: Combine and deduplicate results
    combined_regions = list(set(ner_regions + term_regions))
    
    # Step 4: Filter for country-like entities and handle ambiguous cases
    countries = {"USA", "United States", "US", "America", "Canada", "UK", "United Kingdom", "Britain", 
                 "Australia", "Japan", "China", "India", "Singapore", "Hong Kong", "Switzerland", 
                 "Russia", "Brazil", "South Africa", "EU", "European Union"}
    
    detected = []
    for region in combined_regions:
        region_lower = region.lower()
        if region_lower in {c.lower() for c in countries}:
            detected.append(region)
        elif region in REGION_TERMS and region_lower not in {"ny", "ca", "tx", "fl", "il"}:  # Exclude state codes unless country context
            detected.append(region)
    
    return detected if detected else ["Unknown"]

def detect_state_risks(text):
    detected = []
    text_lower = text.lower()
    for state, (agencies, weight) in STATE_REGULATORS.items():
        for agency in agencies:
            if agency.lower() in text_lower:
                profile = {
                    "state": state,
                    "agency": agency,
                    "weight": weight,
                    "laws": []
                }
                if state == "NY":
                    profile["laws"].append("BitLicense requirement")
                elif state == "TX":
                    profile["laws"].append("Texas Money Services Act")
                elif state == "DE":
                    profile["laws"].append("Delaware Corporate Law")
                elif state == "CA":
                    profile["laws"].append("California Consumer Privacy Act")
                detected.append((state, profile))
    return detected

def detect_mitigation_terms(text):
    text_lower = text.lower()
    return [term for term in MITIGATION_TERMS if term.lower() in text_lower]

risk_embeddings = {cat: model.encode(list(sentences)) for cat, sentences in RISK_CATEGORIES.items()}

def infer_latent_risks(text, threshold=0.60):
    detected = []
    embedding = model.encode(text)
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

    companies = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    persons = [entity.text for entity in sentence.get_spans("ner") if entity.tag == "PER"]
    financial_analysis = extract_financial_terms(chunk_text)
    sentiment_data = analyze_sentiment(chunk_text)
    regions = extract_region(chunk_text)  # Now returns a list
    risk_score = calculate_risk_score(
        financial_analysis["risk_mentions"],
        sentiment_data["sentiment_score"],
        len(chunk_text.split()),
        source_type,
        regions,  # Pass the list directly
        chunk_text
    )
    state_profile = detect_state_risks(chunk_text)

    return {
        "emails": extract_emails(chunk_text),
        "companies": companies,
        "persons": list(set(persons)),
        "phone_numbers": extract_phone_numbers(chunk_text),
        "addresses": extract_addresses(chunk_text),
        "urls": extract_websites(chunk_text),
        "cik_numbers": extract_cik_numbers(chunk_text),
        "financial_terms": financial_analysis["financial_terms"],
        "crypto_terms": financial_analysis["crypto_terms"],
        "risk_mentions": financial_analysis["risk_mentions"],
        "risk_score": risk_score,
        "sentiment": sentiment_data["sentiment"],
        "sentiment_score": sentiment_data["sentiment_score"],
        "mitigation_terms": detect_mitigation_terms(chunk_text),
        "latent_risks": infer_latent_risks(chunk_text),
        "state_regulators": [agency for _, agency in state_profile],
        "state_profile": state_profile,
        "region": regions  # Updated to reflect list output
    }