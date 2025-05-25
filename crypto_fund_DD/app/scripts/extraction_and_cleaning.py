# scripts/extraction_and_cleaning.py

import os
import re
import io
import unicodedata
from datetime import datetime

import fitz  # PyMuPDF for PDF
from PIL import Image
import pytesseract
import pdfplumber
import pandas as pd
from langdetect import detect
from lib.mongo_helpers import update_fund_field

# --- Configure Tesseract if needed ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Directories ---
NEW_EXTRACTED_DIR = "data/new_extracted/"      # Save only new uploads here
EXTRACTED_DIR = "data/extracted_data/"          # Permanent archive for all cleaned data

os.makedirs(NEW_EXTRACTED_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)

# ----------------- Utility Functions -----------------

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"

def extract_tables_from_text(text: str) -> list:
    tables = []
    potential_table = []
    for line in text.splitlines():
        if re.search(r'\s{3,}|\t', line):
            potential_table.append(line)
        else:
            if potential_table:
                tables.append("\n".join(potential_table))
                potential_table = []
    if potential_table:
        tables.append("\n".join(potential_table))
    return tables

def clean_text(raw_text: str) -> str:
    text = unicodedata.normalize("NFKD", raw_text)
    text = re.sub(r"(page\s*\d+(\s*of\s*\d+)?)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(confidential|proprietary|internal use only)", "", text, flags=re.IGNORECASE)
    text = re.sub(r'(?m)^[^\n]{1,20}\n', '', text)
    text = re.sub(r'(?m)^\s*(\d{1,2}([-/]\d{1,2}){1,2})\s*$', '', text)
    text = re.sub(r'[_*\-=~•■◆►¤✦●⚫️★☆]+', ' ', text)
    text = re.sub(r'^[\s]*[\-\*•➤►▪️•⚫️●>]+[\s]+', '- ', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+)\.\s*', r'\1. ', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = text.splitlines()
    new_lines = []
    previous_line = None
    for line in lines:
        if line != previous_line:
            new_lines.append(line)
        previous_line = line
    text = "\n".join(new_lines)
    text = re.sub(r'(\d+)\.([A-Z])', r'\1. \2', text)
    text = re.sub(r'(?m)^[ \t]+', '', text)
    text = re.sub(r'(?m)[ \t]+$', '', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = text.strip()
    return text

def clean_csv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    df = df.fillna("")
    return df

def clean_excel(df: pd.DataFrame) -> pd.DataFrame:
    return clean_csv(df)

# ----------------- Extraction Functions -----------------

def extract_text_from_pdf(file) -> str:
    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf:
        page_text = page.get_text()
        if not page_text.strip():
            # Scanned PDF page, use OCR
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))
            page_text = pytesseract.image_to_string(img)
        text += page_text + "\n"
    return text

def extract_tables_from_pdf(file) -> list:
    tables = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extracted = page.extract_tables()
            if extracted:
                tables.extend(extracted)
    return tables

def extract_text_from_image(file) -> str:
    img = Image.open(file)
    return pytesseract.image_to_string(img)

def extract_text_from_txt(file) -> str:
    return file.read().decode('utf-8')

def extract_text_from_csv(file) -> str:
    df = pd.read_csv(file)
    df = clean_csv(df)
    return df.to_string(index=False)

def extract_text_from_excel(file) -> str:
    dfs = pd.read_excel(file, sheet_name=None)
    text = ""
    for sheet_name, df in dfs.items():
        df = clean_excel(df)
        text += f"\n--- Sheet: {sheet_name} ---\n"
        text += df.to_string(index=False) + "\n"
    return text

def detect_file_type_and_extract(file) -> str:
    name = file.name.lower()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif name.endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image(file)
    elif name.endswith(".txt"):
        return extract_text_from_txt(file)
    elif name.endswith(".csv"):
        return extract_text_from_csv(file)
    elif name.endswith(".xlsx"):
        return extract_text_from_excel(file)
    else:
        return "Unsupported file type."

# ----------------- Main Pipeline -----------------

def process_uploaded_file(uploaded_file):
    """
    Full professional pipeline: Extract -> Clean -> Detect Tables -> Detect Language -> Save all.
    """

    base_name = os.path.splitext(uploaded_file.name)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Extract raw text
    raw_text = detect_file_type_and_extract(uploaded_file)

    # Clean text
    cleaned_text = clean_text(raw_text)

    # Detect tables
    tables = extract_tables_from_text(cleaned_text)

    # Detect language
    detected_language = detect_language(cleaned_text)

    # Save raw text into NEW extracted folder
    raw_path = os.path.join(NEW_EXTRACTED_DIR, f"{base_name}_{timestamp}_raw.txt")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw_text)

    # Save cleaned text into NEW extracted folder
    clean_path = os.path.join(NEW_EXTRACTED_DIR, f"{base_name}_{timestamp}_cleaned.txt")
    with open(clean_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    # 🔽 Add this line right after saving raw_text to file
    update_fund_field(base_name, "raw_text", raw_text)
    # Save tables if any
    tables_paths = []
    if tables:
        for idx, table in enumerate(tables):
            table_path = os.path.join(NEW_EXTRACTED_DIR, f"{base_name}_{timestamp}_table_{idx+1}.txt")
            with open(table_path, "w", encoding="utf-8") as f:
                f.write(table)
            tables_paths.append(table_path)

    # Save metadata (language)
    meta_path = os.path.join(NEW_EXTRACTED_DIR, f"{base_name}_{timestamp}_meta.txt")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"Detected Language: {detected_language}\n")

    return {
        "raw_text_path": raw_path,
        "cleaned_text_path": clean_path,
        "tables_paths": tables_paths,
        "language": detected_language
    }
