import streamlit as st
import os
import base64
from datetime import datetime
import streamlit.components.v1 as components

# --- Streamlit Config ---
st.set_page_config(
    page_title="DueXpert - Reports History",
    page_icon="📄",
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

# --- Load Background Image ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        st.error(f"Error loading image {bin_file}: {e}")
        return ""

logo_image = get_base64_of_bin_file('images/Logo2.png')

# --- Inject Custom Styling ---
page_bg_img = """
<!-- FontAwesome (Global Scope) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">

<!-- Google Fonts - Open Sans -->
<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700" rel="stylesheet">

<style>
:root {
    --primary: #06a3da;  /* DueXpert Blue */
    --dark: #011f3f;     /* Dark Blue */
    --light: #f8f8f8;    /* Light Gray */
    --hover-darken: #048fc2; /* Darkened Primary for hover */
}

/* Full width remove padding and adjust for sidebar */
[data-testid="stAppViewContainer"] {
    background-color: var(--light);
    padding: 20px;
    margin: 0px;
    margin-left: 300px;
}
[data-testid="stAppViewContainer"] > div {
    padding: 0 !important;
    margin: 0 !important;
}
.css-1d391kg, .css-1v0mbdj {
    padding: 0rem;
    margin: 0rem;
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

/* Responsive Design for Sidebar */
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

.section-title {
    margin-top: 0;
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
    background: #06a3da;
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

.section-title h1 {
    font-size: 36px;
    font-weight: 800;
    color: #011f3f;
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
            <a href="/duediligence"><i class="fas fa-search"></i>Due Diligence</a>
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

# --- Reports History Section ---
UPLOADED_DIR = "data/uploaded/"

st.markdown("""
<div class="section-title">
    <h1>Reports History</h1>
</div>
""", unsafe_allow_html=True)

# Detect all uploaded .pdf reports
try:
    pdf_files = [f for f in os.listdir(UPLOADED_DIR) if f.endswith('.pdf')]
except Exception as e:
    st.error(f"Error accessing {UPLOADED_DIR}: {e}")
    pdf_files = []

# --- Add Search Bar and Date Filters ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input("", "", placeholder=" 🔍 Type any keyword (fund name, date, size...)")
with col2:
    start_date = st.date_input("📅 Start date", value=None)
with col3:
    end_date = st.date_input("📅 End date", value=None)

# --- Reports Table Block ---
if pdf_files:
    table_html = """
    <style>
        .blue-table {
            border-collapse: collapse;
            width: 100%;
            font-family: 'Open Sans', sans-serif;
            margin-top: 20px;
            border: 1px solid #ddd;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
        }

        .blue-table caption {
            caption-side: top;
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
            color: #06a3da;
            text-align: center;
        }

        .blue-table th {
            background-color: #06a3da;
            color: white;
            padding: 12px;
            text-align: left;
        }

        .blue-table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            color: #011f3f;
            font-weight: 500;
        }

        .blue-table tr:hover {
            background-color: #f1f9ff;
        }

        .blue-table td a {
            color: #06a3da;
            font-weight: bold;
            text-decoration: none;
        }

        .blue-table td a:hover {
            color: #048fc2;
        }
    </style>

    <table class="blue-table">
        <thead>
            <tr>
                <th>Fund Name</th>
                <th>Upload Date</th>
                <th>Size (KB)</th>
                <th>Download</th>
            </tr>
        </thead>
        <tbody>
    """

    for pdf_file in sorted(pdf_files, key=lambda x: os.path.getmtime(os.path.join(UPLOADED_DIR, x)), reverse=True):
        file_path = os.path.join(UPLOADED_DIR, pdf_file)
        try:
            file_size_kb = os.path.getsize(file_path) / 1024
            upload_time = os.path.getmtime(file_path)
            upload_date = datetime.fromtimestamp(upload_time).strftime('%Y-%m-%d %H:%M:%S')
            fund_name = os.path.splitext(pdf_file)[0]

            # Combine all fields into one lowercase string for search
            row_text = f"{fund_name} {upload_date} {file_size_kb:.2f} Download".lower()

            # Apply text search
            if search_query and search_query.lower() not in row_text:
                continue

            # Apply date range filter
            upload_datetime = datetime.fromtimestamp(upload_time)
            if start_date and upload_datetime.date() < start_date:
                continue
            if end_date and upload_datetime.date() > end_date:
                continue

            # Base64 download
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            download_link = f"data:application/pdf;base64,{b64}"

            table_html += f"""
            <tr>
                <td>{fund_name}</td>
                <td>{upload_date}</td>
                <td>{file_size_kb:.2f}</td>
                <td><a href="{download_link}" download="{pdf_file}">Download</a></td>
            </tr>
            """
        except Exception as e:
            st.warning(f"Error processing {pdf_file}: {e}")
            continue

    # Add message if no results match
    if table_html.endswith("<tbody>\n"):
        table_html += """
        <tr>
            <td colspan="4" style="text-align:center; color: gray;">🔎 No results found for your search or date range.</td>
        </tr>
        """

    table_html += """
        </tbody>
    </table>
    """

    components.html(table_html, height=600, scrolling=True)
else:
    st.info("📄 No reports have been uploaded yet.")

# --- Footer ---
st.markdown("---")
st.markdown('<center><p style="font-size:16px;">Powered by AI | DUEXPERT © 2025</p></center>', unsafe_allow_html=True)