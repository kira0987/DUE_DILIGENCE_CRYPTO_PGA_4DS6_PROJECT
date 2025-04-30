import streamlit as st
import json
import numpy as np
from langchain.vectorstores import FAISS as LangchainFAISS
from langchain_core.documents import Document
from langchain_community.llms import Ollama
from langchain.embeddings import HuggingFaceEmbeddings
import logging
import requests
from datetime import datetime
import os
import time

# 🧠 Load Ollama LLM
llm = Ollama(model="mistral:7b-instruct-q4_0")

logging.basicConfig(filename="rag.log", level=logging.INFO)

# ========== Constants ==========
TRUSTED_SOURCES = [
    "reuters.com", "bloomberg.com", "coindesk.com", "wsj.com",
    "ft.com", "forbes.com", "sec.gov", "cftc.gov"
]
CRYPTO_KEYWORDS = ["SEC", "KYC", "AML", "DeFi", "smart contract", "token", "DAO", "custody", "blockchain"]
CURRENT_MONTH = "April 2025"
CONTEXT_LIMIT = 800  # Words for Mistral 7B's 32K token window (~4 tokens/word)
MIN_RISK_SCORE = 0.5  # Filter whitepapers with scaled_score >= 0.5

# ========== Helper Functions ==========
def load_embedded_json(file_obj):
    return json.load(file_obj)

def detect_dim(data):
    for item in data:
        emb = item.get("embedding", [])
        if isinstance(emb, list) and len(emb) > 0:
            return len(emb)
    return 0

def summarize_metadata(metadata):
    """Summarize metadata to fit context limit."""
    summary = []
    if 'matched_keywords' in metadata:
        summary.append(f"Keywords: {', '.join(metadata['matched_keywords'][:5])}")
    if 'sentiment' in metadata:
        summary.append(f"Sentiment: {metadata['sentiment']} ({metadata.get('sentiment_score', 0):.2f})")
    if 'risk_score' in metadata:
        summary.append(f"Risk Score: {metadata['risk_score'].get('scaled_score', 0):.2f}")
    if 'entities' in metadata:
        entities = metadata['entities']
        if entities.get('companies'):
            summary.append(f"Companies: {', '.join(entities['companies'][:3])}")
        if entities.get('financial_terms'):
            summary.append(f"Financial Terms: {', '.join(entities['financial_terms'][:3])}")
        if entities.get('crypto_terms'):
            summary.append(f"Crypto Terms: {', '.join(entities['crypto_terms'][:3])}")
        if entities.get('risk_mentions'):
            summary.append(f"Risk Mentions: {', '.join(entities['risk_mentions'][:3])}")
    if 'fund_metrics' in metadata:
        metrics = metadata['fund_metrics']
        summary.append(f"Fund Metrics: ROI={metrics.get('roi', 0)}, Stage={metrics.get('stage', 'Unknown')}")
    if 'source' in metadata:
        summary.append(f"Source: {metadata['source'].split('/')[-1]}")
    if 'region' in metadata:
        summary.append(f"Region: {', '.join(metadata['region'])}")
    return "; ".join(summary)[:200]  # Limit to 200 chars

def extract_documents_and_vectors(data, expected_dim):
    docs, vectors = [], []
    for item in data:
        text = item.get("question") or item.get("text")
        embedding = np.array(item.get("embedding", []), dtype=np.float32)
        if text and embedding.shape[0] == expected_dim:
            metadata = item.get("metadata", {})
            # Filter by risk score for whitepapers
            if 'risk_score' in metadata and metadata['risk_score'].get('scaled_score', 0) < MIN_RISK_SCORE:
                continue
            # Include full metadata in Document
            doc_metadata = metadata.copy()
            doc_metadata['summary'] = summarize_metadata(metadata)
            docs.append(Document(page_content=text, metadata=doc_metadata))
            vectors.append(embedding)
    return docs, np.array(vectors, dtype=np.float32)

def build_vector_store(docs):
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return LangchainFAISS.from_documents(docs, embedding_model)

def count_words(text):
    return len(text.split())

def fetch_real_time_news(query, api_key, max_results=3):
    cache_dir = "news_cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = f"{cache_dir}/{query.replace(' ', '_')}.json"
    
    # Check cache (valid for 2 hours)
    if os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < 7200:
        with open(cache_file, 'r') as f:
            return [Document(page_content=content, metadata={'source': 'web', 'date': 'Cached'}) for content in json.load(f)]
    
    news_docs = []
    try:
        url = "https://google.serper.dev/news"
        payload = json.dumps({"q": f"{query} crypto {CURRENT_MONTH}", "num": max_results * 2})
        headers = {'726f689eb88a9b66e0fe5897284c1a2feaa21969': api_key, 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        results = response.json().get('news', [])
        
        for item in results:
            link = item.get('link', '').lower()
            date_str = item.get('date', '')
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            content = f"{title}\n{snippet}\n(Date: {date_str})"
            
            # Source filter
            if not any(source in link for source in TRUSTED_SOURCES):
                continue
                
            # Date filter
            try:
                news_date = datetime.strptime(date_str, '%Y-%m-%d')
                if news_date.year != 2025 or news_date.month != 4:
                    continue
            except ValueError:
                continue
                
            # Keyword relevance filter
            if not any(keyword.lower() in content.lower() for keyword in CRYPTO_KEYWORDS):
                continue
                
            # Content length filter
            if count_words(content) > 200:
                content = ' '.join(content.split()[:200]) + "..."
                
            news_docs.append(Document(
                page_content=content,
                metadata={'source': link, 'date': date_str, 'query': query}
            ))
            if len(news_docs) >= max_results:
                break
                
        # Cache results
        if news_docs:
            with open(cache_file, 'w') as f:
                json.dump([doc.page_content for doc in news_docs], f)
                
        logging.info(f"[SEARCH] Fetched {len(news_docs)} news items for query '{query}' in {response.elapsed.total_seconds()}s")
    except Exception as e:
        logging.error(f"[SEARCH ERROR] {str(e)}")
    return news_docs

def query_rag(query, vectorstore, use_web_search=False, serper_api_key=None):
    try:
        # Fetch static context
        results = vectorstore.similarity_search_with_score(query, k=3)
        context_chunks = []
        total_words = 0
        for r in results:
            if isinstance(r, tuple) and len(r) == 2:
                doc, score = r
                content = doc.page_content.strip()[:200]
                metadata_summary = doc.metadata.get('summary', '')
                chunk = f"- {content}... (Score: {score:.2f}, Metadata: {metadata_summary})"
                words = count_words(chunk)
                if total_words + words <= CONTEXT_LIMIT // 2:
                    context_chunks.append(chunk)
                    total_words += words
            else:
                logging.warning(f"Unexpected result format: {r}")

        # Fetch real-time news
        web_context = []
        if use_web_search and serper_api_key:
            news_docs = fetch_real_time_news(query, serper_api_key)
            if news_docs:
                embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                temp_vectorstore = LangchainFAISS.from_documents(news_docs, embedding_model)
                news_results = temp_vectorstore.similarity_search_with_score(query, k=2)
                for r in news_results:
                    doc, score = r
                    content = doc.page_content.strip()
                    words = count_words(content)
                    if total_words + words <= CONTEXT_LIMIT:
                        web_context.append(f"- {content[:200]}... (Web Score: {score:.2f}, Source: {doc.metadata['source']})")
                        total_words += words

        context = "\n".join(context_chunks + web_context) if context_chunks or web_context else "No relevant context found."

        prompt = f"""
You are an intelligent, real-time-aware risk analysis agent specializing in crypto funds, digital assets, and blockchain-based organizations.

Your task is to analyze all relevant risks and extract key insights using the provided context. You must remain current with real-world events — in crypto, regulations change rapidly, funds may collapse or surge overnight, and new exceptions emerge in short timeframes.

---
📌 **Query**: {query}

📚 **Context**:
{context}

---
🎯 **Instructions**:
1. Interpret the context holistically. The information may include news articles, whitepaper metadata, or summaries. Some content may refer to rapidly evolving events or volatile fund activity — prioritize recency, relevance, and factual clarity.
2. Understand that **real-time events are critical**. A project or fund could be compliant yesterday but non-compliant today. Risk may arise due to regulation, sentiment, liquidity, or governance shifts.
3. Always detect and clearly identify **company or fund names**, jurisdictions, and project affiliations mentioned in the content. These must be used to anchor any conclusions.
4. Focus on extracting and explaining insights related to:
   - Governance
   - Technology and infrastructure
   - Legal and regulatory posture
   - Investor communication and transparency
   - Custody and access control
   - Market dynamics, momentum, or sentiment shifts
5. If data is missing or unclear (e.g., no CIK, no ROI disclosed, no audit), explicitly highlight that.
6. Do not speculate beyond what the content supports.

---
📋 **Response Format**:

🧩 **Key Observations**
- Summarize specific facts from the content (e.g., company names, partnerships, events, dates, scores).

📊 **Risk Insights**
- Outline any risks identified in the following domains:
  - Legal & Compliance
  - Technical Infrastructure
  - Custody & Access Control
  - Governance & Organizational Clarity
  - Investor Transparency & Market Behavior
  - Real-time Sensitivity (e.g., news-driven volatility)

🚨 **Red or Yellow Flags**
- List any notable concerns (e.g., token control features, ambiguous jurisdiction, recent collapses, lack of disclosures).

📌 **Detected Entities & Metadata**
- Company/Fund Names:
- Jurisdictions:
- Risk Scores or Ratings:
- Key Financial or Legal Terms Mentioned:

📉 **Summary Assessment**
- Conclude with a clear sentence summarizing the project’s current health or risk posture based on the latest available context.

Maintain precision, transparency, and structured reasoning. Avoid assumptions.
"""

        response = llm(prompt)
        return response, context

    except Exception as e:
        logging.error(f"[QUERY ERROR] {str(e)}")
        return f"Error processing query: {str(e)}", ""

def batch_query_rag(queries, vectorstore, use_web_search=False, serper_api_key=None):
    import concurrent.futures
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_query = {executor.submit(query_rag, q, vectorstore, use_web_search, serper_api_key): q for q in queries}
        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            try:
                result = future.result(timeout=90)
                if isinstance(result, tuple) and len(result) == 2:
                    results.append(result)
                else:
                    results.append((f"Invalid result format for query: {query}", ""))
            except concurrent.futures.TimeoutError:
                logging.error(f"Query '{query}' timed out.")
                results.append(("Query timed out after 90 seconds.", ""))
            except Exception as e:
                logging.error(f"Query '{query}' failed: {str(e)}")
                results.append((f"Query failed: {str(e)}", ""))
    return results

# ========== Streamlit UI ==========
st.set_page_config(page_title="🛡️ Crypto RAG Risk Analyzer")
st.title("📊 Crypto Fund Risk Assessment")
st.subheader("LLM + RAG with embedded questions, whitepapers, and real-time news")

st.sidebar.header("📁 Upload Files")
q_file = st.sidebar.file_uploader("Upload `embedded_questions.json`", type="json")
wp_files = st.sidebar.file_uploader("Upload embedded whitepapers", type="json", accept_multiple_files=True)

st.sidebar.header("🌐 Real-Time News Search")
use_web_search = st.sidebar.checkbox("Enable real-time news search", value=False)
serper_api_key = st.sidebar.text_input("Serper API Key (required for news search)", type="password")

if q_file and wp_files:
    with st.spinner("🔎 Parsing and Validating Files..."):
        try:
            q_data = load_embedded_json(q_file)
            embedding_dim = detect_dim(q_data)
            if not embedding_dim:
                st.error("❌ Invalid or empty question embeddings.")
                st.stop()

            q_docs, q_vecs = extract_documents_and_vectors(q_data, expected_dim=embedding_dim)
            all_docs = q_docs[:]

            for file in wp_files:
                wp_data = load_embedded_json(file)
                wp_docs, wp_vecs = extract_documents_and_vectors(wp_data, expected_dim=embedding_dim)
                all_docs.extend(wp_docs)

            vectorstore = build_vector_store(all_docs)
            st.success(f"✅ Loaded {len(all_docs)} docs | Embedding dim: {embedding_dim}")

            queries = st.text_area("📥 Enter your due diligence questions:", height=160, placeholder="e.g., What are the latest SEC regulations for crypto funds in April 2025?")
            if st.button("🚀 Analyze"):
                if use_web_search and not serper_api_key:
                    st.error("❌ Please provide a Serper API key for real-time news search.")
                    st.stop()
                query_list = [q.strip() for q in queries.splitlines() if q.strip()]
                results = batch_query_rag(query_list, vectorstore, use_web_search, serper_api_key)
                for i, query in enumerate(query_list):
                    st.markdown(f"### 📈 Analysis for: `{query}`")
                    response, context = results[i]
                    with st.expander("🔍 View Context"):
                        st.markdown(context or "*No matching context found.*")
                    st.markdown("#### Expert Assessment")
                    st.markdown(response)

        except Exception as e:
            st.error(f"❌ Fatal error: {e}")
else:
    st.warning("📂 Upload both the embedded questions and at least one whitepaper file.")