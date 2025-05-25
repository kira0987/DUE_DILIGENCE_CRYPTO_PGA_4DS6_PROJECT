import os
import json

# Import custom modules
from modules.pdf_text_extractor import extract_text_from_pdf  # Extracts raw text
from modules.text_cleaning import clean_text  # Cleans extracted text
from modules.pdf_feature_extractor import extract_entities  # Extracts financial/legal entities
from modules.text_chunker import smart_chunk_text, save_chunks_to_json  # Chunking & embeddings
from modules.vector_database import save_to_faiss  # FAISS Vector Database Storage

# 📌 PDF Directory & Paths
PDF_DIR = "test_pdfs"
sample_pdf = os.path.join(PDF_DIR, "testpdf.pdf")

# Ensure "extracted" directory exists
output_dir = os.path.join(PDF_DIR, "extracted")
os.makedirs(output_dir, exist_ok=True)

# Get the PDF filename without the extension
pdf_filename = os.path.splitext(os.path.basename(sample_pdf))[0]

# 📌 Step 1: Extract Text from PDF
print(f"📄 Extracting text from {sample_pdf}...")
try:
    extracted_text = extract_text_from_pdf(sample_pdf)
    
    # Save raw extracted text
    output_text_file = os.path.join(output_dir, f"{pdf_filename}.txt")
    with open(output_text_file, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    
    print(f"✅ Extracted text saved to {output_text_file}")
except Exception as e:
    print(f"❌ Error extracting text: {e}")
    exit()

# 📌 Step 2: Clean Extracted Text
print("🧹 Cleaning extracted text...")
cleaned_text = clean_text(extracted_text)

# 📌 Step 3: Entity Extraction (Financial, Crypto & Legal Entities)
print("📊 Running entity analysis on extracted text...")
try:
    analysis_results = extract_entities(cleaned_text)
    
    # Save entity extraction results
    output_analysis_file = os.path.join(output_dir, f"{pdf_filename}_analysis.json")
    with open(output_analysis_file, "w", encoding="utf-8") as json_file:
        json.dump(analysis_results, json_file, indent=4)
    
    print(f"✅ Crypto & Risk Analysis saved to {output_analysis_file}")
except Exception as e:
    print(f"❌ Error analyzing text: {e}")

# 📌 Step 4: Smart Chunking & Embedding for RAG Processing
print("🔹 Chunking text & generating embeddings with Nomic...")
try:
    chunks = smart_chunk_text(cleaned_text)  # 🔥 Uses Nomic embeddings for chunking
    
    # Save chunked text
    output_chunk_file = os.path.join(output_dir, f"{pdf_filename}_chunks.json")
    save_chunks_to_json(chunks, output_chunk_file)
    
    # Save embeddings to FAISS Vector Database
    save_to_faiss(chunks)

    print(f"✅ Chunks & embeddings saved to {output_chunk_file}")
except Exception as e:
    print(f"❌ Error during chunking & embedding: {e}")

print("🎯 Processing completed successfully! Ready for RAG retrieval.")