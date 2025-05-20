import streamlit as st
import streamlit.components.v1 as components
import base64
import torch
import sys
import os
import glob
import shutil
import re
import json
from collections import defaultdict

# Add the missing import for MongoDB helpers
sys.path.append(os.path.abspath("lib"))
from lib.mongo_helpers import db, load_question_bank, insert_fund_metadata, append_qa_result

sys.path.append(os.path.abspath("scripts"))
from scripts.llm_responder import ask_llm, platform_assistant_safe_answer, check_faithfulness, evaluate_answer, apply_feedback_to_answer, followup_assistant
from scripts.graph_rag_retriever import retrieve_context
from scripts.extraction_and_cleaning import process_uploaded_file
from scripts.semantic_chunker import main as chunking_main
from scripts.embed_chunks import main as embedding_main
from scripts.build_graph import main as graph_build_main
from scripts.validate_commitments import validate_all_commitments
from scripts.validate_commitments_step2 import validate_step2
from scripts.generate_pptx import main as generate_pptx_main

_ = torch.classes  # Fix for PyTorch + Streamlit runtime issue

def highlight_matches(text, search_term):
    if not search_term.strip():
        return text
    try:
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        return pattern.sub(lambda match: f'<mark>{match.group(0)}</mark>', text)
    except:
        return text
# --- Streamlit Config ---
st.set_page_config(
    page_title="DueXpert - Due Diligence",
    page_icon="⚙️",
    layout="wide",
)


# Mirror real input to Streamlit session state
col1, col2, col3 = st.columns([3, 3, 2])
with col3:
    search_query = st.text_input(
        label="",
        placeholder="🔍 Search for a question or a category ..",
        key="search_query",
        label_visibility="collapsed"
    )


# --- Hide Streamlit Default Header/Footer and Sidebar ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- Load Background Image ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_image = get_base64_of_bin_file('images/Logo2.png')

# --- Inject Custom Styling: Sidebar and Main Content ---
page_bg_img = """
<!-- FontAwesome (Global Scope) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">

<style>
:root {
    --primary: #06a3da;
    --dark: #011f3f;
    --light: #f8f8f8;
}

/* Full width remove padding */
[data-testid="stAppViewContainer"] {
    background-color: #f8f8f8;
    padding: 20px;
    margin: 0px;
    margin-left: 300px; /* Indent content to make room for sidebar */
}
[data-testid="stAppViewContainer"] > div {
    padding: 0 !important;
    margin: 0 !important;
}
.css-1d391kg, .css-1v0mbdj {
    padding: 0rem;
    margin: 0rem;
}
.simple-search {
    top: 10px !important;
    right: 40px;
    width: 50px !important;
    z-index: 999;
}

input[type="text"] {
    width: 100% !important;
    height: 42px;
    font-size: 15px;
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid #ccc;
    box-shadow: none;
    transition: all 0.2s ease-in-out;
}

input[type="text"]:focus {
    outline: none;
    border: 1px solid #06a3da;
    box-shadow: 0 0 6px rgba(6, 163, 218, 0.4);
}

/* Sidebar */
.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 300px;
    height: 100vh;
    background: #ffffff;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    justify-content: space-between; /* Push top and bottom sections apart */
    padding: 20px 0;
    z-index: 9999;
}

.sidebar .top-section {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.sidebar .logo-section {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 40px;
}

.sidebar .logo-section img {
    width: 50px;
    height: 50px;
    object-fit: contain;
    border: none;
    margin-right: 10px;
}

.sidebar .logo-section span {
    font-size: 24px;
    font-weight: bold;
    color: #06a3da;
}

.sidebar .logo-section span .highlight {
    color: #00658a;
}

.sidebar .top-links, .sidebar .bottom-links {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.sidebar a {
    color: #333;
    text-decoration: none;
    font-size: 18px;
    font-weight: 500;
    padding: 15px 20px;
    display: flex;
    align-items: center;
    transition: 0.3s;
}

.sidebar a i {
    margin-right: 10px;
    font-size: 20px;
    color: #06a3da; /* Blue icons */
    transition: 0.3s;
}

.sidebar a:hover {
    background: #e6f0fa;
    color: #06a3da;
}

.sidebar a:hover i {
    color: #ffffff; /* White icons on hover */
}

.sidebar .bottom-links a {
    padding: 15px 20px; /* Consistent padding for bottom links */
}

.sidebar .pro-card {
    background: #06a3da;
    border-radius: 10px;
    padding: 15px;
    margin: 0 20px 20px; /* Margin to avoid sticking to edges and bottom */
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    color: #ffffff;
    margin-top: auto; /* Pushes the card to the bottom */
    position: relative;
    justify-content: center;
    gap: 10px;
}

.sidebar .pro-card img {
    width: 30px;
    height: 30px;
    margin-bottom: 10px;
}

.sidebar .pro-card h3 {
    font-size: 23px;
    margin: 5px 0;
    font-weight: 600;
}

.sidebar .pro-card p {
    font-size: 16px;
    margin: 5px 0;
    color: #e0f0ff;
    align-items: center;
}

.sidebar .pro-card .pro-button {
    background: #ffffff;
    color: #06a3da;
    border: none;
    padding: 8px 15px;
    border-radius: 5px;
    font-size: 14px;
    cursor: pointer;
    transition: 0.3s;
    margin-top: 10px;
    text-decoration: none;
    align-items: center;
}

.sidebar .pro-card .pro-button:hover {
    background: #e0f0ff;
}

.sidebar .bottom-icons {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 10px;
}

.sidebar .bottom-icons a {
    color: #333;
    text-decoration: none;
    font-size: 18px;
    padding: 10px 0;
    display: flex;
    align-items: center;
    width: 100%;
    justify-content: center;
}

.sidebar .bottom-icons a i {
    margin-right: 5px;
    font-size: 16px;
    color: #06a3da;
}

.sidebar .bottom-icons a:hover {
    background: #e6f0fa;
    color: #06a3da;
}

.sidebar .bottom-icons a:hover i {
    color: #ffffff;
}

/* Responsive Design */
@media (max-width: 768px) {
    .sidebar {
        width: 80px;
        align-items: center;
    }
    .sidebar .top-links, .sidebar .bottom-links {
        align-items: center;
    }
    .sidebar a {
        justify-content: center;
        font-size: 0; /* Hide text */
    }
    .sidebar a i {
        margin-right: 0;
        font-size: 24px;
    }
    .sidebar .logo-section span {
        display: none; /* Hide title */
    }
    .sidebar .logo-section img {
        margin-right: 0;
    }
    .sidebar .pro-card {
        margin: 0 10px 10px;
        padding: 10px;
    }
    .sidebar .pro-card img {
        width: 25px;
        height: 25px;
    }
    .sidebar .pro-card h3 {
        font-size: 14px;
        margin: 0 0 4px 0;
    }
    .sidebar .pro-card p {
        font-size: 12px;
    }
    .sidebar .pro-card .pro-button {
        padding: 6px 12px;
        font-size: 12px;
    }
    .sidebar .bottom-icons a {
        font-size: 0;
    }
    .sidebar .bottom-icons a i {
        font-size: 18px;
    }
    [data-testid="stAppViewContainer"] {
        margin-left: 80px; /* Adjust content margin for smaller sidebar */
    }
}

@media (max-width: 480px) {
    .sidebar {
        width: 60px;
    }
    .sidebar a i {
        font-size: 20px;
    }
    .sidebar .pro-card {
        margin: 0 5px 5px;
        padding: 8px;
    }
    .sidebar .pro-card img {
        width: 20px;
        height: 20px;
    }
    .sidebar .pro-card h3 {
        font-size: 12px;
    }
    .sidebar .pro-card p {
        font-size: 10px;
        margin: 0;
    }
    .sidebar .pro-card .pro-button {
        padding: 4px 10px;
        font-size: 10px;
    }
    .sidebar .bottom-icons a i {
        font-size: 16px;
    }
    [data-testid="stAppViewContainer"] {
        margin-left: 60px;
    }
}

/* Search Bar Styling */
.custom-search-container {
  position: fixed;
  top: 20px;
  right: 40px;
  z-index: 10000;
}

.group {
  display: flex;
  line-height: 28px;
  align-items: center;
  position: relative;
  max-width: 200px;
  background: #f3f3f4;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.input {
  width: 120%;
  height: 40px;
  line-height: 28px;
  padding: 0 1rem;
  padding-left: 2.5rem;
  border: none;
  border-radius: 8px;
  outline: none;
  background-color: transparent;
  color: #0d0c22;
}

.input::placeholder {
  color: #9e9ea7;
}

.input:focus,
.input:hover {
  outline: none;
  border: none;
  background-color: #fff;
  box-shadow: 0 0 0 3px rgba(6, 163, 218, 0.3);
}

.icon {
  position: absolute;
  left: 0.8rem;
  fill: #9e9ea7;
  width: 1rem;
  height: 1rem;
}
mark {
    background-color: #ffeb3b;
    color: #000;
    padding: 2px 4px;
    border-radius: 3px;
}

</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- Sidebar ---
st.markdown(f"""
<div class="sidebar">
    <div class="top-section">
        <div class="logo-section">
            <img src="data:image/png;base64,{logo_image}">
            <span>Due<span class="highlight">X</span>pert</span>
        </div>
        <div class="top-links">
            <a href="/home_page"><i class="fas fa-home"></i>Home</a>
            <a href="#"><i class="fas fa-search"></i>Due Diligence</a>
            <a href="#"><i class="fas fa-chart-line"></i>Risk Scoring</a>
            <a href="#"><i class="fas fa-file-alt"></i>Reports</a>
        </div>
    </div>
    <div class="bottom-section">
        <div class="pro-card">
            <img src="data:image/png;base64,{get_base64_of_bin_file('images/subscribe_16678160.gif')}">
            <h3><center>Go unlimited with <br>PRO</center></h3>
            <p>Unlock DueXpert’s full toolkit  insights, automation, and confident fund evaluations.!</p>
            <a href="#" class="pro-button">Get started with PRO</a>
        </div>
        <div class="bottom-icons">
            <a href="#"><i class="fas fa-gear"></i>Setting & Subscription</a>
            <a href="#"><i class="fas fa-sign-out-alt"></i>Logout</a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Setup Directories ---
EXTRACTED_DIR = "data/extracted_data/"
UPLOADED_DIR = "data/uploaded/"
os.makedirs(UPLOADED_DIR, exist_ok=True)

# --- Session State Initialization ---
if "active_file" not in st.session_state:
    st.session_state["active_file"] = None
if "latest_uploaded_filename" not in st.session_state:
    st.session_state["latest_uploaded_filename"] = None
if "selected_category" not in st.session_state:
    st.session_state["selected_category"] = None
if "active_question" not in st.session_state:
    st.session_state["active_question"] = None
if "validated_commitments_done" not in st.session_state:
    st.session_state["validated_commitments_done"] = False
if "pptx_generated" not in st.session_state:
    st.session_state["pptx_generated"] = False

# --- Upload Section Styling (Aligned with home_page.py) ---
st.markdown("""
<style>
:root {
    --primary: #06a3da;
    --dark: #011f3f;
    --light: #f8f8f8;
}

.upload-section {
    padding: 15px 15px 40px 15px !important;  /* top, right, bottom, left */
    background: var(--light) !important;
    text-align: center !important;
}

.section-title {
    margin-top: 0 !important;
    position: relative;
    padding-bottom: 10px;
    margin-bottom: 40px;
    text-align: center;
}
.section-title::before {
    content: "";
    position: absolute;
    width: 150px;
    height: 5px;
    background: var(--primary);
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 3px;
    animation: underlineWithDot 3s infinite ease-in-out;
}
.section-title::after {
    content: "";
    position: absolute;
    width: 10px;
    height: 10px;
    background: white;
    bottom: -2.5px;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 50%;
    animation: dotMove 3s infinite ease-in-out;
}
@keyframes underlineWithDot {
    0%, 100% { width: 0; }
    50% { width: 150px; }
}
@keyframes dotMove {
    0% { left: calc(50% - 75px); }
    50% { left: 50%; }
    100% { left: calc(50% + 75px); }
}
.section-title h5 {
    font-weight: 700;
    text-transform: uppercase;
    color: var(--primary);
    margin-bottom: 10px;
}
.section-title h1 {
    font-size: 36px;
    font-weight: 800;
    color: var(--dark);
    margin: 0;
}

.bn49 {
  border: 0;
  text-align: center;
  display: inline-block;
  padding: 14px;
  margin: 7px;
  color: #ffffff !important;  /* Force white color even if it's a link */
  width: 220px;       /* Make button longer horizontally */
  padding: 18px 20px; /* More vertical (top/bottom) space and horizontal padding */
  font-size: 18px;    /* Make text larger */
  background-color: #36a2eb;
  border-radius: 8px;
  font-family: "Segoe UI", sans-serif;
  font-weight: 600;
  text-decoration: none !important; /* Explicitly remove underline */
  transition: box-shadow 200ms ease-out;
}
.bn49:hover {
  box-shadow: 0 0 10px rgba(54, 162, 235, 0.7);
}

/* Hide the default Streamlit buttons for Reformulate, Make Concise, and Add Regulation */
button[data-key^="reformulate_"],
button[data-key^="concise_"],
button[data-key^="regulate_"] {
  display: none !important;
}

/* Custom Download Button Styling */
/* From Uiverse.io by Tsiangana */ 
.botao {
  width: 125px;
  height: 45px;
  border-radius: 20px;
  border: none;
  box-shadow: 1px 1px rgba(107, 221, 215, 0.37);
  padding: 5px 10px;
  background-color: rgb(59, 190, 230);
  color: #fff;
  font-family: Roboto, sans-serif;
  font-weight: 505;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  filter: drop-shadow(0 0 10px rgba(59, 190, 230, 0.568));
  transition: 0.5s linear;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.botao .mysvg {
  display: none;
}

.botao:hover {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  transition: 0.5s linear;
}

.botao:hover .texto {
  display: none;
}

.botao:hover .mysvg {
  display: inline;
}

.botao:hover::after {
  content: "";
  position: absolute;
  width: 16px;
  height: 3px;
  background-color: rgb(59, 190, 230);
  margin-left: -20px;
  animation: animate 0.9s linear infinite;
}

.botao:hover::before {
  content: "";
  position: absolute;
  top: -3px;
  left: -3px;
  width: 100%;
  height: 100%;
  border: 3.5px solid transparent;
  border-top: 3.5px solid #fff;
  border-right: 3.5px solid #fff;
  border-radius: 50%;
  animation: animateC 2s linear infinite;
}

@keyframes animateC {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes animate {
  0% {
    transform: translateY(0);
  }
  100% {
    transform: translateY(20px);
  }
}

/* Style for the anchor tag to remove default link styling */
.download-link {
  text-decoration: none;
  color: inherit;
}
</style>
""", unsafe_allow_html=True)

# --- Upload Section ---
st.markdown("""
<div class="upload-section">
    <div class="section-title">
        <h1>Start Your Due Diligence Process</h1>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "📋 Upload multiple files",
    type=["pdf"],
    accept_multiple_files=True,
    key="file_uploader_key"
)

if uploaded_files:
    st.info(f"📂 {len(uploaded_files)} file(s) uploaded. Ready to process.")
    if st.button("🚀 Start Processing", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Clean up previous data
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

# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

# --- Categories Section Styling (Enhanced with Icons) ---
st.markdown("""
<style>
.category-section {
    padding: 50px 15px !important;
    background: var(--light) !important;
    text-align: center !important;
}

.category-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 20px rgba(52, 112, 252, 0.4);
    transition: transform 0.3s ease;
    width: 280px !important;
    min-height: 200px !important;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    justify-content: center;
    cursor: pointer;
}

.category-card:hover {
    transform: scale(1.05);
}

.category-icon {
    font-size: 36px;
    color: var(--primary);
    margin-bottom: 15px;
}

.category-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--dark);
    margin: 0;
}

.category-form {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
}

.category-button {
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.qa-section {
    padding: 20px;
    background: var(--light);
}

.chat-message-user {
    background: #e6f0fa;
    border-radius: 15px;
    padding: 10px 15px;
    margin: 10px 0;
    max-width: 80%;
    margin-left: auto;
    color: var(--dark);
}

.chat-message-assistant {
    background: #ffffff;
    border-radius: 15px;
    padding: 10px 15px;
    margin: 10px 0;
    max-width: 80%;
    margin-right: auto;
    color: var(--dark);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
    .category-card {
        width: 100% !important;
        max-width: 300px !important;
        margin: 0 auto 20px auto;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Categories Section ---
st.markdown("""
<div class="category-section">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">Do you need insights? </h5>
        <h1>Explore Due Diligence Categories</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# Define category icons mapping
category_icons = {
    "Legal & Regulatory": "fas fa-gavel",
    "Tokenomics & Trading Integrity": "fas fa-coins",
    "AML / KYC": "fas fa-user-check",
    "IP & Contracts": "fas fa-file-contract",
    "Financial Health": "fas fa-chart-bar",
    "Custody & Asset Security": "fas fa-lock",
    "Governance": "fas fa-users",
    "Risk Management": "fas fa-exclamation-triangle",
    "Cybersecurity & Data Privacy": "fas fa-shield-alt",
    "Community & UX": "fas fa-users-cog",
    "Strategy & Competitive Positioning": "fas fa-chess",
    "Technology & Infrastructure": "fas fa-server",
    "ESG & Sustainability": "fas fa-leaf",
}

# Load and group questions by category
classified_questions = load_question_bank()
tag_groups = defaultdict(list)
for q in classified_questions:
    tag = q.get("tag", "Uncategorized")
    tag_groups[tag].append(q)

# Display category cards
if not st.session_state.get("selected_category"):
    cols = st.columns(4)
    for idx, tag in enumerate(sorted(tag_groups.keys())):
        # Check if tag or any question inside matches the search
        questions_in_tag = tag_groups[tag]
        match_in_questions = any(search_query.lower() in q["question"].lower() for q in questions_in_tag)
        if search_query.lower() in tag.lower() or match_in_questions or search_query == "":
            col_idx = idx % 4
            with cols[col_idx]:
                icon = category_icons.get(tag, "fas fa-question-circle")
                with st.form(key=f"category_form_{tag}"):
                    st.markdown(f""" <div class="category-card"> <button type="submit" name="category" value="{tag}" class="category-button"> <div class="category-icon"><i class="{icon}"></i></div> <div class="category-title">{tag}</div> </button> </div>""", unsafe_allow_html=True)
                    if st.form_submit_button(label="", use_container_width=True):
                        st.session_state["selected_category"] = tag

# --- Questions and Answers Section ---
if st.session_state.get("selected_category"):
    selected_category = st.session_state["selected_category"]
    st.markdown(f""" <div class="qa-section"> <h3 style="color: var(--dark);">Questions in {selected_category}</h3> </div>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Back to Categories", key="back_to_categories_top"):
        st.session_state["selected_category"] = None
        st.session_state["active_question"] = None
        st.rerun()

    questions = tag_groups.get(selected_category, [])
    # Filter questions based on search query
    filtered_questions = [q for q in questions if search_query.lower() in q["question"].lower() or search_query == ""]

    # Step 1: Move question selection outside the loop with immediate rerun
    if st.session_state.get("active_question") is None and filtered_questions:
        for q in filtered_questions:
            q_id = q.get("id", "")
            if st.button(f"🔷 {q.get('question')}", key=f"question_{q_id}"):
                st.session_state["active_question"] = q_id
                st.rerun()

    # Step 2: Show answer and related content outside the loop
    if st.session_state.get("active_question"):
        selected_qid = st.session_state["active_question"]
        selected_q = next(q for q in questions if q.get("id") == selected_qid)
        q_text = selected_q["question"]
        q_id = selected_q["id"]

        # Generate or retrieve answer if not already in session state
        if f"answer_{q_id}" not in st.session_state:
            with st.spinner("🔍 Retrieving and generating answer..."):
                context = retrieve_context(q_text, source_filter=st.session_state.get("latest_uploaded_filename"))
                if context and not context.startswith("❌"):
                    answer = ask_llm(q_text, context)
                    fund_name = st.session_state.get("latest_uploaded_filename")
                    append_qa_result(fund_name, q_text, answer)
                    st.session_state[f"answer_{q_id}"] = answer
                    st.session_state[f"context_{q_id}"] = context
                else:
                    st.session_state[f"answer_{q_id}"] = "⚠️ No relevant information found."

        answer = st.session_state.get(f"answer_{q_id}", "⚠️ No answer available.")
        st.markdown(f"""
        <div class="chat-message-user">
            <strong>Q:</strong> {q_text}
        </div>
        <div class="chat-message-assistant">
            <strong>A:</strong> {answer}
        </div>
        """, unsafe_allow_html=True)

        # Add enhancement buttons with bn49 style
        html_content = f"""
        <div style="display: flex; justify-content: space-between; margin-top: 10px;">
            <a href="#" class="bn49 reformulate-btn" data-key="reformulate_{q_id}" style="margin-right: 5px;">📝 Reformulate</a>
            <a href="#" class="bn49 concise-btn" data-key="concise_{q_id}" style="margin-right: 5px;">🔁 Make Concise</a>
            <a href="#" class="bn49 regulate-btn" data-key="regulate_{q_id}">📜 Add Regulation</a>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
        st.markdown("""
        <script>
            function attachClickHandler(className) {
                document.querySelectorAll('.' + className).forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        const buttonKey = btn.getAttribute('data-key');
                        const targetButton = document.querySelector('button[data-key="' + buttonKey + '"]');
                        if (targetButton) {
                            targetButton.click();
                        } else {
                            console.error('Button with data-key="' + buttonKey + '" not found');
                        }
                    });
                });
            }

            attachClickHandler('reformulate-btn');
            attachClickHandler('concise-btn');
            attachClickHandler('regulate-btn');
        </script>
        """, unsafe_allow_html=True)
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🪄 Reformulate", key=f"reformulate_{q_id}"):
                    with st.spinner("🔧 Reformulating..."):
                        try:
                            refined_answer = apply_feedback_to_answer("Reformulate this", q_text, answer)
                            st.session_state[f"refined_answer_{q_id}"] = refined_answer
                        except Exception as e:
                            st.error(f"❌ Failed to reformulate: {e}")
            with col2:
                if st.button("🔁 Make Concise", key=f"concise_{q_id}"):
                    with st.spinner("🔧 Making concise..."):
                        try:
                            refined_answer = apply_feedback_to_answer("Make it more concise", q_text, answer)
                            st.session_state[f"refined_answer_{q_id}"] = refined_answer
                        except Exception as e:
                            st.error(f"❌ Failed to make concise: {e}")
            with col3:
                if st.button("🛡️ Add Regulation", key=f"regulate_{q_id}"):
                    with st.spinner("🔧 Adding regulatory context..."):
                        try:
                            refined_answer = apply_feedback_to_answer("Add regulatory context", q_text, answer)
                            st.session_state[f"refined_answer_{q_id}"] = refined_answer
                        except Exception as e:
                            st.error(f"❌ Failed to add regulation: {e}")
        # Display refined answer if it exists
        if f"refined_answer_{q_id}" in st.session_state:
            st.markdown("### ✨ Refined Answer:")
            st.success(st.session_state[f"refined_answer_{q_id}"])

        # Add follow-up chatbot input
        followup = st.text_input("💬 Ask a follow-up:", key=f"followup_{q_id}")
        if followup:
            with st.spinner("💬 Generating response..."):
                reply = platform_assistant_safe_answer(followup)
            if "❓ Sorry" in reply:
                st.warning(f"**🤖 Bot:** {reply}")
            else:
                st.info(f"**🤖 Bot:** {reply}")

        # Add Back to Questions button
        if st.button("⬅️ Back to Questions", key=f"back_{q_id}"):
            st.session_state["active_question"] = None
            st.rerun()
        if st.button("⬅️ Back to Categories", key="back_to_categories_bottom"):
            st.session_state["selected_category"] = None
            st.session_state["active_question"] = None
            st.rerun()

# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

# --- Generate Final Due Diligence Report ---
st.markdown("""
<div class="category-section">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">within few seconds</h5>
        <h1>Generate a report</h1>
    </div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.get("pptx_generated", False):
    if st.button("📅 Generate Executive PPTX Report"):
        with st.spinner("🧐 Compiling report slides..."):
            try:
                fund_name = st.session_state.get("latest_uploaded_filename")
                generate_pptx_main()
                st.session_state["pptx_generated"] = True
                st.success("✅ Report generated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to generate report: {e}")
else:
    # Read the PPTX file and encode it as base64
    try:
        with open("output/due_diligence_report.pptx", "rb") as pptx_file:
            pptx_data = pptx_file.read()
            pptx_base64 = base64.b64encode(pptx_data).decode()
        # Create the download link with the custom button inside
        st.markdown(f"""
        <a href="data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{pptx_base64}" download="due_diligence_report.pptx" class="download-link">
            <button class="botao">
                <svg class="mysvg" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" height="24px" width="24px">
                    <g stroke-width="0" id="SVGRepo_bgCarrier"></g>
                    <g stroke-linejoin="round" stroke-linecap="round" id="SVGRepo_tracerCarrier"></g>
                    <g id="SVGRepo_iconCarrier">
                        <g id="Interface / Download">
                            <path stroke-linejoin="round" stroke-linecap="round" stroke-width="2" stroke="#f1f1f1" d="M6 21H18M12 3V17M12 17L17 12M12 17L7 12" id="Vector"></path>
                        </g>
                    </g>
                </svg>
                <span class="texto">Download</span>
            </button>
        </a>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Failed to load the report for download: {e}")
        # --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)


# --- Button Styling (Copied from home_page.py) ---
st.markdown("""
<style>
.btn-primary {
    background-color: #06A3DA;
    color: white;
    font-size: 16px;
    padding: 10px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.btn-primary:hover {
    background-color: #048fc2;
    color: white;
}
</style>
""", unsafe_allow_html=True)
# --- Button Styling (Copied from home_page.py) ---
st.markdown("""
<style>
.btn-primary {
    background-color: #06A3DA;
    color: white;
    font-size: 16px;
    padding: 10px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.btn-primary:hover {
    background-color: #048fc2;
    color: white;
}
</style>
""", unsafe_allow_html=True)
st.markdown("---")


# ---  Feedback Form  ---
# --- Styled Feedback Form with .bn49 Button ---
st.markdown("""
<style>
.feedback-wrapper {
    background-color: #ffffff;
    border: 1px solid #cce4f9;
    border-radius: 16px;
    padding: 25px 30px;
    max-width: 600px;
    margin: 0 auto 60px auto;
    box-shadow: 0 0 20px rgba(6, 163, 218, 0.25);
    text-align: center;
}

.feedback-wrapper h3 {
    color: #011f3f;
    margin-bottom: 15px;
    font-size: 26px;
    font-weight: 800;
}

textarea.feedback-textarea {
    width: 100%;
    height: 120px;
    padding: 15px;
    font-size: 16px;
    border-radius: 10px;
    border: 1px solid #a0c4ff;
    resize: none;
    background: #f8fbff;
    box-shadow: inset 0 0 8px rgba(6, 163, 218, 0.15);
    font-family: "Segoe UI", sans-serif;
}

textarea.feedback-textarea:focus {
    outline: none;
    border-color: #06a3da;
    box-shadow: 0 0 10px rgba(6, 163, 218, 0.3);
}

.bn49 {
  border: 0;
  text-align: center;
  display: inline-block;
  padding: 14px;
  margin-top: 20px;
  color: #ffffff !important;
  width: 220px;
  font-size: 18px;
  background-color: #36a2eb;
  border-radius: 8px;
  font-family: "Segoe UI", sans-serif;
  font-weight: 600;
  text-decoration: none !important;
  transition: box-shadow 200ms ease-out;
}

.bn49:hover {
  box-shadow: 0 0 10px rgba(54, 162, 235, 0.7);
}
</style>

<div class="feedback-wrapper">
    <h3>We Value Your Feedback</h3>
    <textarea class="feedback-textarea" id="custom_feedback" placeholder="Type your feedback here..."></textarea>
    <button class="bn49" onclick="sendFeedback()">📤 Send</button>
</div>

<script>
function sendFeedback() {
    const message = document.getElementById("custom_feedback").value;
    if (message.trim() !== "") {
        window.parent.postMessage({type: 'streamlit:toast', message: '💌 Thank you for your feedback!'}, '*');
    } else {
        window.parent.postMessage({type: 'streamlit:toast', message: '⚠️ Please enter something.'}, '*');
    }
}
</script>
""", unsafe_allow_html=True)


st.markdown('<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>', unsafe_allow_html=True)


