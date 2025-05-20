import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict
import base64
import os
import json
import matplotlib.pyplot as plt

from scripts.risk_calculator import calculate_risk_score, analyze_tag_text, detect_negative_sentiment, IMPORTANCE_WEIGHTS

# --- Streamlit Config ---
st.set_page_config(
    page_title="DueXpert - Risk Dashboard",
    page_icon="📊",
    layout="wide",
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
# --- Function to Encode Image as Base64 ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_image = get_base64_of_bin_file('images/Logo2.png')

# --- Custom CSS Styling (Reused from duediligence.py) ---
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
    justify-content: space-between;
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
    color: #06a3da;
    transition: 0.3s;
}

.sidebar a:hover {
    background: #e6f0fa;
    color: #06a3da;
}

.sidebar a:hover i {
    color: #ffffff;
}

.sidebar .bottom-links a {
    padding: 15px 20px;
}

.sidebar .pro-card {
    background: #06a3da;
    border-radius: 10px;
    padding: 15px;
    margin: 0 20px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    color: #ffffff;
    margin-top: auto;
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
        font-size: 0;
    }
    .sidebar a i {
        margin-right: 0;
        font-size: 24px;
    }
    .sidebar .logo-section span {
        display: none;
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
        margin-left: 80px;
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

/* Additional Styling for Dashboard */
.category-section {
    padding: 50px 15px !important;
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
            <p>Unlock DueXpert’s full toolkit insights, automation, and confident fund evaluations.!</p>
            <a href="#" class="pro-button">Get started with PRO</a>
        </div>
        <div class="bottom-icons">
            <a href="#"><i class="fas fa-gear"></i>Setting & Subscription</a>
            <a href="#"><i class="fas fa-sign-out-alt"></i>Logout</a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Load CSV and Classified JSON ---
try:
    # Load CSV
    df = pd.read_csv("data/auto_answered_questions.csv")

    # Normalize all column names to lowercase
    df.columns = [c.strip().lower() for c in df.columns]  # now "question", "answer", etc.

    # Normalize "question" content (strip whitespace and lowercase)
    df["question"] = df["question"].astype(str).str.strip().str.lower()

    # Load and normalize classified questions
    with open("data/classified_questions.json", "r") as f:
        classified = json.load(f)

    # Normalize keys in tag map to lowercase
    tag_map = {q["question"].strip().lower(): q["tag"] for q in classified}

    # Map tags into DataFrame using normalized question
    df["tag"] = df["question"].map(tag_map)

except FileNotFoundError:
    st.error("❌ Required files ('auto_answered_questions.csv' or 'classified_questions.json') not found.")
    st.stop()

except Exception as e:
    st.error(f"❌ Unexpected error: {e}")
    st.stop()

# --- Generate Findings and Issues for Each Category ---
tag_findings = defaultdict(lambda: ([], []))

for q in classified:
    question = q["question"].strip().lower()  # Normalize question for consistency
    tag = q["tag"]
    row = df[df["question"] == question]
    if not row.empty and not detect_negative_sentiment(row.iloc[0]["answer"]):
        tag_findings[tag][0].append(row.iloc[0]["answer"])
    else:
        tag_findings[tag][1].append(question)

# --- Analyze Tags and Calculate Risk Scores ---
analysis = {}
for tag in tag_findings:
    findings, issues = tag_findings[tag]
    analysis[tag] = analyze_tag_text(tag, findings, issues)

risk_scores = calculate_risk_score(analysis, df, classified)

# --- Title Section ---
st.markdown("""
<div class="category-section">
    <div class="section-title">
        <h1>Risk Scoring</h1>
        <h5 class="fw-bold text-primary text-uppercase">Engine </h5>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Display Risk Score Per Category with Emojis/Color ---
st.markdown("### 📂 Risk Scores by Category")
for tag, score in sorted(risk_scores.items(), key=lambda x: -x[1]):
    color = "🔴" if score >= 60 else "🟠" if score >= 30 else "🟢"
    st.markdown(f"<div style='font-size:18px'><strong>{color} {tag}</strong>: {score:.1f}</div>", unsafe_allow_html=True)

# --- Show Total Weighted Risk Score ---
total_weight = sum(IMPORTANCE_WEIGHTS.get(tag, 0) for tag in risk_scores)
total_risk = sum(risk_scores[tag] * IMPORTANCE_WEIGHTS.get(tag, 0) for tag in risk_scores)
overall_risk = total_risk / total_weight if total_weight > 0 else 0

st.markdown("""
<div style='
    background-color:#011f3f;
    color:#ffffff;
    padding:20px;
    border-radius:12px;
    text-align:center;
    font-size:20px;
    margin:20px 0;'
>
    <strong>🌐 Total Weighted Risk Score:</strong> {:.1f}
</div>
""".format(overall_risk), unsafe_allow_html=True)

# --- Plot Histogram (Using Chart.js) ---

tags = list(risk_scores.keys())
scores = [risk_scores[t] for t in tags]
colors = ['#FF4136' if s >= 60 else '#FF851B' if s >= 30 else '#2ECC40' for s in scores]
st.markdown("### 📊 Risk Score Distribution")

tags = list(risk_scores.keys())
scores = [risk_scores[t] for t in tags]
colors = ['#FF4136' if s >= 60 else '#FF851B' if s >= 30 else '#2ECC40' for s in scores]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(tags, scores, color=colors)

ax.set_xlim([0, 100])
ax.set_xlabel("Risk Score (0-100)", fontsize=12)
ax.set_title("Risk Scores by Category", fontsize=14)
ax.invert_yaxis()  # Highest score on top
ax.grid(axis='x', linestyle='--', alpha=0.7)

# Add score labels to bars
for i, v in enumerate(scores):
    ax.text(v + 1, i, f"{v:.1f}", va='center', fontsize=10)

st.pyplot(fig)

st.markdown("### 💡 Recommendations")

for tag in sorted(risk_scores, key=lambda x: -risk_scores[x]):
    score = risk_scores[tag]
    missing_list = analysis[tag]['missing']
    missing_items = ', '.join(missing_list)[:100] + ('...' if len(', '.join(missing_list)) > 100 else '')
    
    if score >= 60:
        st.error(f"🚨 {tag}: High risk ({score:.1f}). Address: {missing_items}")
    elif score >= 30:
        st.warning(f"⚠️ {tag}: Medium risk ({score:.1f}). Review: {missing_items}")
    else:
        st.success(f"✅ {tag}: Low risk ({score:.1f}). No urgent issues.")

# --- Footer ---
st.markdown("""
<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>
""", unsafe_allow_html=True)
