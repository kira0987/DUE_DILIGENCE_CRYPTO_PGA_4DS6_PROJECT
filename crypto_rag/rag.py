import streamlit as st
import json
import numpy as np
from langchain.vectorstores import FAISS as LangchainFAISS
from langchain_core.documents import Document
from langchain_community.llms import Ollama
from langchain.embeddings import HuggingFaceEmbeddings
import logging

# 🧠 Load Ollama LLM
llm = Ollama(model="mistral:7b-instruct-q4_0")

logging.basicConfig(filename="rag.log", level=logging.INFO)

# ========== Helper Functions ==========
def load_embedded_json(file_obj):
    return json.load(file_obj)

def detect_dim(data):
    for item in data:
        emb = item.get("embedding", [])
        if isinstance(emb, list) and len(emb) > 0:
            return len(emb)
    return 0

def extract_documents_and_vectors(data, expected_dim):
    docs, vectors = [], []
    for item in data:
        text = item.get("question") or item.get("text")
        embedding = np.array(item.get("embedding", []), dtype=np.float32)
        if text and embedding.shape[0] == expected_dim:
            metadata = item.get("metadata", {})
            docs.append(Document(page_content=text, metadata=metadata))
            vectors.append(embedding)
    return docs, np.array(vectors, dtype=np.float32)

def build_vector_store(docs):
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return LangchainFAISS.from_documents(docs, embedding_model)

def query_rag(query, vectorstore):
    try:
        results = vectorstore.similarity_search_with_score(query, k=5)
        context_chunks = []
        for r in results:
            if isinstance(r, tuple) and len(r) == 2:
                doc, score = r
                content = doc.page_content.strip()
                context_chunks.append(f"- {content[:200]}... (Score: {score:.2f})")
            else:
                logging.warning(f"Unexpected result format: {r}")

        if not context_chunks:
            return "No relevant context found.", ""

        context = "\n".join(context_chunks)

        prompt = f"""
You are a multidisciplinary crypto fund risk intelligence officer.

Your role combines U.S. legal expertise, SEC compliance insight, blockchain auditing, smart contract analysis, and investor protection standards.

Your goal is to **inductively assess risks** by starting from the specific evidence in the context, then generalizing patterns and verdicts across key categories.

---
📌 **Query:** {query}

📚 **Context:**
{context}

---
🎓 **Your Role:** U.S.-oriented crypto fund lawyer, risk analyst, and regulator.

Respond with a professional audit report using this format:

---
🧩 **Key Observations**
- Highlight specific facts from context: controls, compliance flags, smart contract roles, dates, jurisdictions, team members, CIK numbers, or structural claims.

📊 **Risk Analysis**
- Evaluate implications for each risk category:
    - ⚖️ *Legal*: SEC violations, securities law, KYC/AML.
    - 🛠️ *Technical*: Smart contract vulnerabilities, kill switches, role control.
    - 🔐 *Custody & Access*: Token freeze features, control mechanisms.
    - 💼 *Governance*: DAO/LLC/SPV structure, team transparency.
    - 📈 *Investor Risk*: Lockup misalignment, unclear utility, lack of disclosures.
    - 📍 *Jurisdiction & Regulator Fit*: U.S.-based or foreign shell.

🚨 **Red Flags**
- State clear inconsistencies, overpromises, or regulatory evasion.

📌 **Detected Metadata**
- CIK: [if available]
- Emails / URLs / Addresses
- Jurisdictions: U.S. states or offshore regions
- Financial / Regulatory / Crypto terms matched

📉 **Seriousness Rating**
- Rate numerically per category: `0 (None)` to `5 (Critical)`
- Conclude with weighted total risk score: `Final Score = X/30`

⚖️ **Verdict**
- `✅ Low Risk` → no major findings
- `⚠️ Medium Risk` → mitigatable concerns
- `🚨 High Risk` → potential violation or fraud concern

📎 **U.S. Regulatory Action Recommendation**
- Suggest actions for auditors, lawyers, or SEC (e.g. 10-K audit, freeze risk, Reg D exemption review).

Respond with clarity, precision, and rich formatting (emojis, bullets, scores).
"""
        response = llm(prompt)
        return response, context

    except Exception as e:
        logging.error(f"[QUERY ERROR] {str(e)}")
        return f"Error processing query: {str(e)}", ""

def batch_query_rag(queries, vectorstore):
    import concurrent.futures
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_query = {executor.submit(query_rag, q, vectorstore): q for q in queries}
        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            try:
                result = future.result(timeout=60)
                if isinstance(result, tuple) and len(result) == 2:
                    results.append(result)
                else:
                    results.append((f"Invalid result format for query: {query}", ""))
            except concurrent.futures.TimeoutError:
                logging.error(f"Query '{query}' timed out.")
                results.append(("Query timed out after 60 seconds.", ""))
            except Exception as e:
                logging.error(f"Query '{query}' failed: {str(e)}")
                results.append((f"Query failed: {str(e)}", ""))
    return results

# ========== Streamlit UI ==========
st.set_page_config(page_title="🛡️ Crypto RAG Risk Analyzer")
st.title("📊 Crypto Fund Risk Assessment")
st.subheader("LLM + RAG with embedded questions and whitepapers")

st.sidebar.header("📁 Upload Files")
q_file = st.sidebar.file_uploader("Upload `embedded_questions.json`", type="json")
wp_files = st.sidebar.file_uploader("Upload embedded whitepapers", type="json", accept_multiple_files=True)

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

            queries = st.text_area("📥 Enter your due diligence questions:", height=160)
            if st.button("🚀 Analyze"):
                query_list = [q.strip() for q in queries.splitlines() if q.strip()]
                results = batch_query_rag(query_list, vectorstore)
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
