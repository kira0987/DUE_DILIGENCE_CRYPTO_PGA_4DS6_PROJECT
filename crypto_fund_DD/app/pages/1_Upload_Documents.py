import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import glob
import shutil
import re
import json
import streamlit as st
import base64
import sys
from lib.mongo_helpers import db
from lib.mongo_helpers import append_qa_result
from lib.mongo_helpers import load_question_bank
from scripts.visualize_graph import visualize_graph
from scripts.generate_pptx import main as generate_pptx_main
from scripts.extraction_and_cleaning import process_uploaded_file
from scripts.semantic_chunker import main as chunking_main
from scripts.embed_chunks import main as embedding_main
from scripts.build_graph import main as graph_build_main
from scripts.graph_rag_retriever import retrieve_context
from scripts.llm_responder import ask_llm, detect_and_structure_gaps, ask_llm_raw,apply_feedback_to_answer,platform_assistant_safe_answer, followup_assistant,detect_commitments,detect_commitments_in_text,evaluate_answer,check_faithfulness
from scripts.evaluate_investor_risk import evaluate_investor_risk
from scripts.risk_scorer import score_investment
from lib.mongo_helpers import insert_fund_metadata
from collections import defaultdict
from lib.mongo_helpers import store_risk_scores

sys.path.append(os.path.abspath("scripts"))

# --- Init session state ---
if "validated_commitments_done" not in st.session_state:
    st.session_state["validated_commitments_done"] = False

if "show_graph" not in st.session_state:
    st.session_state["show_graph"] = False
for key in ["show_graph", "feedback_responses"]:
    if key not in st.session_state:
        st.session_state[key] = {}
if "feedback_responses" not in st.session_state:
    st.session_state["feedback_responses"] = {}
if "active_file" not in st.session_state:
    st.session_state["active_file"] = None



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
            fund_name = os.path.splitext(uploaded_file.name)[0]           
            st.session_state["latest_uploaded_filename"] = fund_name
            os.environ["LATEST_UPLOADED_FUND"] = fund_name

            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                # 🔽 INSERT THIS BLOCK HERE (around line 152)
                existing = db["funds"].find_one({"fund_name": fund_name})
                if existing:
                    st.warning(f"⚠️ Fund '{fund_name}' already exists in MongoDB. Skipping reprocessing.")
                    inserted_id = existing["_id"]
                else:
                    inserted_id = insert_fund_metadata(fund_name, uploaded_file.name)
                    st.success(f"✅ New fund inserted with ID: {inserted_id}")
                    process_uploaded_file(uploaded_file)

            
        progress_bar.progress(25)
        st.success("✅ Extraction and Cleaning Done!")
        status_text.text("🔎 Detecting Fund Commitments and Promises...")

        try:
            

            latest_uploaded_prefix = st.session_state.get("latest_uploaded_filename", "")
            matching_cleaned_files = glob.glob(os.path.join(EXTRACTED_DIR, f"{latest_uploaded_prefix}_*_cleaned.txt"))

            if matching_cleaned_files:
                latest_cleaned_file = max(matching_cleaned_files, key=os.path.getmtime)
                with open(latest_cleaned_file, "r", encoding="utf-8") as f:
                    text = f.read()

                detected_commitments = detect_commitments_in_text(text, source_file=os.path.basename(latest_cleaned_file))

                if detected_commitments:
                    os.makedirs("data", exist_ok=True)
                    with open("data/commitments.json", "w", encoding="utf-8") as f:
                        json.dump(detected_commitments, f, indent=2, ensure_ascii=False)
                    st.success(f"✅ Detected {len(detected_commitments)} fund commitments!")
                else:
                    st.info("✅ No commitments or promises detected in this uploaded document.")
            else:
                st.warning("⚠️ No cleaned extracted document found for commitment detection.")
        except Exception as e:
            st.error(f"❌ Failed to detect commitments: {e}")
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
# --- Validate Commitments Section ---
st.markdown("---")
st.markdown('<p class="big-font">🕵️ Validate Fund Commitments</p>', unsafe_allow_html=True)

if os.path.exists("data/commitments.json"):
    if st.button("🕵️ Validate Fund Promises and Claims"):
        from scripts.validate_commitments import validate_all_commitments

        with st.spinner("🔍 Validating fund commitments against public sources... Please wait."):
            validate_all_commitments()

        st.success("✅ Validation complete! Results saved to data/commitments_validated.json.")

else:
    st.info("ℹ️ No commitments detected yet. Upload and process a document first.")
if st.button("🕵️ Validate Deeply (Step 2)"):
    from scripts.validate_commitments_step2 import validate_step2
    validate_step2()
    st.success("✅ Deep validation completed! Check commitments_validated_step2.json.")

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
            evaluation = evaluate_answer(q_text, context, answer)
            tag = cq.get("tag", "Uncategorized")
            fund_name = st.session_state.get("latest_uploaded_filename")
            append_qa_result(fund_name, q_text, answer)
            st.session_state[f"answer_{q_id}"] = answer
            st.session_state[f"context_{q_id}"] = context

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
    # 4.5. Store in MongoDB
    fund_name = st.session_state.get("latest_uploaded_filename")
    store_risk_scores(fund_name, risk_scores)

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

# --- Manual Q&A (Platform Assistant Only) ---
st.markdown('<p class="big-font">💬 Platform Assistant Chatbot</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Ask anything about the DueXpert platform, our features, and services!</p>', unsafe_allow_html=True)

question = st.text_input("Ask about the DueXpert platform:", placeholder="e.g., What services does DueXpert offer?")

if question:
    with st.spinner("💬 Generating platform response..."):
        final_answer = platform_assistant_safe_answer(question)

    st.success("✅ Answer Generated")
    st.markdown("### 💬 Platform Chatbot Answer:")

    if "❓ Sorry" in final_answer:
        st.warning(final_answer)
    else:
        st.info(final_answer)

            
st.markdown("---")

# --- Auto-Answer from Question Bank (Grouped by Domain) ---
st.markdown('<p class="big-font">📂 Auto-Answer from Question Bank (Grouped by Domain)</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Click any question below to generate a live answer based on your documents.</p>', unsafe_allow_html=True)

classified_questions = load_question_bank()

tag_groups = defaultdict(list)
for q in classified_questions:
    tag = q.get("tag", "Uncategorized")  # fallback if "tag" is missing
    tag_groups[tag].append(q)
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
                    fund_name = st.session_state.get("latest_uploaded_filename")
                    evaluation = evaluate_answer(q_text, context, answer)
                    tag = q.get("tag", "Uncategorized")
                    append_qa_result(fund_name, q_text, answer)

                  
                    st.session_state[f"answer_{q_id}"] = answer
                    st.session_state[f"context_{q_id}"] = context

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

            if f"answer_{q_id}" in st.session_state:
                answer = st.session_state[f"answer_{q_id}"]
                st.chat_message("user").markdown(f"**Q: {q_text}**")
                st.chat_message("assistant").markdown(f"**A: {answer}**")

                faithfulness_result = check_faithfulness(st.session_state.get(f"context_{q_id}", ""), answer)
                if faithfulness_result['status'] == "Faithful":
                    st.success(f"🔎 Faithfulness Check: ✅ Faithful\n\n{faithfulness_result['explanation']}")
                else:
                    st.error(f"🔎 Faithfulness Check: ❌ Not Faithful\n\n{faithfulness_result['explanation']}")

                with st.spinner("🛡️ Evaluating investor risk impact..."):
                    try:
                        risk_level = evaluate_investor_risk(answer)
                        risk_icon = {
                            "Positive": "✅",
                            "Partial": "🟡",
                            "Negative": "❌",
                            "Missing": "⚠️"
                        }.get(risk_level, "❔")

                        st.markdown(f"### 🛡️ Investor Risk Classification: {risk_icon} **{risk_level}**")
                    except Exception as e:
                        st.error(f"❌ Investor risk evaluation failed: {e}")

                context_for_eval = st.session_state.get(f"context_{q_id}", "")
                with st.spinner("📝 Evaluating answer quality..."):
                    evaluation = evaluate_answer(q_text, context_for_eval, answer)
                    st.markdown("### 📊 Answer Quality Evaluation:")

                    import plotly.graph_objects as go

                    labels = ["Completeness", "Accuracy", "Clarity"]
                    scores = [
                        evaluation.get("Completeness", 0),
                        evaluation.get("Accuracy", 0),
                        evaluation.get("Clarity", 0)
                    ]

                    colors = [
                        "#ffc107" if s < 8 else "#28a745" for s in scores
                    ]

                    fig = go.Figure(go.Bar(
                        x=labels,
                        y=scores,
                        marker_color=colors,
                        text=[f"{s}/10" for s in scores],
                        textposition="outside"
                    ))

                    fig.update_layout(
                        height=250,
                        width=500,
                        margin=dict(t=30, b=20, l=30, r=30),
                        title=dict(text="Answer Quality Metrics", x=0.5, font=dict(size=18)),
                        yaxis=dict(title="Score (0–10)", range=[0, 10], showgrid=True),
                        xaxis=dict(title=None),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white")
                    )

                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{q_id}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("✏️ Reformulate", key=f"reformulate_btn_{q_id}"):
                        with st.spinner("🔧 Reformulating..."):
                            try:
                                refined_answer = apply_feedback_to_answer("Reformulate this", q_text, answer)
                                st.session_state[f"refined_answer_{q_id}"] = refined_answer
                            except Exception as e:
                                st.error(f"❌ Failed to reformulate: {e}")

                with col2:
                    if st.button("🧼 Make Concise", key=f"concise_btn_{q_id}"):
                        with st.spinner("🔧 Making concise..."):
                            try:
                                refined_answer = apply_feedback_to_answer("Make it more concise", q_text, answer)
                                st.session_state[f"refined_answer_{q_id}"] = refined_answer
                            except Exception as e:
                                st.error(f"❌ Failed to make concise: {e}")

                with col3:
                    if st.button("📜 Add Regulation", key=f"regulate_btn_{q_id}"):
                        with st.spinner("🔧 Adding regulatory context..."):
                            try:
                                refined_answer = apply_feedback_to_answer("Add regulatory context", q_text, answer)
                                st.session_state[f"refined_answer_{q_id}"] = refined_answer
                            except Exception as e:
                                st.error(f"❌ Failed to add regulation: {e}")

                if f"refined_answer_{q_id}" in st.session_state:
                    st.markdown("### ✨ Refined Answer:")
                    st.success(st.session_state[f"refined_answer_{q_id}"])

                st.markdown("### 💬 Ask a Follow-up Related to This Question/Answer:")
                followup_input = st.text_input(
                    f"Type your follow-up question about '{q_text}'",
                    key=f"followup_input_{q_id}",
                    placeholder="e.g., Can you explain the compliance part more clearly?"
                )

                if followup_input:
                    with st.spinner("💬 Thinking about your follow-up..."):
                        followup_response = followup_assistant(q_text, answer, followup_input)
                    st.success("✅ Follow-up Answer:")
                    st.info(followup_response)


                    

# --- Generate PPTX Report Section ---
st.markdown("### 📊 Generate Final Due Diligence Report")

if st.button("📅 Generate Executive PPTX Report"):
    with st.spinner("🧐 Compiling report slides..."):
        try:
            fund_name = st.session_state.get("latest_uploaded_filename")
            generate_pptx_main()

            st.success("✅ Report generated successfully!")

            with open("output/due_diligence_report.pptx", "rb") as pptx_file:
                st.download_button(
                    label="📥 Download PPTX Report",
                    data=pptx_file,
                    file_name="due_diligence_report.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )

        except Exception as e:
            st.error(f"❌ Failed to generate report: {e}")

st.markdown("""
<!-- Feedback Box (From Uiverse by catraco) -->
<div class="bg-slate-800 border border-slate-700 grid grid-cols-6 gap-2 rounded-xl p-2 text-sm" style="margin-top: 60px;">
    <h1 class="text-center text-slate-600 text-xl font-bold col-span-6">Send Feedback</h1>
    <textarea class="bg-slate-700 text-slate-300 h-28 placeholder:text-slate-300 placeholder:opacity-50 border border-slate-600 col-span-6 resize-none outline-none rounded-lg p-2 duration-300 focus:border-slate-300" placeholder="Your feedback..."></textarea>
    <button class="fill-slate-300 col-span-1 flex justify-center items-center rounded-lg p-2 duration-300 bg-slate-700 hover:border-slate-300 focus:fill-blue-200 focus:bg-blue-600 border border-slate-600">
        <svg viewBox="0 0 512 512" height="20px" xmlns="http://www.w3.org/2000/svg">
            <path d="M464 256A208 208 0 1 0 48 256a208 208 0 1 0 416 0zM0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zm177.6 62.1C192.8 334.5 218.8 352 256 352s63.2-17.5 78.4-33.9c9-9.7 24.2-10.4 33.9-1.4s10.4 24.2 1.4 33.9c-22 23.8-60 49.4-113.6 49.4s-91.7-25.5-113.6-49.4c-9-9.7-8.4-24.9 1.4-33.9s24.9-8.4 33.9 1.4zM144.4 208a32 32 0 1 1 64 0 32 32 0 1 1 -64 0zm192-32a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"></path>
        </svg>
    </button>
    <button class="fill-slate-300 col-span-1 flex justify-center items-center rounded-lg p-2 duration-300 bg-slate-700 hover:border-slate-300 focus:fill-blue-200 focus:bg-blue-600 border border-slate-600">
        <svg viewBox="0 0 512 512" height="20px" xmlns="http://www.w3.org/2000/svg">
            <path d="M464 256A208 208 0 1 0 48 256a208 208 0 1 0 416 0zM0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zM174.6 384.1c-4.5 12.5-18.2 18.9-30.7 14.4s-18.9-18.2-14.4-30.7C146.9 319.4 198.9 288 256 288s109.1 31.4 126.6 79.9c4.5 12.5-2 26.2-14.4 30.7s-26.2-2-30.7-14.4C328.2 358.5 297.2 336 256 336s-72.2 22.5-81.4 48.1zM144.4 208a32 32 0 1 1 64 0 32 32 0 1 1 -64 0zm192-32a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"></path>
        </svg>
    </button>
    <span class="col-span-2"></span>
    <button class="col-span-2 stroke-slate-300 bg-slate-700 focus:stroke-blue-200 focus:bg-blue-600 border border-slate-600 hover:border-slate-300 rounded-lg p-2 duration-300 flex justify-center items-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="30px" height="30px" viewBox="0 0 24 24" fill="none">
            <path d="M7.39999 6.32003L15.89 3.49003C19.7 2.22003 21.77 4.30003 20.51 8.11003L17.68 16.6C15.78 22.31 12.66 22.31 10.76 16.6L9.91999 14.08L7.39999 13.24C1.68999 11.34 1.68999 8.23003 7.39999 6.32003Z" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
            <path d="M10.11 13.6501L13.69 10.0601" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
        </svg>
    </button>
</div>
""", unsafe_allow_html=True)


st.markdown("---")
st.markdown("""
<!-- Feedback Box (From Uiverse by catraco) -->
<div class="bg-slate-800 border border-slate-700 grid grid-cols-6 gap-2 rounded-xl p-2 text-sm" style="margin-top: 60px;">
    <h1 class="text-center text-slate-600 text-xl font-bold col-span-6">Send Feedback</h1>
    <textarea class="bg-slate-700 text-slate-300 h-28 placeholder:text-slate-300 placeholder:opacity-50 border border-slate-600 col-span-6 resize-none outline-none rounded-lg p-2 duration-300 focus:border-slate-300" placeholder="Your feedback..."></textarea>
    <button class="fill-slate-300 col-span-1 flex justify-center items-center rounded-lg p-2 duration-300 bg-slate-700 hover:border-slate-300 focus:fill-blue-200 focus:bg-blue-600 border border-slate-600">
        <svg viewBox="0 0 512 512" height="20px" xmlns="http://www.w3.org/2000/svg">
            <path d="M464 256A208 208 0 1 0 48 256a208 208 0 1 0 416 0zM0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zm177.6 62.1C192.8 334.5 218.8 352 256 352s63.2-17.5 78.4-33.9c9-9.7 24.2-10.4 33.9-1.4s10.4 24.2 1.4 33.9c-22 23.8-60 49.4-113.6 49.4s-91.7-25.5-113.6-49.4c-9-9.7-8.4-24.9 1.4-33.9s24.9-8.4 33.9 1.4zM144.4 208a32 32 0 1 1 64 0 32 32 0 1 1 -64 0zm192-32a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"></path>
        </svg>
    </button>
    <button class="fill-slate-300 col-span-1 flex justify-center items-center rounded-lg p-2 duration-300 bg-slate-700 hover:border-slate-300 focus:fill-blue-200 focus:bg-blue-600 border border-slate-600">
        <svg viewBox="0 0 512 512" height="20px" xmlns="http://www.w3.org/2000/svg">
            <path d="M464 256A208 208 0 1 0 48 256a208 208 0 1 0 416 0zM0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zM174.6 384.1c-4.5 12.5-18.2 18.9-30.7 14.4s-18.9-18.2-14.4-30.7C146.9 319.4 198.9 288 256 288s109.1 31.4 126.6 79.9c4.5 12.5-2 26.2-14.4 30.7s-26.2-2-30.7-14.4C328.2 358.5 297.2 336 256 336s-72.2 22.5-81.4 48.1zM144.4 208a32 32 0 1 1 64 0 32 32 0 1 1 -64 0zm192-32a32 32 0 1 1 0 64 32 32 0 1 1 0-64z"></path>
        </svg>
    </button>
    <span class="col-span-2"></span>
    <button class="col-span-2 stroke-slate-300 bg-slate-700 focus:stroke-blue-200 focus:bg-blue-600 border border-slate-600 hover:border-slate-300 rounded-lg p-2 duration-300 flex justify-center items-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="30px" height="30px" viewBox="0 0 24 24" fill="none">
            <path d="M7.39999 6.32003L15.89 3.49003C19.7 2.22003 21.77 4.30003 20.51 8.11003L17.68 16.6C15.78 22.31 12.66 22.31 10.76 16.6L9.91999 14.08L7.39999 13.24C1.68999 11.34 1.68999 8.23003 7.39999 6.32003Z" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
            <path d="M10.11 13.6501L13.69 10.0601" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
        </svg>
    </button>
</div>
""", unsafe_allow_html=True)


st.markdown('<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>', unsafe_allow_html=True)
