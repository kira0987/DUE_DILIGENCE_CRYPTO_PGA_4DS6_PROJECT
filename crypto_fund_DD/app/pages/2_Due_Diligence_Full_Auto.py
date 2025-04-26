import os
import glob
import shutil
import re
import json
import streamlit as st

from scripts.extraction_and_cleaning import process_uploaded_file
from scripts.semantic_chunker import main as chunking_main
from scripts.embed_chunks import main as embedding_main
from scripts.build_graph import main as graph_build_main
from scripts.graph_rag_retriever import retrieve_context
from scripts.llm_responder import ask_llm, evaluate_answer, check_faithfulness, classify_question, detect_and_structure_gaps, ask_llm_raw
from scripts.intelligent_scraper import intelligent_scrape

# --- JSON Extractor Helper ---
def extract_json_from_text(text):
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        return match.group(0)
    return None

# --- Setup Directories ---
EXTRACTED_DIR = "data/extracted_data/"
UPLOADED_DIR = "data/uploaded/"
os.makedirs(UPLOADED_DIR, exist_ok=True)

# --- Streamlit Config ---
st.set_page_config(page_title="🧠 Due Diligence Assistant", page_icon="🤖", layout="wide")

# --- Sidebar Styling (Must be in every page) ---
sidebar_style = """
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #203a43 0%, #2c5364 100%);
    color: white;
    padding: 2rem 1rem;
}
[data-testid="stSidebarNav"] ul {
    list-style-type: none;
    padding: 0;
}
[data-testid="stSidebarNav"] ul li {
    margin-bottom: 15px;
}
[data-testid="stSidebarNav"] ul li a {
    display: block;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    text-decoration: none;
    font-weight: bold;
    color: white;
    transition: background 0.3s, color 0.3s;
}
[data-testid="stSidebarNav"] ul li a:hover {
    background-color: rgba(255, 255, 255, 0.2);
    color: #00FFFF;
}
</style>
"""
st.markdown(sidebar_style, unsafe_allow_html=True)

# --- Page Background Styling ---
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}
[data-testid="stHeader"] { background: rgba(0, 0, 0, 0); }
.big-font { font-size: 50px !important; font-weight: bold; color: #FFFFFF; text-shadow: 2px 2px 5px rgba(0,0,0,0.7); }
.medium-font { font-size: 24px !important; color: #D3D3D3; }
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- Page Title ---
st.markdown('<p class="big-font">📤 Upload Documents and 🧠 Ask Questions</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Upload PDFs, Preprocess Automatically, and Ask Smart Questions on Your Knowledge Base.</p>', unsafe_allow_html=True)
st.markdown("---")

# --- Upload Section ---
uploaded_files = st.file_uploader(
    "📎 Upload your documents (PDF, TXT, CSV, XLSX, Images)",
    type=["pdf", "txt", "csv", "xlsx", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"📂 {len(uploaded_files)} file(s) uploaded. Ready to process.")

    if st.button("🚀 Start Processing"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # --- Full Cleanup ---
        for file_path in glob.glob('data/new_chunks/*.txt'):
            os.remove(file_path)
        for path in ["data/embeddings/embeddings.npy", "data/embeddings/ids.txt", "data/faiss_index.index", "data/graph.pkl"]:
            if os.path.exists(path):
                os.remove(path)
        for folder in ["data/chunks/", "data/new_chunks/"]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.makedirs(folder)

        import scripts.graph_rag_retriever as retriever
        retriever.index = None
        retriever.id_list = None
        retriever.G = None

        st.info("🧹 Cleaned old data. Starting fresh!")

        # --- Process Uploaded Files ---
        status_text.text("🔄 Extracting and Cleaning Text...")
        for uploaded_file in uploaded_files:
            save_path = os.path.join(UPLOADED_DIR, uploaded_file.name)
            filename_clean = os.path.splitext(uploaded_file.name)[0].replace(" ", "").replace("-", "")
            st.session_state["latest_uploaded_filename"] = filename_clean

            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            process_uploaded_file(uploaded_file)
        progress_bar.progress(25)
        st.success("✅ Extraction and Cleaning Done!")

        status_text.text("🔪 Chunking into Semantic Chunks...")
        chunking_main()
        progress_bar.progress(50)
        st.success("✅ Chunking Done!")

        status_text.text("🔮 Embedding Chunks...")
        embedding_main()
        progress_bar.progress(75)
        st.success("✅ Embedding Done!")

        status_text.text("🕸️ Building Knowledge Graph...")
        graph_build_main()
        progress_bar.progress(100)
        st.success("✅ Knowledge Graph Built!")
        status_text.text("🎯 All files processed! You can now ask questions.")
        st.balloons()

st.markdown("---")

# --- Manual Question and Answer Section ---
st.markdown('<p class="big-font">🧠 Ask Questions</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">The AI will search your uploaded documents and answer intelligently.</p>', unsafe_allow_html=True)

question = st.text_input("💬 Type your question here", placeholder="e.g., What are the main investment risks?")

if question:
    with st.spinner("🔍 Classifying the question..."):
        question_type = classify_question(question)
    st.markdown(f"🔎 **Detected Question Type:** {question_type}")

    if question_type == "Missing Context":
        st.warning("⚠️ This question cannot be answered properly with the current documents.")
    else:
        with st.spinner("🔍 Searching for relevant information..."):
            context = retrieve_context(question, source_filter=st.session_state.get("latest_uploaded_filename"))

        if not context or context.startswith("❌"):
            st.error("⚠️ No relevant information found.")
        else:
            with st.expander("📚 Retrieved Context (click to expand)", expanded=False):
                st.write(context)

            with st.spinner("🧠 Generating professional answer..."):
                final_answer = ask_llm(question, context)

            st.success("✅ Final Answer Ready!")
            st.markdown("### 💬 Answer:")
            st.write(final_answer)

            with st.spinner("🛡️ Checking Faithfulness..."):
                faithfulness = check_faithfulness(question, context, final_answer)
            st.markdown("### 🛡️ Faithfulness Check:")
            st.info(faithfulness)

            with st.spinner("📝 Evaluating Answer Quality..."):
                evaluation_raw = evaluate_answer(question, context, final_answer)
                try:
                    evaluation_json = extract_json_from_text(evaluation_raw)
                    evaluation = json.loads(evaluation_json)
                except Exception as e:
                    st.error(f"❌ Failed to parse Evaluation JSON: {e}")
                    evaluation = {}

            st.markdown("### 📊 Answer Quality Evaluation:")
            st.json(evaluation)

            gap_analysis = None
            with st.spinner("🚨 Detecting Missing Information..."):
                gap_raw = detect_and_structure_gaps(question, context, final_answer, evaluation.get("Missing_Points", []))
                try:
                    gap_json = extract_json_from_text(gap_raw)
                    gap_analysis = json.loads(gap_json)
                except Exception as e:
                    st.error(f"❌ Failed to parse Gap Analysis JSON: {e}")

            if gap_analysis:
                st.markdown("### 🛠️ Gap Analysis for Data Acquisition:")
                st.json(gap_analysis)

                if st.button("🚀 Fill Missing Gaps"):
                    with st.spinner("🔎 Scraping external data and improving answer..."):
                        external_texts = []
                        for gap in gap_analysis:
                            query = gap.get("Suggested_Search_Query", "")
                            if query:
                                scraped = intelligent_scrape(query, mode="serper", num_results=2)
                                external_texts.extend(scraped)

                        external_data = "\n\n".join(external_texts)

                        big_prompt = f"""
You are a Due Diligence Expert.

Original Context:
{context}

Scraped External Data:
{external_data}

Previous Answer:
{final_answer}

Faithfulness Check:
{faithfulness}

Gap Analysis:
{json.dumps(gap_analysis, indent=2)}

Your task:
- Improve the previous answer using the new external data.
- Address all missing points.
- Stay faithful to context and external data.
- Write professionally and clearly.

New Improved Final Answer:
"""
                        final_improved_answer = ask_llm_raw(big_prompt)

                        st.success("✅ Final Improved Answer:")
                        st.markdown(final_improved_answer)
            else:
                st.warning("⚠️ No missing information detected.")

st.markdown("---")

# --- Footer ---
st.markdown('<center><p style="font-size:16px;">Powered by AI | Crypto Fund Due Diligence System © 2025</p></center>', unsafe_allow_html=True)
