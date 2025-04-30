import os
import json
import logging
import tkinter as tk
from tkinter import filedialog
from extract_text import extract_text_to_txt
from chunk_text import chunk_text_by_words
from process_urls import process_urls
from generate_embeddings import generate_embeddings
import boto3
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_investor_pitch():
    pitch = """
    AI-Powered Crypto Fund Risk Assessment
    Avoid crypto scams with AI precision! Our tool analyzes documents, web content, and real-time news to deliver actionable risk insights for investors. 
    Scalability: Deployable on AWS Lambda/Google Cloud Functions for massive datasets with distributed processing.
    Enhanced with SEC EDGAR checks, tokenomics simulation, and fund lifecycle modeling for U.S.-focused due diligence.
    """
    print(pitch)

def generate_summary_report(json_data, output_prefix, benchmarks=None):
    if not json_data:
        logging.warning("No data to generate summary report.")
        return
    summary = {
        "total_chunks": len(json_data),
        "average_risk_score": float(np.mean([entry["metadata"]["risk_score"]["scaled_score"] for entry in json_data])),
        "average_sentiment_score": float(np.mean([entry["metadata"]["sentiment_score"] for entry in json_data])),
        "high_risk_chunks": sum(1 for entry in json_data if entry["metadata"]["risk_score"]["scaled_score"] > 5),
        "key_entities": {
            "companies": list(set([ent for entry in json_data for ent in entry["metadata"]["entities"]["companies"]])),
            "persons": list(set([ent for entry in json_data for ent in entry["metadata"]["entities"]["persons"]]))
        },
        "avg_roi": float(np.mean([entry["metadata"]["fund_metrics"]["roi"] for entry in json_data])),
        "avg_liquidity_runway": float(np.mean([entry["metadata"]["fund_metrics"]["liquidity_runway"] for entry in json_data]))
    }
    if benchmarks:
        summary["benchmark_comparison"] = {
            "top_fund_risk": benchmarks.get("top_fund_risk", 3.0),
            "top_fund_roi": benchmarks.get("top_fund_roi", 8.0)
        }
    summary_file = f"{output_prefix}_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    logging.info(f"Summary report saved to: {summary_file}")

def process_file(file_path, output_dir):
    try:
        txt_file = extract_text_to_txt(file_path, output_dir)
        if not txt_file:
            return None, None, ["Text extraction failed."]
        with open(txt_file, "r", encoding="utf-8") as f:
            full_text = f.read()
        file_chunk_data, file_chunk_file = chunk_text_by_words(txt_file, output_dir)
        file_prefix = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(txt_file))[0]}_file")
        refined_data, eps, threshold = generate_embeddings(file_chunk_data, file_prefix, full_text)
        url_chunk_data, url_prefix, url_issues = process_urls(txt_file, output_dir)
        if url_chunk_data:
            url_refined_data, url_eps, url_threshold = generate_embeddings(url_chunk_data, url_prefix, full_text)
            refined_data.extend(url_refined_data)
        return refined_data, file_prefix, url_issues
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        return None, None, [f"Processing failed for {file_path}: {str(e)}"]

def main():
    root = tk.Tk()
    root.withdraw()
    output_dir = filedialog.askdirectory(title="Select Output Directory")
    if not output_dir:
        logging.error("No output directory selected. Exiting.")
        return
    os.makedirs(output_dir, exist_ok=True)
    print_investor_pitch()
    files = filedialog.askopenfilenames(
        title="Select JSON, PDF, TXT, DOCX, or HTML files",
        filetypes=[("JSON files", "*.json"), ("PDF files", "*.pdf"), ("Text files", "*.txt"), 
                   ("DOCX files", "*.docx"), ("HTML files", "*.html"), ("All files", "*.*")]
    )
    if not files:
        logging.error("No files selected. Exiting.")
        return
    issues = []
    all_refined_data = []
    benchmarks = {"top_fund_risk": 3.0, "top_fund_roi": 8.0}
    with ProcessPoolExecutor(max_workers=2) as executor:  # Reduced workers
        futures = [executor.submit(process_file, file_path, output_dir) for file_path in files]
        for future in futures:
            refined_data, prefix, file_issues = future.result()
            if refined_data:
                all_refined_data.extend(refined_data)
                generate_summary_report(refined_data, prefix, benchmarks)
            issues.extend(file_issues)
    if all_refined_data:
        high_risk = [entry for entry in all_refined_data if entry["metadata"]["risk_score"]["scaled_score"] > 7]
        if high_risk:
            logging.info("High-risk chunks detected. Review recommended:")
            for i, entry in enumerate(high_risk[:3], 1):
                logging.info(f"{i}. {entry['text'][:100]}... (Risk: {entry['metadata']['risk_score']['scaled_score']})")
    if issues:
        logging.info("\nIssues encountered:")
        for issue in issues:
            logging.info(f"- {issue}")
    else:
        logging.info("\nProcessing completed successfully.")

if __name__ == "__main__":
    main()