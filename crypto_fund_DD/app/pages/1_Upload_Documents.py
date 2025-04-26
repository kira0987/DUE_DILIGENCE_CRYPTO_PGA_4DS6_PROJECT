import os
import glob
import shutil
import re
import json
import streamlit as st
import base64
from scripts.visualize_graph import visualize_graph
import sys, os
sys.path.append(os.path.abspath("scripts"))
from generate_pptx import main as generate_pptx_main
from scripts.extraction_and_cleaning import process_uploaded_file
from scripts.semantic_chunker import main as chunking_main
from scripts.embed_chunks import main as embedding_main
from scripts.build_graph import main as graph_build_main
from scripts.graph_rag_retriever import retrieve_context
from scripts.llm_responder import ask_llm, evaluate_answer, check_faithfulness, classify_question, detect_and_structure_gaps, ask_llm_raw
from scripts.intelligent_scraper import intelligent_scrape

# --- Init session state ---
if "show_graph" not in st.session_state:
    st.session_state["show_graph"] = False

# --- JSON Extractor Helper ---
def extract_json_from_text(text):
    if isinstance(text, dict):
        return json.dumps(text)  # already a dict, return safely as string
    elif isinstance(text, str):
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return match.group(0)
    return None


# --- Helper to Encode Image ---
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- Setup Directories ---
EXTRACTED_DIR = "data/extracted_data/"
UPLOADED_DIR = "data/uploaded/"
os.makedirs(UPLOADED_DIR, exist_ok=True)

# --- Streamlit Config ---
st.set_page_config(page_title="🧠 Due Diligence Assistant", page_icon="🤖", layout="wide")

# --- Sidebar and Background Styling ---
custom_style = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #141E30, #243B55);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] { 
    background: rgba(0, 0, 0, 0); 
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141E30 0%, #243B55 100%);
    color: white;
    padding: 1rem;
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
    padding: 0.7rem 1rem;
    border-radius: 10px;
    font-weight: bold;
    color: white;
    text-decoration: none;
    transition: all 0.3s ease;
}
[data-testid="stSidebarNav"] ul li a:hover {
    background-color: rgba(255, 255, 255, 0.15);
    color: #00FFFF;
}
.sidebar-title {
    font-size: 26px;
    font-weight: bold;
    color: #00FFFF;
    text-align: center;
    text-decoration: underline;
    margin-top: 10px;
}
.big-font { 
    font-size: 50px !important; 
    font-weight: bold; 
    color: #FFFFFF; 
    text-shadow: 2px 2px 5px rgba(0,0,0,0.7); 
}
.medium-font { 
    font-size: 24px !important; 
    color: #D3D3D3; 
}
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# --- Sidebar Logo + Title ---
with st.sidebar:
    img_base64 = get_image_base64("assets/logo (1).png")
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem;'>
            <img src="data:image/png;base64,{img_base64}" style="width:100px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0,0,0,0.2);">
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">DUEXPERT</div>', unsafe_allow_html=True)

# --- Page Title ---
st.markdown('<p class="big-font">📤 Upload Documents and 🧠 Ask Questions</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Upload PDFs, Preprocess Automatically, and Ask Smart Questions on Your Knowledge Base.</p>', unsafe_allow_html=True)
st.markdown("---")

# --- Upload Section ---
uploaded_files = st.file_uploader(
    "📎 Upload multiple files",
    type=["pdf", "txt", "csv", "xlsx", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="file_uploader_key"
)

if uploaded_files:
    st.info(f"📂 {len(uploaded_files)} file(s) uploaded. Ready to process.")
    if st.button("🚀 Start Processing", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

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

        st.info("🧹 Full cleanup done. Only new documents will be processed!")

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
        st.success("✅ Graph Built Successfully!")
        status_text.text("🎯 All files processed! You can now ask questions.")
        st.balloons()
        with st.spinner("🧠 Answering all due diligence questions..."):
            from scripts.answer_questions import generate_all_answers
            generate_all_answers()
        st.success("✅ All questions answered and saved.")      
        status_text.text("🎯 All files processed! You can now generate the PPTX report.")

st.markdown("---")

# --- Graph Section ---
st.markdown("### 🌐 GraphRAG Visualization")
if st.button("📊 Show Graph Visualization"):
    st.session_state["show_graph"] = True
if st.session_state.get("show_graph", False):
    visualize_graph()

# --- Manual Q&A ---
st.markdown('<p class="big-font">🧠 Ask Questions</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">The AI will search your uploaded documents and answer intelligently.</p>', unsafe_allow_html=True)

question = st.text_input("Ask a question:", placeholder="e.g., What are the main investment risks?")

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

            st.success("✅ Answer Generated")
            st.markdown("### 💬 Final Answer:")
            st.write(final_answer)

            with st.spinner("🛡️ Checking faithfulness..."):
                faithfulness = check_faithfulness(question, context, final_answer)
            st.markdown("### 🛡️ Faithfulness Check:")
            st.info(faithfulness)

            with st.spinner("📝 Evaluating answer quality..."):
                evaluation_raw = evaluate_answer(question, context, final_answer)
                try:
                    evaluation_json = extract_json_from_text(evaluation_raw)
                    evaluation = json.loads(evaluation_json) if isinstance(evaluation_json, str) else {}
                except Exception as e:
                    st.error(f"❌ Failed to parse Evaluation JSON: {e}")
                    evaluation = {}

            st.markdown("### 📊 Answer Quality Evaluation:")
            st.json(evaluation)

            with st.spinner("🚨 Detecting Missing Information for Scraping..."):
                gap_analysis = detect_and_structure_gaps(
                    question,
                    context,
                    final_answer,
                    evaluation.get("Missing_Points", [])
                )

            st.markdown("### 🛠️ Gap Analysis for Data Acquisition:")
            st.json(gap_analysis)

            if gap_analysis and st.button("🚀 Fill Missing Gaps with External Data"):
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
            elif not gap_analysis:
                st.warning("⚠️ No gaps detected.")

st.markdown("---")

# --- Auto-Answer from Question Bank (Grouped by Tag) ---
st.markdown('<p class="big-font">🗂️ Auto-Answer from Question Bank (Grouped by Domain)</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Click any question below to generate a live answer based on your documents.</p>', unsafe_allow_html=True)

CLASSIFIED_PATH = "data/classified_questions.json"

if os.path.exists(CLASSIFIED_PATH):
    from collections import defaultdict
    with open(CLASSIFIED_PATH, "r", encoding="utf-8") as f:
        classified_questions = json.load(f)

    tag_groups = defaultdict(list)
    for q in classified_questions:
        tag_groups[q["tag"]].append(q)

    import random
    background_colors = ["#1a1a2e", "#16213e", "#0f3460", "#53354a", "#2a2a72", "#222831", "#1e3d59", "#123456"]

    for tag in sorted(tag_groups.keys()):
        with st.expander(f"🏷️ {tag}", expanded=False):
            for q in tag_groups[tag]:
                q_text = q.get("question", "")
                q_id = q.get("id", "")
                if st.button(f"❓ {q_text}", key=f"button_tagged_{q_id}"):
                    with st.spinner("🔍 Classifying the question..."):
                        question_type = classify_question(q_text)
                    st.markdown(f"**🔎 Detected Question Type:** `{question_type}`")

                    if question_type == "Missing Context":
                        st.warning("⚠️ Cannot answer properly with the current documents.")
                    else:
                        with st.spinner("🔍 Retrieving and generating answer..."):
                            context = retrieve_context(q_text, source_filter=st.session_state.get("latest_uploaded_filename"))

                        if context and not context.startswith("❌"):
                            answer = ask_llm(q_text, context)

                            st.chat_message("user").markdown(f"**Q: {q_text}**")
                            st.chat_message("assistant").markdown(f"**A: {answer}**")

                            with st.spinner("🛡️ Checking faithfulness..."):
                                faithfulness = check_faithfulness(q_text, context, answer)
                            st.markdown("### 🛡️ Faithfulness Check:")
                            st.info(faithfulness)

                            with st.spinner("📝 Evaluating answer quality..."):
                                evaluation = evaluate_answer(q_text, context, answer)
                            st.markdown("### 📊 Answer Quality Evaluation:")
                            st.json(evaluation)

                            with st.spinner("🚨 Detecting Missing Information for Scraping..."):
                                gap_analysis = detect_and_structure_gaps(
                                    q_text,
                                    context,
                                    answer,
                                    evaluation.get("Missing_Points", [])
                                )
                            st.markdown("### 🛠️ Gap Analysis for Data Acquisition:")
                            st.json(gap_analysis)
                        else:
                            st.warning("⚠️ No relevant information found.")

else:
    st.warning("⚠️ Please run classification first to generate 'classified_questions.json'.")

# --- Generate PPTX Report Section ---
# --- Generate PPTX Report Section ---
st.markdown("### 📊 Generate Final Due Diligence Report")

if st.button("📥 Generate Executive PPTX Report"):
    with st.spinner("🧠 Compiling report slides..."):
        try:
            import sys, os
            sys.path.append(os.path.abspath("scripts"))
            from generate_pptx import main as generate_pptx_main

            generate_pptx_main()
            st.success("✅ Report generated successfully!")
            st.markdown("[📥 Download PPTX](output/due_diligence_report.pptx)", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Failed to generate report: {e}")

st.markdown("---")
st.markdown('<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>', unsafe_allow_html=True)