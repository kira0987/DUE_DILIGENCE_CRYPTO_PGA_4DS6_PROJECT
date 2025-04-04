import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.ensemble import IsolationForest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Placeholder for a crypto-specific fine-tuned model
model = SentenceTransformer('all-distilroberta-v1')  # Replace with fine-tuned model later

def generate_risk_heatmap(json_data, output_prefix):
    """Generate an interactive risk vs sentiment heatmap."""
    risk_scores = [entry["metadata"]["risk_score"] for entry in json_data]
    sentiment_scores = [entry["metadata"]["sentiment_score"] for entry in json_data]
    fig = px.imshow([risk_scores, sentiment_scores], 
                    labels=dict(x="Chunk Index", y="Metric", color="Score"),
                    y=["Risk", "Sentiment"], 
                    color_continuous_scale="YlOrRd",
                    title="Risk vs Sentiment Heatmap")
    fig.write_html(f"{output_prefix}_risk_heatmap.html")
    logging.info(f"Interactive heatmap saved to: {output_prefix}_risk_heatmap.html")

def generate_case_studies(json_data, output_prefix):
    """Generate detailed case studies for all high-risk chunks."""
    high_risk = [entry for entry in json_data if entry["metadata"]["risk_score"] > 5]
    with open(f"{output_prefix}_case_studies.txt", "w", encoding="utf-8") as f:
        for i, entry in enumerate(high_risk, 1):
            f.write(f"Case Study {i}:\n")
            f.write(f"Source: {entry['metadata']['source']}\n")
            f.write(f"Text: {entry['text'][:500]}...\n")
            f.write(f"Risk Score: {entry['metadata']['risk_score']}\n")
            f.write(f"Categories: {', '.join(k for k, v in entry['metadata']['categories'].items() if v)}\n")
            f.write(f"Entities: {entry['metadata']['entities']}\n\n")
    logging.info(f"Case studies saved to: {output_prefix}_case_studies.txt")

def post_process_embeddings(json_data, eps=5.0, min_samples=2):
    """Refine embeddings with clustering and relaxed filtering."""
    embeddings = np.array([entry["embedding"] for entry in json_data])
    
    scaler = StandardScaler()
    scaled_embeddings = scaler.fit_transform(embeddings)
    
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(scaled_embeddings)
    logging.info(f"DBSCAN labels: {np.unique(labels, return_counts=True)}")
    
    filtered_data = [json_data[i] for i, label in enumerate(labels) if label != -1]
    if not filtered_data:
        logging.warning("DBSCAN found no clusters; using all data")
        filtered_data = json_data
    
    # Relaxed filtering to retain critical info
    refined_data = [entry for entry in filtered_data if 
                    entry["metadata"]["risk_score"] >= 0 or 
                    any(entry["metadata"]["categories"].values())]
    
    logging.info(f"Reduced from {len(json_data)} to {len(refined_data)} entries.")
    return refined_data

def generate_embeddings(chunk_data, output_prefix):
    """Generate and save embeddings with anomaly detection."""
    if not chunk_data:
        logging.warning(f"No chunks to embed for {output_prefix}")
        return
    
    logging.info(f"Generating embeddings for {len(chunk_data)} chunks")
    all_chunks = [entry["text"] for entry in chunk_data]
    embeddings = model.encode(all_chunks, show_progress_bar=True, batch_size=32)
    
    # Detect anomalies in embeddings
    clf = IsolationForest(contamination=0.1, random_state=42)
    preds = clf.fit_predict(embeddings)
    anomalies = [i for i, pred in enumerate(preds) if pred == -1]
    logging.info(f"Detected {len(anomalies)} anomalies in embeddings.")
    
    raw_json_data = []
    for i, (c, m, e) in enumerate(zip(all_chunks, [entry["metadata"] for entry in chunk_data], embeddings)):
        entry = {
            "text": c,
            "metadata": m,
            "embedding": e.tolist(),
            "anomaly": i in anomalies  # Flag anomalies
        }
        raw_json_data.append(entry)
    
    raw_output_json = f"{output_prefix}_raw_embedded.json"
    with open(raw_output_json, "w", encoding="utf-8") as f:
        json.dump(raw_json_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Raw embeddings saved to: {raw_output_json}")
    
    refined_json_data = post_process_embeddings(raw_json_data)
    refined_output_json = f"{output_prefix}_refined_embedded.json"
    with open(refined_output_json, "w", encoding="utf-8") as f:
        json.dump(refined_json_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Refined embeddings saved to: {refined_output_json}")
    
    if refined_json_data:
        refined_embeddings = np.array([entry["embedding"] for entry in refined_json_data])
        index = faiss.IndexFlatL2(refined_embeddings.shape[1])
        index.add(refined_embeddings)
        faiss.write_index(index, f"{output_prefix}_faiss_index.bin")
        logging.info(f"FAISS index saved to: {output_prefix}_faiss_index.bin")
        
        generate_risk_heatmap(refined_json_data, output_prefix)
        generate_case_studies(refined_json_data, output_prefix)
    
    print(f"Raw: {raw_output_json} ({len(raw_json_data)} chunks)")
    print(f"Refined: {refined_output_json} ({len(refined_json_data)} chunks)")