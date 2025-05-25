import streamlit.components.v1 as components
import base64
import torch
import sys
import os
sys.path.append(os.path.abspath("scripts"))
from scripts.llm_responder import platform_assistant_safe_answer

_ = torch.classes  # Fix for PyTorch + Streamlit runtime issue
import streamlit as st

st.set_page_config(
    page_title="DueXpert | Home",
    page_icon="🏠",
    layout="wide",
)

# Handle navbar redirection to other pages
if st.query_params.get("page") == ["duediligence"]:
    st.switch_page("duediligence.py")

# --- Streamlit Config ---
# --- Hide Streamlit Default Header/Footer and Sidebar ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
[data-testid="stAppViewContainer"] {
    margin-left: 0px;
    padding-left: 0px;
}
</style>
""", unsafe_allow_html=True)

# --- Load Background Image ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_image = get_base64_of_bin_file('images/back.png')
crypto_image = get_base64_of_bin_file('images/crypto.jpeg')
logo_image = get_base64_of_bin_file('images/Logo2.png')
about_image = get_base64_of_bin_file('images/crypto.jpeg')  # Add your about image here

# --- Inject Custom Styling: Full Width and Navbar ---
page_bg_img = f"""
<!-- FontAwesome (Global Scope) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">

<style>
/* Full width remove padding */
[data-testid="stAppViewContainer"] {{
    background-color: #f8f8f8;
    padding: 50px;
    margin: 0px;
}}
[data-testid="stAppViewContainer"] > div {{
    padding: 0 !important;
    margin: 0 !important;
}}
.css-1d391kg, .css-1v0mbdj {{
    padding: 0rem;
    margin: 0rem;
}}

/* Navbar */
.navbar {{
    background: #ffffff;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    position: fixed;
    top: 30px;
    left: 5%;
    width: 90%;
    z-index: 9999;
}}
.navbar a {{
    color: black;
    text-decoration: none;
    margin-left: 2rem;
    font-size: 20px;
    font-weight: bold;
}}
.navbar a:hover {{
    color: #409eff;
    transition: 0.3s;
}}
.navbar img {{
    width: 50px;
    height: 50px;
    object-fit: contain;
    border: none;
}}
.medium-font {{
    font-size: 20px !important;
    color: #666666;
    line-height: 1.6;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- Navbar ---
st.markdown(f"""
<div class="navbar">
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{logo_image}">
        <span style="font-size:36px; font-weight:bold; margin-left:15px; color: #06a3da;">Due<span style="color: #00658a;">X</span>pert</span>
    </div>
    <div style="display: flex; gap: '30'px;">
        <a href="#">Home</a>
        <a href="\duediligence">Due Diligence</a>
        <a href="#">Risk Scoring </a>
        <a href="#">Reports</a>
        <a href="#">Subscription</a>
    </div>
</div>
""", unsafe_allow_html=True)

# --- About Us Styling ---
about_style = """
<style>
:root {
    --primary: #06a3da;
    --secondary: #1847a8;
    --light: #f8f8f8;
    --dark: #011f3f;
}

/* Override Streamlit Column Padding */
[data-testid="column"] [data-testid="stVerticalBlock"] {
    padding-left: 0 !important;
    margin-left: 0 !important;
}

/* Ensure row alignment for image and text */
.row {
    display: flex;
    flex-wrap: wrap;
    margin-left: 0 !important;
    margin-right: 0 !important;
}
.g-4 {
    margin-bottom: 1.5rem !important;
}
.align-items-center {
    align-items: center !important;
}
.col-lg-6 {
    flex: 0 0 50%;
    max-width: 50%;
    padding-left: 0 !important;
    padding-right: 15px;
}

/* Left-Aligned Underline Animation for About Us */
.left-aligned-underline {
    text-align: left;
    position: relative;
    padding-bottom: 10px;
    margin-bottom: 30px;
}
.left-aligned-underline::before {
    content: "";
    width: 150px;
    height: 5px;
    background: var(--primary);
    position: absolute;
    bottom: 0;
    left: 0;
    border-radius: 3px;
    animation: underlineWithDot 3s infinite;
}
.left-aligned-underline::after {
    content: "";
    width: 10px;
    height: 10px;
    background: white;
    position: absolute;
    bottom: -2.5px;
    left: 0;
    border-radius: 50%;
    animation: dotMoveLeft 3s infinite;
}
@keyframes underlineWithDot {
    0%, 100% { width: 0; }
    50% { width: 150px; }
}
@keyframes dotMoveLeft {
    0% { left: 0; }
    50% { left: 75px; }
    100% { left: 150px; }
}
.text-uppercase {
    text-transform: uppercase !important;
}
.text-primary {
    color: var(--primary) !important;
    font-size: 26px;
}
.fw-semi-bold {
    font-weight: 600 !important;
}
.display-5 {
    font-size: 36px;
    font-weight: 800;
    color: var(--dark);
    line-height: 1.2;
    margin-left: 0 !important;
    padding-left: 0 !important;
}
.mb-4 {
    margin-bottom: 1.5rem !important;
}

.check-item {
    font-size: 16px;
    color: #000000;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    margin-left: 0 !important;
    padding-left: 0 !important;
}
.check-emoji {
    color: #06a3da;
    margin-right: 10px;
    font-size: 20px;
    font-weight: bold;
}
.call-box {
    display: inline-flex;
    align-items: center;
    gap: 15px;
    background: #06a3da;
    color: #ffffff;
    padding: 15px 25px;
    border-radius: 10px;
    margin-bottom: 30px;
    font-size: 16px;
    font-weight: 500;
}
.call-box i {
    font-size: 24px;
}
.quote-btn {
    padding: 12px 30px;
    font-size: 18px;
    font-weight: 600;
    border: none;
    border-radius: 30px;
    background: #06a3da;
    color: #ffffff;
    text-decoration: none;
    transition: all 0.4s ease;
    display: inline-block;
}
.quote-btn:hover {
    background: linear-gradient(90deg, #1847a8, #3470fc);
    transform: scale(1.05);
    box-shadow: 0 0 15px rgba(52, 112, 252, 0.5);
}
.about-text {
    color: #000000;
    font-size: 40px;             /* Make the text bigger */
    line-height: 2;            /* Add spacing between lines */
    font-weight: 500;            /* Make it less thin */
    padding-right: 20px;         /* Add some breathing room */
    padding-left: 0 !important;
    margin-left: 0 !important;
    margin-bottom: 30px;
    text-align: justify;         /* Optional: aligns both sides of the paragraph */
}


.img-fluid {
    max-width: 20%;
    height: 50%;
    border-radius: 5px;
    border: 4px solid #06a3da;
    box-shadow: 0 8px 24px rgba(6, 163, 218, 0.4);
    transition: transform 0.4s ease;
}

.img-fluid:hover {
    transform: scale(1.03);
}


.rounded {
    border-radius: 20px !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
</style>
"""
st.markdown(about_style, unsafe_allow_html=True)

# --- About Us Section ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title left-aligned-underline">
        <h5 class="text-primary text-uppercase">About Us</h5>
    </div>
</div>
""", unsafe_allow_html=True)

# Use HTML row for better alignment instead of st.columns
st.markdown(f"""
<div class="row g-4 align-items-center">
    <div class="col-lg-6">
        <div style="margin-left: 0 !important; padding-left: 0 !important;">
            <h1 class="display-5 mb-4">We Empower Investors Through Automated Crypto Fund Due Diligence</h1>
            <p class="about-text">DueXpert is an AI-powered platform designed to streamline the due diligence process
                for crypto investment funds. By analyzing complex documents
                — from legal disclosures to fund strategies — we help investors uncover critical risks,
                verify claims, and evaluate opportunities without the guesswork.
                <br>
                Our mission is simple: <b>turn information overload into clarity.</b>
                Whether you're an institutional investor, auditor, or analyst,
                DueXpert equips you with the structured answers you need to make fast, 
                confident, and well-informed decisions.
            </p>
            <a class="btn btn-primary py-3 px-5 rounded-pill shadow-sm" href="#">Get Started</a>
        </div>
    </div>
    <div class="col-lg-6">
        <img class="img-fluid rounded" src="data:image/jpeg;base64,{about_image}" alt="About Us">
    </div>
</div>
""", unsafe_allow_html=True)

# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

# --- Services Section Styling ---
st.markdown("""
<style>
:root {
    --primary: #06a3da;
    --dark: #011f3f;
    --light: #f8f8f8;
}

.service-section {
    padding: 50px 15px !important;
    background: var(--light) !important;
    text-align: center !important;
}

.section-title {
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

.service-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 20px rgba(52, 112, 252, 0.4);
    transition: transform 0.3s ease;
    width: 350px !important; /* Fixed width for consistency */
    min-height: 500px !important; /* Minimum height to ensure uniformity */
    margin: 0 auto; /* Center the card within the column */
    display: flex;
    flex-direction: column;
    justify-content: space-between; /* Distribute content evenly */
}

.service-card:hover {
    transform: scale(1.05);
}

.service-icon {
    font-size: 36px;
    color: var(--primary);
    margin-bottom: 15px;
}

.service-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--dark);
    margin: 0 0 10px 0;
}

.service-desc {
    font-size: 16px;
    color: #666666;
    margin-bottom: 20px;
    padding: 0 10px;
}
</style>
""", unsafe_allow_html=True)
# --- Services Section ---
st.markdown("""
<div class="service-section">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">Our Services</h5>
        <h1>Explore What DueXpert Can Do</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# Use columns to create a grid of service cards
cols = st.columns(4)

with cols[0]:
    st.markdown("""
    <div class="service-card">
        <div class="service-icon"><i class="fas fa-cogs"></i></div>
        <div class="service-title">Due Diligence Automation</div>
        <div class="service-desc">Automate the entire due diligence workflow from document upload to AI-powered analysis and decision-ready outputs.</div>
        <a class="btn btn-primary py-2 px-4 rounded-pill shadow-sm" href="#">Explore</a>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    st.markdown("""
    <div class="service-card">
        <div class="service-icon"><i class="fas fa-question-circle"></i></div>
        <div class="service-title">Q&A Generation</div>
        <div class="service-desc">Ask any question and receive structured, document-based answers powered by intelligent AI retrieval and response generation.</div>
        <a class="btn btn-primary py-2 px-4 rounded-pill shadow-sm" href="#">Try Now</a>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown("""
    <div class="service-card">
        <div class="service-icon"><i class="fas fa-exclamation-triangle"></i></div>
        <div class="service-title">Risk Detection Engine</div>
        <div class="service-desc">Detect hidden financial, strategic, or compliance risks across complex fund documentation using LLM models.</div>
        <a class="btn btn-primary py-2 px-4 rounded-pill shadow-sm" href="#">Detect</a>
    </div>
    """, unsafe_allow_html=True)

with cols[3]:
    st.markdown("""
    <div class="service-card">
        <div class="service-icon"><i class="fas fa-file-powerpoint"></i></div>
        <div class="service-title">Instant Report Generation</div>
        <div class="service-desc">Generate executive-ready PowerPoint reports summarizing key findings, answers, and visual risk scores — instantly.</div>
        <a class="btn btn-primary py-2 px-4 rounded-pill shadow-sm" href="#">Generate</a>
    </div>
    """, unsafe_allow_html=True)

# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
# --- Spacer ---

st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

# --- Line Animation Under "Pricing Plans" ---
st.markdown("""
<style>
.section-title {
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
</style>
""", unsafe_allow_html=True)

# --- Pricing Plans Styling ---
pricing_style = """
<style>
:root {
    --primary: #06a3da;
    --secondary: #1847a8;
    --light: #f8f8f8;
    --dark: #011f3f;
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
.text-center {
    text-align: center !important;
}
.pricing-item {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 20px rgba(52, 112, 252, 0.4);
    transition: transform 0.3s ease;
}
.pricing-item:hover {
    transform: scale(1.05);
}
.pricing-item h4 {
    font-size: 24px;
    font-weight: 600;
    color: var(--primary);
    margin: 0;
}
.pricing-item small {
    font-size: 14px;
    text-transform: uppercase;
    color: #666666;
}
.pricing-item h1 {
    font-size: 40px;
    font-weight: 700;
    color: var(--dark);
}
.pricing-item .feature {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    color: #000000;
    font-size: 16px;
}
</style>
"""
st.markdown(pricing_style, unsafe_allow_html=True)

# --- Pricing Plans Section ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title text-center">
        <h5 class="fw-bold text-primary text-uppercase">Pricing Plans</h5>
        <h1 class="mb-0">We are Offering Competitive <br>Prices for Our Clients</h1>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="pricing-item">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Basic Plan</h4>
            <small class="text-uppercase">For Individual Investors</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>49.00
                <small style="font-size: 16px; vertical-align: bottom;">/h</small>
            </h1>
            <div class="feature"><span>Risk Scoring</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Basic Analytics</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Risk Scoring</span><i class="fa fa-times text-danger"></i></div>
            <div class="feature"><span>PPTX Reports</span><i class="fa fa-times text-danger"></i></div>
            <a class="btn btn-primary py-3 px-5 rounded-pill shadow-sm" href="#">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="pricing-item" style="box-shadow: 0 0 30px rgba(52, 112, 252, 0.5); position: relative; z-index: 1;">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Standard Plan</h4>
            <small class="text-uppercase">For Small Funds</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>199
                <small style="font-size: 16px; vertical-align: bottom;">/h</small>
            </h1>
            <div class="feature"><span>Risk Scoring</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Advanced Analytics</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Deep Search</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>PPTX Reports</span><i class="fa fa-times text-danger"></i></div>
            <a class="btn btn-primary py-3 px-5 rounded-pill shadow-sm" href="#">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="pricing-item">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Advanced Plan</h4>
            <small class="text-uppercase">For Large Funds</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>1500
                <small style="font-size: 16px; vertical-align: bottom;">/month</small>
            </h1>
            <div class="feature"><span>Risk Scoring</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Advanced Analytics</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Deep Search</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>PPTX Reports</span><i class="fa fa-check text-primary"></i></div>
            <a class="btn btn-primary py-3 px-5 rounded-pill shadow-sm" href="#">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

# --- Chatbot Section ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title text-center">
        <h5 class="fw-bold text-primary text-uppercase">Assistant Chatbot</h5>
        <h1 class="mb-0">Ask anything about the DueXpert platform, <br> our features & services</h1>
    </div>
</div>
""", unsafe_allow_html=True)

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

# --- Spacer ---
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

# --- Button Styling (Applied Across Homepage) ---
st.markdown("""
<style>
.btn-primary {
    background-color: #06A3DA; /* Light cyan-blue */
    color: white;
    font-size: 16px;
    padding: 10px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.btn-primary:hover {
    background-color: #048fc2; /* Slightly darker blue on hover */
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.markdown("---")

st.markdown('<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>', unsafe_allow_html=True)