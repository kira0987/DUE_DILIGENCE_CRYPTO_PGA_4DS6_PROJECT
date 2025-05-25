import os
import json
import streamlit as st
from modules.pdf_text_extractor import extract_text_from_pdf
from modules.text_cleaning import clean_text
from modules.pdf_feature_extractor import extract_entities
from modules.text_chunker import smart_chunk_text, save_chunks_to_json
from modules.vector_database import save_to_faiss, search_faiss

# 📌 Directories
UPLOAD_DIR = "uploaded_pdfs"
EXTRACTED_DIR = os.path.join(UPLOAD_DIR, "extracted")
os.makedirs(EXTRACTED_DIR, exist_ok=True)

# 🎨 Streamlit UI
st.set_page_config(page_title="Crypto Due Diligence", layout="wide")

st.title("📄 Crypto Due Diligence AI")
st.markdown("🔍 Upload a *PDF* document to analyze its financial, crypto, and legal risks.")

# 📌 File Uploader
uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file is not None:
    pdf_filename = uploaded_file.name
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)

    # Save uploaded file
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ File {pdf_filename} uploaded successfully!")

    # 📌 Step 1: Extract Text
    st.write("📄 Extracting text...")
    extracted_text = extract_text_from_pdf(pdf_path)

    # Save extracted text
    text_file = os.path.join(EXTRACTED_DIR, f"{pdf_filename}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    st.success("✅ Text extracted successfully!")

    # 📌 Step 2: Clean Text
    st.write("🧹 Cleaning text...")
    cleaned_text = clean_text(extracted_text)
    st.success("✅ Text cleaned!")

    # 📌 Step 3: Extract Entities
    st.write("📊 Extracting entities (financial, crypto, legal)...")
    analysis_results = extract_entities(cleaned_text)

    # Save analysis results
    analysis_file = os.path.join(EXTRACTED_DIR, f"{pdf_filename}_analysis.json")
    with open(analysis_file, "w", encoding="utf-8") as json_file:
        json.dump(analysis_results, json_file, indent=4)

    st.success("✅ Entity extraction completed!")

    # 📌 Display Extracted Entities
    st.subheader("📌 Extracted Entities")
    st.json(analysis_results)

    # 📌 Step 4: Chunking & Embedding
    st.write("🔹 Chunking text & generating embeddings with Nomic...")
    chunks = smart_chunk_text(cleaned_text)

    # Save chunks
    chunk_file = os.path.join(EXTRACTED_DIR, f"{pdf_filename}_chunks.json")
    save_chunks_to_json(chunks, chunk_file)

    # Save embeddings to FAISS
    index_file = os.path.join(EXTRACTED_DIR, f"{pdf_filename}_embeddings.index")
    save_to_faiss(chunks, index_path=index_file)

    st.success("✅ Chunking & Embeddings saved!")

    # 📌 Enable Q&A
    st.subheader("🧐 Ask Questions About the Document")
    user_query = st.text_input("Type your question:")

    if st.button("🔍 Search"):
        if user_query:
            results = search_faiss(user_query, k=5, index_path=index_file)

            # ✅ *Ensure Correct Formatting for Display*
            st.subheader("📌 Top Answers from Document")
            if isinstance(results, str):
                st.markdown(f"*Answer:* {results}")  # ✅ Ensure correct response format
            elif isinstance(results, list) and results:
                formatted_text = " ".join(results)  # ✅ Join text properly for readability
                st.markdown(f"*Answer:* {formatted_text}")
            else:
                st.warning("⚠️ No relevant answers found. Try another question.")
        else:
            st.warning("⚠️ Please enter a question.")
