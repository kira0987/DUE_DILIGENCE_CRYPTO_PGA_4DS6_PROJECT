import streamlit as st
import base64

# --- Set Page Config ---
st.set_page_config(
    page_title="DUEXPERT - Crypto Fund Due Diligence",
    page_icon="💼",
    layout="wide"
)

# --- Animated Background Styling ---
page_bg_img = """
<style>
@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(-45deg, #141E30, #243B55, #141E30, #243B55);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    color: white;
    font-family: 'Segoe UI', sans-serif;
    padding-top: 1rem;
}
[data-testid="stHeader"] {
    background: rgba(0, 0, 0, 0);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #243B55 0%, #141E30 100%);
    color: white;
    padding: 2rem 1rem;
}
[data-testid="stSidebarNav"] {
    padding-top: 2rem;
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
.sidebar-title {
    font-size: 26px;
    font-weight: bold;
    color: #00FFFF;
    text-align: center;
    text-decoration: underline;
    margin-top: 10px;
}
.big-font {
    font-size: 54px !important;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 0.5rem;
}
.medium-font {
    font-size: 22px !important;
    color: #D3D3D3;
    margin-bottom: 1rem;
}
.feature-card {
    background: rgba(255, 255, 255, 0.08);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
    height: 250px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: all 0.3s ease-in-out;
}
.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 25px rgba(0,0,0,0.5);
}
.feature-icon {
    font-size: 36px;
    margin-bottom: 10px;
}
.feature-title {
    font-size: 22px;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 8px;
}
.feature-description {
    font-size: 17px;
    color: #E0E0E0;
    line-height: 1.5;
    font-weight: 500;
}
hr {
    margin-top: 0.5rem;
    margin-bottom: 1rem;
    border: 0;
    border-top: 1px solid #ccc;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- Sidebar Logo + Title (Corrected with base64 encoding) ---
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

with st.sidebar:
    img_base64 = get_image_base64("assets/logo (1).png")  # ✅ Correctly load your image
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem;'>
            <img src="data:image/png;base64,{img_base64}" style="width:110px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0,0,0,0.2);">
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">DUEXPERT</div>', unsafe_allow_html=True)

# --- Main Title ---
st.markdown('<p class="big-font">💼 Crypto Fund Due Diligence Automation</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">Simplify, Automate, and Improve Due Diligence for Cryptocurrency Investments</p>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Features Section ---
st.subheader("🔎 Why Use This Platform?")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📚</div>
        <div class="feature-title">Automated Data Collection</div>
        <div class="feature-description">
            Collect documents, APIs, and websites.<br>
            Extract text, tables, and images automatically.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">Intelligent Q&A System</div>
        <div class="feature-description">
            Ask questions to AI.<br>
            Get smart answers about compliance (SEC, AML, KYC).
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Generate Professional Reports</div>
        <div class="feature-description">
            Instant PowerPoint reports.<br>
            Summarize Risk, Compliance, and Investment data.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Footer ---
st.markdown('<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>', unsafe_allow_html=True)
