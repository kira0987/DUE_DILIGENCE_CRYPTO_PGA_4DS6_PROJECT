import os
import json
import logging
import tkinter as tk
from tkinter import filedialog
from extract_text import extract_text_to_txt
from chunk_text import chunk_text_by_words
from process_urls import process_urls
from generate_embeddings import generate_embeddings
import boto3  # For potential AWS Lambda integration
import numpy as np  # Added for summary report statistics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_investor_pitch():
    pitch = """
    AI-Powered Crypto Fund Risk Assessment
    Avoid crypto scams with AI precision! Our tool analyzes documents and web content to deliver actionable risk insights for investors. 
    Scalability: Deployable on AWS Lambda/Google Cloud Functions for massive datasets with distributed processing.
    """
    print(pitch)

def generate_summary_report(json_data, output_prefix):
    """Generate a simplified summary report for investors."""
    if not json_data:
        logging.warning("No data to generate summary report.")
        return
    
    summary = {
        "total_chunks": len(json_data),
        "average_risk_score": float(np.mean([entry["metadata"]["risk_score"] for entry in json_data])),  # Convert to float for JSON serialization
        "average_sentiment_score": float(np.mean([entry["metadata"]["sentiment_score"] for entry in json_data])),  # Convert to float for JSON serialization
        "high_risk_chunks": sum(1 for entry in json_data if entry["metadata"]["risk_score"] > 5),
        "key_entities": {
            "companies": list(set([ent for entry in json_data for ent in entry["metadata"]["entities"]["companies"]])),
            "persons": list(set([ent for entry in json_data for ent in entry["metadata"]["entities"]["persons"]]))
        }
    }
    summary_file = f"{output_prefix}_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    logging.info(f"Summary report saved to: {summary_file}")

def main():
    root = tk.Tk()
    root.withdraw()
    
    output_dir = filedialog.askdirectory(title="Select Output Directory")
    if not output_dir:
        logging.error("No output directory selected. Exiting.")
        return
    os.makedirs(output_dir, exist_ok=True)
    
    print_investor_pitch()
    
    file_path = filedialog.askopenfilename(
        title="Select a JSON, PDF, TXT, DOCX, or HTML file",
        filetypes=[("JSON files", "*.json"), ("PDF files", "*.pdf"), ("Text files", "*.txt"), 
                   ("DOCX files", "*.docx"), ("HTML files", "*.html"), ("All files", "*.*")]
    )
    if not file_path:
        logging.error("No file selected. Exiting.")
        return
    
    issues = []
    
    # Text Extraction
    try:
        txt_file = extract_text_to_txt(file_path, output_dir)
        if not txt_file:
            issues.append("Text extraction failed.")
    except Exception as e:
        issues.append(f"Error extracting text: {str(e)}")
    
    # File Chunking and Embeddings
    try:
        file_chunk_data, file_chunk_file = chunk_text_by_words(txt_file, output_dir)
        file_prefix = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(txt_file))[0]}_file")
        generate_embeddings(file_chunk_data, file_prefix)
        generate_summary_report(file_chunk_data, file_prefix)  # Added call to generate summary report for file data
    except Exception as e:
        issues.append(f"Error processing file chunks: {str(e)}")
    
    # URL Processing and Embeddings
    try:
        url_chunk_data, url_prefix, url_issues = process_urls(txt_file, output_dir)
        issues.extend(url_issues)
        if url_chunk_data:
            generate_embeddings(url_chunk_data, url_prefix)
            generate_summary_report(url_chunk_data, url_prefix)  # Added call to generate summary report for URL data
    except Exception as e:
        issues.append(f"Error processing URLs: {str(e)}")
    
    # Report Issues
    if issues:
        logging.info("\nIssues encountered:")
        for issue in issues:
            logging.info(f"- {issue}")
    else:
        logging.info("\nProcessing completed successfully.")

if __name__ == "__main__":
    main()