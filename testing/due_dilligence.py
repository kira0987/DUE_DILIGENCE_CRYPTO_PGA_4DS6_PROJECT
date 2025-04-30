import os
import json
import logging
import requests
from sec_edgar_api import EdgarClient
from bs4 import BeautifulSoup
from github import Github
from sentence_transformers import SentenceTransformer
from .utils import extract_entities, analyze_sentiment, calculate_risk_score, BASE_RISK_CATEGORIES, KEYWORDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize models and clients
edgar_client = EdgarClient(user_agent="CryptoDueDiligence/1.0")
model = SentenceTransformer('all-distilroberta-v1')
github_client = Github()  # Add your GitHub token if rate-limited: Github("your_token")

# --- SEC Filings ---
def fetch_sec_filings(cik_or_ticker, output_dir, form_types=["10-K", "8-K", "S-1"]):
    """
    Fetch SEC filings for a given CIK or ticker and process them for risk analysis.
    Returns extracted text and metadata for pipeline integration.
    """
    try:
        # Attempt to fetch company info using CIK or ticker
        company_info = edgar_client.get_company_info(cik=cik_or_ticker)
        cik = company_info["cik"]
        logging.info(f"Fetching SEC filings for CIK: {cik}")
        
        # Fetch recent filings of specified types
        filings = []
        for form in form_types:
            filing_data = edgar_client.get_filings(cik=cik, form_type=form, limit=1)
            if filing_data and "entries" in filing_data:
                filings.extend(filing_data["entries"])
        
        if not filings:
            logging.warning(f"No filings found for CIK: {cik}")
            return None, None
        
        # Process each filing
        sec_data = []
        for filing in filings:
            url = filing["link"]
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator=" ")
            
            # Extract key sections (e.g., Risk Factors, Management Discussion)
            sections = {"Item 1A": "", "Item 7": ""}
            for section in sections:
                start = text.find(section)
                if start != -1:
                    end = text.find("Item", start + 1) if "Item" in text[start + 1:] else len(text)
                    sections[section] = text[start:end].strip()
            
            # Save raw text for pipeline processing
            output_file = os.path.join(output_dir, f"{cik}_{filing['form_type']}_filing.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            logging.info(f"SEC filing saved to: {output_file}")
            
            # Analyze sections
            for section_name, section_text in sections.items():
                if section_text:
                    entities, anonymized_text = extract_entities(section_text, source_type="sec")
                    sentiment_data = analyze_sentiment(anonymized_text)
                    metadata = {
                        "source": url,
                        "form_type": filing["form_type"],
                        "section": section_name,
                        "entities": entities,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["sentiment_score"],
                        "risk_score": entities["risk_score"]
                    }
                    sec_data.append({
                        "text": anonymized_text,
                        "metadata": metadata
                    })
        
        return sec_data, output_file
    except Exception as e:
        logging.error(f"Failed to fetch SEC filings for {cik_or_ticker}: {str(e)}")
        return None, None

# --- ETF Analysis ---
def fetch_etf_data(etf_ticker, output_dir):
    """
    Fetch ETF prospectus or metadata and extract key metrics for comparison.
    Uses SEC EDGAR as a source (simplified here; extend with other APIs if needed).
    """
    try:
        # Simplified: Assume ticker links to SEC filing (e.g., S-1 prospectus)
        # In practice, use financial APIs like Yahoo Finance or iShares for metadata
        filing_data = edgar_client.get_filings(ticker=etf_ticker, form_type="S-1", limit=1)
        if not filing_data or "entries" not in filing_data:
            logging.warning(f"No ETF data found for {etf_ticker}")
            return None, None
        
        filing = filing_data["entries"][0]
        url = filing["link"]
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ")
        
        # Extract key metrics (simplified regex-based; refine with proper parsing)
        aum = re.search(r"Assets Under Management.*?\$([\d,.]+)", text, re.IGNORECASE)
        expense_ratio = re.search(r"Expense Ratio.*?(\d+\.\d+%)", text, re.IGNORECASE)
        risk_section = text.find("Risk Factors") != -1 and text[text.find("Risk Factors"):text.find("Item", text.find("Risk Factors") + 1)].strip()
        
        # Save raw text
        output_file = os.path.join(output_dir, f"{etf_ticker}_etf.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        logging.info(f"ETF data saved to: {output_file}")
        
        # Process risk section if present
        if risk_section:
            entities, anonymized_text = extract_entities(risk_section, source_type="etf")
            sentiment_data = analyze_sentiment(anonymized_text)
            metadata = {
                "source": url,
                "aum": aum.group(1) if aum else "Unknown",
                "expense_ratio": expense_ratio.group(1) if expense_ratio else "Unknown",
                "entities": entities,
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["sentiment_score"],
                "risk_score": entities["risk_score"]
            }
            return [{"text": anonymized_text, "metadata": metadata}], output_file
        return None, output_file
    except Exception as e:
        logging.error(f"Failed to fetch ETF data for {etf_ticker}: {str(e)}")
        return None, None

# --- Smart Contract Audits (GitHub) ---
def analyze_github_repo(repo_url, output_dir):
    """
    Fetch GitHub repo contents and analyze for audit reports or warnings.
    """
    try:
        repo_name = repo_url.split("github.com/")[-1].rstrip("/")
        repo = github_client.get_repo(repo_name)
        contents = repo.get_contents("")
        
        audit_data = []
        for content in contents:
            if "audit" in content.name.lower() or content.name.lower() in ["readme.md", "security.md"]:
                file_content = content.decoded_content.decode("utf-8")
                entities, anonymized_text = extract_entities(file_content, source_type="github")
                sentiment_data = analyze_sentiment(anonymized_text)
                
                # Check for warning keywords
                warnings = [kw for kw in ["vulnerability", "failed", "issue", "exploit"] if kw in file_content.lower()]
                metadata = {
                    "source": content.html_url,
                    "file_name": content.name,
                    "warnings": warnings,
                    "entities": entities,
                    "sentiment": sentiment_data["sentiment"],
                    "sentiment_score": sentiment_data["sentiment_score"],
                    "risk_score": entities["risk_score"]
                }
                audit_data.append({
                    "text": anonymized_text,
                    "metadata": metadata
                })
        
        # Save raw content
        output_file = os.path.join(output_dir, f"{repo_name.replace('/', '_')}_github.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join([c.decoded_content.decode("utf-8") for c in contents if c.type == "file"]))
        logging.info(f"GitHub repo data saved to: {output_file}")
        
        return audit_data, output_file
    except Exception as e:
        logging.error(f"Failed to analyze GitHub repo {repo_url}: {str(e)}")
        return None, None

# --- Token Metrics (CoinGecko) ---
def fetch_token_metrics(token_id, output_dir):
    """
    Fetch token metrics from CoinGecko to verify whitepaper claims and assess market risk.
    """
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{token_id}"
        response = requests.get(url, timeout=10)
        token_data = response.json()
        
        # Extract key metrics
        metrics = {
            "price": token_data["market_data"]["current_price"]["usd"],
            "volume_24h": token_data["market_data"]["total_volume"]["usd"],
            "market_cap": token_data["market_data"]["market_cap"]["usd"],
            "circulating_supply": token_data["market_data"]["circulating_supply"],
            "price_change_24h": token_data["market_data"]["price_change_percentage_24h"]
        }
        
        # Save as JSON for reference
        output_file = os.path.join(output_dir, f"{token_id}_token_metrics.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)
        logging.info(f"Token metrics saved to: {output_file}")
        
        # Generate text summary for analysis
        summary_text = f"Token: {token_id}\nPrice: ${metrics['price']}\n24h Volume: ${metrics['volume_24h']}\nMarket Cap: ${metrics['market_cap']}\nCirculating Supply: {metrics['circulating_supply']}\n24h Change: {metrics['price_change_24h']}%"
        entities, anonymized_text = extract_entities(summary_text, source_type="token")
        sentiment_data = analyze_sentiment(anonymized_text)
        metadata = {
            "source": url,
            "metrics": metrics,
            "entities": entities,
            "sentiment": sentiment_data["sentiment"],
            "sentiment_score": sentiment_data["sentiment_score"],
            "risk_score": entities["risk_score"]
        }
        
        return [{"text": anonymized_text, "metadata": metadata}], output_file
    except Exception as e:
        logging.error(f"Failed to fetch token metrics for {token_id}: {str(e)}")
        return None, None