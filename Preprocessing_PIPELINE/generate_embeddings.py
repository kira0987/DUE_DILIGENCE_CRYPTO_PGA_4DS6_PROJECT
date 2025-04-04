import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import logging
import matplotlib.pyplot as plt
import seaborn as sns

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the model
model = SentenceTransformer('all-distilroberta-v1')

def generate_risk_heatmap(json_data, output_prefix):
    """Generate a risk vs sentiment heatmap."""
    risk_scores = [entry["metadata"]["risk_score"] for entry in json_data]
    sentiment_scores = [entry["metadata"]["sentiment_value"] for entry in json_data]  # Updated from "sentiment_score"
    plt.figure(figsize=(8, 6))
    sns.heatmap(np.array([risk_scores, sentiment_scores]), annot=True, cmap="YlOrRd",
                xticklabels=False, yticklabels=["Risk", "Sentiment"])
    plt.title("Risk vs Sentiment Heatmap")
    plt.savefig(f"{output_prefix}_risk_heatmap.png")
    plt.close()
    logging.info(f"Risk heatmap saved to: {output_prefix}_risk_heatmap.png")

    
def generate_case_studies(json_data, output_prefix):
    """Generate case studies for high-risk chunks."""
    high_risk = [entry for entry in json_data if entry["metadata"]["risk_score"] > 5]
    with open(f"{output_prefix}_case_studies.txt", "w", encoding="utf-8") as f:
        for i, entry in enumerate(high_risk[:3], 1):
            f.write(f"Case Study {i}:\n")
            f.write(f"Source: {entry['metadata']['source']}\n")
            f.write(f"Text: {entry['text'][:200]}...\n")
            f.write(f"Risk Score: {entry['metadata']['risk_score']}\n")
            f.write(f"Reason: High risk terms - {', '.join(entry['metadata']['entities']['risk_mentions'][:3])}\n\n")
    logging.info(f"Case studies saved to: {output_prefix}_case_studies.txt")

def post_process_embeddings(json_data, eps=5.0, min_samples=2):
    """Post-process embeddings with clustering and relaxed filtering."""
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
    
    logging.info(f"Post-clustering: {len(filtered_data)} entries remain")
    
    for i, entry in enumerate(filtered_data[:5], 1):
        logging.info(f"Sample {i}: risk_score={entry['metadata']['risk_score']}, "
                     f"sentiment_score={entry['metadata']['sentiment_score']}, "
                     f"categories={entry['metadata']['categories']}")
    
    refined_data = [entry for entry in filtered_data if
                    entry["metadata"]["risk_score"] >= 0 or
                    entry["metadata"]["sentiment_score"] < 0.75 or
                    any(cat for cat in entry["metadata"]["categories"].values() if cat)]
    
    logging.info(f"Reduced from {len(json_data)} to {len(refined_data)} entries.")
    return refined_data

def generate_embeddings(chunk_data, output_prefix):
    """Generate embeddings and save raw/refined outputs."""
    if not chunk_data:
        logging.warning(f"No chunks to embed for {output_prefix}")
        return
    
    logging.info(f"Generating embeddings for {len(chunk_data)} chunks")
    all_chunks = [entry["text"] for entry in chunk_data]
    all_metadata = [entry["metadata"] for entry in chunk_data]
    
    embeddings = model.encode(all_chunks, show_progress_bar=True, batch_size=32)
    
    raw_json_data = [{"text": c, "metadata": m, "embedding": e.tolist()}
                     for c, m, e in zip(all_chunks, all_metadata, embeddings)]
    
    raw_output_json = f"{output_prefix}_raw_embedded.json"
    with open(raw_output_json, "w", encoding="utf-8") as f:
        json.dump(raw_json_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Raw embeddings saved to: {raw_output_json}")
    
    refined_json_data = post_process_embeddings(raw_json_data, eps=5.0, min_samples=2)
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
    else:
        logging.warning("Refined data is empty; no FAISS index or visualizations generated.")
    
    print(f"Raw: {raw_output_json} ({len(raw_json_data)} chunks)")
    print(f"Refined: {refined_output_json} ({len(refined_json_data)} chunks)")