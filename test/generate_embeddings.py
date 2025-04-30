import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
import logging
from utils import optimize_thresholds
import plotly.express as px

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
model = SentenceTransformer('all-distilroberta-v1')

def generate_risk_heatmap(json_data, output_prefix):
    risk_scores = [entry["metadata"]["risk_score"]["scaled_score"] for entry in json_data]
    sentiment_scores = [entry["metadata"]["sentiment_score"] for entry in json_data]
    fig = px.imshow([risk_scores, sentiment_scores], 
                    labels=dict(x="Chunk Index", y="Metric", color="Score"),
                    y=["Risk", "Sentiment"], 
                    color_continuous_scale="YlOrRd",
                    title="Risk vs Sentiment Heatmap")
    fig.write_html(f"{output_prefix}_risk_heatmap.html")
    logging.info(f"Interactive heatmap saved to: {output_prefix}_risk_heatmap.html")

def generate_case_studies(json_data, output_prefix):
    high_risk = [entry for entry in json_data if entry["metadata"]["risk_score"]["scaled_score"] > 5]
    with open(f"{output_prefix}_case_studies.txt", "w", encoding="utf-8") as f:
        for i, entry in enumerate(high_risk, 1):
            f.write(f"Case Study {i}:\n")
            f.write(f"Source: {entry['metadata']['source']}\n")
            f.write(f"Text: {entry['text'][:500]}...\n")
            f.write(f"Risk Score: {entry['metadata']['risk_score']['scaled_score']}\n")
            f.write(f"Categories: {', '.join(k for k, v in entry['metadata']['categories'].items() if v)}\n")
            f.write(f"Entities: {entry['metadata']['entities']}\n\n")
    logging.info(f"Case studies saved to: {output_prefix}_case_studies.txt")

def post_process_embeddings(json_data, eps=5.0, threshold=0.50):
    embeddings = np.array([entry["embedding"] for entry in json_data])
    eps, threshold = optimize_thresholds(embeddings, eps, threshold)
    
    dbscan = DBSCAN(eps=eps, min_samples=2)
    labels = dbscan.fit_predict(embeddings)
    logging.info(f"DBSCAN labels: {np.unique(labels, return_counts=True)}")
    
    filtered_data = [json_data[i] for i, label in enumerate(labels) if label != -1]
    if not filtered_data:
        logging.warning("DBSCAN found no clusters; using all data")
        filtered_data = json_data
    
    refined_data = [entry for entry in filtered_data if 
                    entry["metadata"]["risk_score"]["scaled_score"] >= 0 or 
                    any(entry["metadata"]["categories"].values())]
    
    logging.info(f"Reduced from {len(json_data)} to {len(refined_data)} entries.")
    return refined_data, eps, threshold

def simulate_fund_metrics(text):
    text_lower = text.lower()
    roi = 5.0
    if "high return" in text_lower or "yield" in text_lower:
        roi += 2.0
    if "risk" in text_lower:
        roi -= 1.5
    stage = "Seed" if "early stage" in text_lower else "Series A" if "growth" in text_lower else "Mature"
    liquidity_runway = 12
    if "liquidity" in text_lower and "low" in text_lower:
        liquidity_runway -= 6
    return {"roi": roi, "stage": stage, "liquidity_runway": liquidity_runway}

def generate_embeddings(chunk_data, output_prefix, full_text=None):
    if not chunk_data:
        logging.warning(f"No chunks to embed for {output_prefix}")
        return
    
    logging.info(f"Generating embeddings for {len(chunk_data)} chunks")
    all_chunks = [entry["text"] for entry in chunk_data]
    embeddings = model.encode(all_chunks, show_progress_bar=True, batch_size=32)
    
    doc_embedding = model.encode(full_text) if full_text else None
    
    clf = IsolationForest(contamination=0.1, random_state=42)
    preds = clf.fit_predict(embeddings)
    anomalies = [i for i, pred in enumerate(preds) if pred == -1]
    logging.info(f"Detected {len(anomalies)} anomalies in embeddings.")
    
    raw_json_data = []
    for i, (c, m, e) in enumerate(zip(all_chunks, [entry["metadata"] for entry in chunk_data], embeddings)):
        fund_metrics = simulate_fund_metrics(c)
        entry = {
            "text": c,
            "metadata": {**m, "fund_metrics": fund_metrics},
            "embedding": e.tolist(),
            "anomaly": i in anomalies
        }
        raw_json_data.append(entry)
    
    raw_output_json = f"{output_prefix}_raw_embedded.json"
    with open(raw_output_json, "w", encoding="utf-8") as f:
        json.dump(raw_json_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Raw embeddings saved to: {raw_output_json}")
    
    refined_json_data, eps, threshold = post_process_embeddings(raw_json_data)
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
        
        if doc_embedding is not None:
            with open(f"{output_prefix}_doc_embedding.json", "w") as f:
                json.dump({"doc_embedding": doc_embedding.tolist()}, f)
            logging.info(f"Document-level embedding saved to: {output_prefix}_doc_embedding.json")
        
        generate_risk_heatmap(refined_json_data, output_prefix)
        generate_case_studies(refined_json_data, output_prefix)
    
    print(f"Raw: {raw_output_json} ({len(raw_json_data)} chunks)")
    print(f"Refined: {refined_output_json} ({len(refined_json_data)} chunks)")
    return refined_json_data, eps, threshold