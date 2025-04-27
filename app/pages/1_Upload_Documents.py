import os
import glob
import shutil
import re
import json
import streamlit as st
import base64
import sys

from scripts.visualize_graph import visualize_graph
from scripts.generate_pptx import main as generate_pptx_main
from scripts.extraction_and_cleaning import process_uploaded_file
from scripts.semantic_chunker import main as chunking_main
from scripts.embed_chunks import main as embedding_main
from scripts.build_graph import main as graph_build_main
from scripts.graph_rag_retriever import retrieve_context
from scripts.llm_responder import ask_llm, detect_and_structure_gaps, ask_llm_raw,refine_answer
from scripts.evaluate_investor_risk import evaluate_investor_risk
from scripts.risk_scorer import score_investment

sys.path.append(os.path.abspath("scripts"))

# --- Init session state ---
if "show_graph" not in st.session_state:
    st.session_state["show_graph"] = False

# --- JSON Extractor Helper ---
def extract_json_from_text(text):
    if isinstance(text, dict):
        return json.dumps(text)
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
st.set_page_config(page_title="🧐 Due Diligence Assistant", page_icon="🤖", layout="wide")

# --- Styling ---
custom_style = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #141E30, #243B55);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] { background: rgba(0, 0, 0, 0); }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141E30 0%, #243B55 100%);
    color: white;
    padding: 1rem;
}
.sidebar-title {
    font-size: 26px;
    font-weight: bold;
    color: #00FFFF;
    text-align: center;
    text-decoration: underline;
    margin-top: 10px;
}
.big-font { font-size: 50px !important; font-weight: bold; color: #FFFFFF; }
.medium-font { font-size: 24px !important; color: #D3D3D3; }
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# --- Sidebar Logo + Title ---
with st.sidebar:
    img_base64 = get_image_base64("assets/logo (1).png")
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem;'>
            <img src="data:image/png;base64,{img_base64}" style="width:100px; border-radius: 12px;">
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">DUEXPERT</div>', unsafe_allow_html=True)

# --- Page Title ---
st.markdown('<p class="big-font">📄 Upload Documents and 🧐 Ask Questions</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Upload PDFs, Preprocess Automatically, and Ask Smart Questions on Your Knowledge Base.</p>', unsafe_allow_html=True)
st.markdown("---")

# --- Upload Section ---
uploaded_files = st.file_uploader(
    "📋 Upload multiple files",
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

        st.info("🧹 Cleanup done. Processing new documents only!")

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

        status_text.text("🔸 Building Knowledge Graph...")
        graph_build_main()
        progress_bar.progress(100)
        st.success("✅ Graph Built Successfully!")
        status_text.text("🌟 Done! You can now ask questions.")
        st.balloons()
st.markdown("---")
st.markdown('<p class="big-font">🛡️ Risk Scoring Engine</p>', unsafe_allow_html=True)

if st.button("🛡️ Run Risk Scoring Now"):
    st.info("🛠️ Calculating Risk Scoring... Please wait!")

    # 1. Load the critical questions
    with open(os.path.join("data", "critical_questions.json"), "r", encoding="utf-8") as f:
        critical_questions = json.load(f)


    # 2. Initialize answers dict
    answers_dict = {}

    for cq in critical_questions:
        q_id = cq['id']
        q_text = cq['question']

        # 3. For each critical question, retrieve context and answer
        context = retrieve_context(q_text, source_filter=st.session_state.get("latest_uploaded_filename"))

        if context and not context.startswith("❌"):
            answer = ask_llm(q_text, context)
            try:
                parsed = json.loads(answer)
                direct_answer = parsed.get("Direct Answer", answer)
            except Exception:
                direct_answer = answer
        else:
            direct_answer = "❌ No answer available."

        answers_dict[q_id] = direct_answer

    # 4. Run risk scoring
    risk_scores = score_investment(answers_dict)

    # 5. Display Results
    st.success("✅ Risk Scoring Done!")
    st.markdown("### 📈 Risk Scores per Category:")

    for category, score in risk_scores.items():
        if category != "TOTAL":
            st.markdown(f"**🏷️ {category}:** `{score}%`")

    st.markdown("### 🧮 Total Investment Risk Score:")
    st.markdown(f"<h2 style='color:#00FF00;'>🛡️ {risk_scores['TOTAL']}%</h2>", unsafe_allow_html=True)

st.markdown("---")

# --- Graph Section ---
st.markdown("### 🌐 GraphRAG Visualization")
if st.button("📊 Show Graph Visualization"):
    st.session_state["show_graph"] = True
if st.session_state.get("show_graph", False):
    visualize_graph()

# --- Manual Q&A ---
st.markdown('<p class="big-font">🧐 Ask Questions</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">The AI will search your uploaded documents and answer intelligently.</p>', unsafe_allow_html=True)

question = st.text_input("Ask a question:", placeholder="e.g., What are the main investment risks?")

if question:

    with st.spinner("🔍 Searching for relevant information..."):
        context = retrieve_context(question, source_filter=st.session_state.get("latest_uploaded_filename"))

    if not context or context.startswith("❌"):
        st.error("⚠️ No relevant information found.")
    else:
        with st.expander("📚 Retrieved Context (click to expand)", expanded=False):
            st.write(context)

        with st.spinner("🧐 Generating professional answer..."):
            final_answer = ask_llm(question, context)

        st.success("✅ Answer Generated")
        st.markdown("### 💬 Final Structured Answer:")

        try:
            answer_data = json.loads(final_answer)

            # Direct Answer
            if "Direct Answer" in answer_data:
                st.markdown(f"**📝 Direct Answer:** {answer_data['Direct Answer']}")

            # Extracted Facts
            if "Extracted Facts" in answer_data:
                st.markdown("**📌 Extracted Facts:**")
                facts = answer_data["Extracted Facts"]
                if isinstance(facts, list):
                    for fact in facts:
                        st.markdown(f"- {fact}")
                else:
                    st.write(facts)

            # Compliance Status
            if "Compliance Status" in answer_data:
                st.markdown(f"**⚖️ Compliance Status:** {answer_data['Compliance Status']}")

            # Missing Information Detected
            if "Missing Information Detected" in answer_data:
                missing_info = answer_data["Missing Information Detected"]
                if isinstance(missing_info, list) and missing_info:
                    st.markdown("**🚨 Missing Information Detected:**")
                    for item in missing_info:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("✅ No critical information missing.")

            # Conclusion
            if "Conclusion" in answer_data:
                st.markdown(f"**🧠 Conclusion:** {answer_data['Conclusion']}")

        except Exception as e:
            st.error(f"❌ Failed to parse structured answer: {e}")
            st.write(final_answer)
         

        with st.spinner("🚨 Detecting Gaps for Data Acquisition..."):
            gap_raw = detect_and_structure_gaps(question, context, final_answer)
            gap_json = extract_json_from_text(gap_raw)

            if gap_json:
                try:
                    parsed_gaps = json.loads(gap_json)
                    if isinstance(parsed_gaps, list) and parsed_gaps and "Status" not in parsed_gaps[0]:
                        os.makedirs("data", exist_ok=True)
                        with open("data/missing_gaps_to_scrape.json", "w", encoding="utf-8") as f:
                            json.dump(parsed_gaps, f, indent=2, ensure_ascii=False)
                        st.success("✅ Missing gaps detected and saved to backend.")
                    else:
                        st.info("✅ No missing gaps detected for this question.")
                except Exception as e:
                    st.error(f"❌ Failed to save or parse gaps: {e}")
            else:
                st.warning("⚠️ No gaps detected or invalid gap format.")
            

st.markdown("---")

# --- Auto-Answer from Question Bank (Grouped by Domain) ---
st.markdown('<p class="big-font">📂 Auto-Answer from Question Bank (Grouped by Domain)</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Click any question below to generate a live answer based on your documents.</p>', unsafe_allow_html=True)

CLASSIFIED_PATH = "data/classified_questions.json"

if os.path.exists(CLASSIFIED_PATH):
    from collections import defaultdict
    with open(CLASSIFIED_PATH, "r", encoding="utf-8") as f:
        classified_questions = json.load(f)

    tag_groups = defaultdict(list)
    for q in classified_questions:
        tag_groups[q["tag"]].append(q)

    for tag in sorted(tag_groups.keys()):
        with st.expander(f"🏷️ {tag}", expanded=False):
            for q in tag_groups[tag]:
                q_text = q.get("question", "")
                q_id = q.get("id", "")
                if st.button(f"❓ {q_text}", key=f"button_tagged_{q_id}"):
                    with st.spinner("🔍 Retrieving and generating answer..."):
                        context = retrieve_context(q_text, source_filter=st.session_state.get("latest_uploaded_filename"))

                    if context and not context.startswith("❌"):
                        answer = ask_llm(q_text, context)
                        st.session_state["last_answer"] = answer
                        st.session_state["last_context"] = context
                        st.session_state["last_question"] = q_text

                        # --- Risk Evaluation Block ---
                        try:
                            parsed_answer = json.loads(answer)
                            if isinstance(parsed_answer, dict) and "Direct Answer" in parsed_answer:
                                direct_answer_text = parsed_answer["Direct Answer"]
                            else:
                                direct_answer_text = answer
                        except Exception:
                            direct_answer_text = answer

                        direct_answer_text = direct_answer_text.strip()[:1200]

                        try:
                            risk_evaluation = evaluate_investor_risk(direct_answer_text).strip().capitalize()
                            risk_label = {
                                "Positive": "🟢 Positive",
                                "Negative": "🔴 Negative",
                                "Partial": "🟠 Partial",
                                "Missing": "⚪ Missing"
                            }.get(risk_evaluation, "⚪ Unknown")
                            st.markdown("### 🛡️ Investor Risk Impact Analysis")
                            st.success(f"✅ {risk_label}")
                        except Exception as e:
                            st.warning(f"⚠️ Risk Evaluation Failed: {e}")

                        # --- Display the Question and Answer ---
                        st.chat_message("user").markdown(f"**Q: {q_text}**")
                        st.chat_message("assistant").markdown(f"**A: {answer}**")

                        # --- Buttons for Improving the Answer ---
                        st.markdown("### 🛠️ Improve this Answer:")

                        col1, col2, col3 = st.columns(3)

                        if col1.button("✏️ Reformulate", key=f"reformulate_{q_id}"):
                            st.session_state["refinement_action"] = "reformulate"

                        if col2.button("✂️ Make Concise", key=f"concise_{q_id}"):
                            st.session_state["refinement_action"] = "concise"

                        if col3.button("🏛️ Add Regulatory Context", key=f"regulatory_{q_id}"):
                            st.session_state["refinement_action"] = "regulatory"

                        if "refinement_action" in st.session_state and st.session_state["refinement_action"]:
                            action_type = st.session_state["refinement_action"]
                            with st.spinner(f"🔧 Refining Answer: {action_type.capitalize()}..."):
                                refined = refine_answer(action_type, st.session_state["last_answer"], st.session_state["last_context"])

                            st.markdown(f"### 🔧 Refined Answer ({action_type.capitalize()}):")
                            st.write(refined)
                            st.session_state["refinement_action"] = None

                        with st.spinner("🚨 Detecting Gaps for Data Acquisition..."):
                            gap_raw = detect_and_structure_gaps(q_text, context, answer)
                            gap_json = extract_json_from_text(gap_raw)

                            if gap_json:
                                try:
                                    parsed_gaps = json.loads(gap_json)
                                    if isinstance(parsed_gaps, list) and parsed_gaps and "Status" not in parsed_gaps[0]:
                                        os.makedirs("data", exist_ok=True)
                                        with open("data/missing_gaps_to_scrape.json", "w", encoding="utf-8") as f:
                                            json.dump(parsed_gaps, f, indent=2, ensure_ascii=False)
                                        st.success("✅ Missing gaps saved to backend.")
                                    else:
                                        st.info("✅ No missing gaps detected for this question.")
                                except Exception as e:
                                    st.error(f"❌ Failed to save gaps: {e}")
                            else:
                                st.warning("⚠️ No gaps detected or invalid gap format.")

                    else:
                        st.warning("⚠️ No relevant information found.")


else:
    st.warning("⚠️ Please run classification first to generate 'classified_questions.json'.")

# --- Generate PPTX Report Section ---
st.markdown("### 📊 Generate Final Due Diligence Report")

if st.button("📅 Generate Executive PPTX Report"):
    with st.spinner("🧐 Compiling report slides..."):
        try:
            from generate_pptx import main as generate_pptx_main
            generate_pptx_main()
            st.success("✅ Report generated successfully!")
            st.markdown("[📥 Download PPTX](output/due_diligence_report.pptx)", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Failed to generate report: {e}")  

st.markdown("---")

st.markdown('<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>', unsafe_allow_html=True)
