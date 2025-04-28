import pandas as pd
import os
import asyncio
import aiohttp
import json
from tqdm import tqdm
import random
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import spacy
from flair.data import Sentence
from flair.models import SequenceTagger
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

model = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("en_core_web_lg")
flair_tagger = SequenceTagger.load("flair/ner-english-large")
sentiment_analyzer = SentimentIntensityAnalyzer()

CSV_PATH = "sec_edgar_daily_indexes_2014_2025.csv"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/"
OUTPUT_DIR = "sec_filings/"
CACHE_DIR = os.path.join(OUTPUT_DIR, "cache")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {"User-Agent": "CryptoDueDiligence (houssameddine.benkheder@esprit.tn)", "Accept-Encoding": "gzip, deflate", "Host": "www.sec.gov"}

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
        # Expanded nuanced red flags
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



RISK_WEIGHTS = {
    "legal_regulatory": 5.0,
    "cyber_resilience": 4.5,
    "asset_safeguarding": 4.0,
    "market_risk": 3.5,
    "operational_scale": 3.0,
    "interoperability": 2.5,
    "general_operational": 2.0
}


def clean_filing_text(raw_text):
    return re.sub(r'\s+', ' ', raw_text).strip()

async def fetch_sec_filing(session, url, cache_path, pbar):
    try:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                text = await response.text()
                cleaned_text = clean_filing_text(text)
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)
                pbar.update(1)
                return cleaned_text
            else:
                pbar.update(1)
                return ""
    except:
        pbar.update(1)
        return ""

async def fetch_all_filings(cik, filing_records):
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
        with tqdm(total=len(filing_records), desc=f"Fetching Filings for CIK {cik}", unit="file") as pbar:
            tasks = []
            for row in filing_records:
                accession = row['File Name'].split('/')[-1].replace('.txt', '')
                cache_path = os.path.join(CACHE_DIR, f"{accession}.txt")
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        tasks.append(asyncio.to_thread(lambda x: x, f.read()))
                else:
                    url = f"{SEC_ARCHIVES_URL}edgar/data/{cik}/{accession.replace('-', '')}/{accession}.txt"
                    tasks.append(fetch_sec_filing(session, url, cache_path, pbar))
                    await asyncio.sleep(random.uniform(0.1, 0.5))
            return await asyncio.gather(*tasks)

def extract_entities(text):
    doc = nlp(text)
    sentence = Sentence(text)
    flair_tagger.predict(sentence)
    crypto_mentions = {term: text.lower().count(term.lower()) for term in CRYPTO_TERMS if term.lower() in text.lower()}
    total_crypto = sum(crypto_mentions.values())
    currency_pattern = re.compile(r'(\d+\.?\d*)\s*(USD|BTC|ETH|bitcoin|ethereum)', re.IGNORECASE)
    currencies = currency_pattern.findall(text)
    risk_mentions = [risk for category in RISK_CATEGORIES.values() for risk in category if risk.lower() in text.lower()]
    sentiment = sentiment_analyzer.polarity_scores(text)["compound"]
    risk_score = sum(RISK_WEIGHTS[cat] for cat in RISK_CATEGORIES if any(r in RISK_CATEGORIES[cat] for r in risk_mentions)) * (1 + abs(sentiment) if sentiment < 0 else 1 - sentiment * 0.5)
    return {
        "crypto_terms": crypto_mentions,
        "total_crypto_mentions": total_crypto,
        "currencies": [{"amount": float(amount), "currency": curr.upper()} for amount, curr in currencies],
        "risk_mentions": risk_mentions,
        "risk_score": min(risk_score / 100, 10),
        "sentiment": "positive" if sentiment >= 0.05 else "negative" if sentiment <= -0.05 else "neutral",
        "companies": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
        "persons": [entity.text for entity in sentence.get_spans("ner") if entity.tag == "PER"]
    }

def preprocess(cik):
    print(f"Processing CIK: {cik}")
    df = pd.read_csv(CSV_PATH, chunksize=100000)
    matching_filings = pd.concat([chunk[chunk['CIK'].astype(str) == cik] for chunk in df])
    if matching_filings.empty:
        print(f"No filings found for CIK {cik}")
        return
    company_name = matching_filings.iloc[0]['Company Name'].replace('/', '_')
    filings = asyncio.run(fetch_all_filings(cik, matching_filings.to_dict('records')))
    all_chunks = []
    for filing in filings:
        words = filing.split()
        for i in range(0, len(words), 10000):
            chunk = ' '.join(words[i:i + 10000])
            embedding = model.encode(chunk).tolist()
            metadata = extract_entities(chunk)
            metadata["text"] = chunk
            metadata["embedding"] = embedding
            all_chunks.append(metadata)
    output_folder = os.path.join(OUTPUT_DIR, f"{company_name}_{cik}")
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"{company_name}_{cik}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)
    print(f"Saved embeddings and metadata to {output_file}")

if __name__ == "__main__":
    cik = input("Enter CIK number: ").strip()
    if cik.isdigit():
        preprocess(cik)
    else:
        print("CIK must be numeric.")