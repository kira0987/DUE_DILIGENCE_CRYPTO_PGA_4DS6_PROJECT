import tkinter as tk
from tkinter import filedialog, messagebox
import json
from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

class RAGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SEC Filing RAG Query")
        self.data = None
        tk.Label(root, text="Select JSON File:").pack(pady=5)
        tk.Button(root, text="Browse", command=self.load_json).pack(pady=5)
        tk.Label(root, text="Enter Query:").pack(pady=5)
        self.query_entry = tk.Entry(root, width=50)
        self.query_entry.pack(pady=5)
        tk.Button(root, text="Search", command=self.search).pack(pady=5)
        self.result_text = tk.Text(root, height=20, width=80)
        self.result_text.pack(pady=10)

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            messagebox.showinfo("Success", f"Loaded {file_path}")

    def assess_scam_risk(self, top_chunk):
        crypto_count = top_chunk["total_crypto_mentions"]
        risk_score = top_chunk["risk_score"]
        sentiment = top_chunk["sentiment"]
        risk_mentions = len(top_chunk["risk_mentions"])
        currencies = len(top_chunk["currencies"])
        scam_score = 0
        reasoning = []
        if crypto_count > 10:
            scam_score += 3
            reasoning.append(f"High crypto mentions ({crypto_count}) suggest heavy crypto focus, potential red flag.")
        if risk_score > 7:
            scam_score += 3
            reasoning.append(f"High risk score ({risk_score:.2f}) indicates significant risk factors.")
        if sentiment == "negative":
            scam_score += 2
            reasoning.append("Negative sentiment may reflect operational or reputational issues.")
        if risk_mentions > 15:
            scam_score += 2
            reasoning.append(f"Many risk mentions ({risk_mentions}) could indicate instability.")
        if currencies > 5:
            scam_score += 1
            reasoning.append(f"Multiple currency mentions ({currencies}) might suggest speculative activity.")
        likelihood = "Low" if scam_score < 3 else "Moderate" if scam_score < 6 else "High"
        return scam_score, likelihood, reasoning

    def search(self):
        if not self.data:
            messagebox.showerror("Error", "Please load a JSON file first.")
            return
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showerror("Error", "Please enter a query.")
            return
        query_embedding = model.encode(query)
        scores = [util.cos_sim(query_embedding, chunk["embedding"]).item() for chunk in self.data]
        top_idx = np.argmax(scores)
        top_chunk = self.data[top_idx]
        scam_score, likelihood, reasoning = self.assess_scam_risk(top_chunk)
        result = f"Top Match (Score: {scores[top_idx]:.2f}):\n\n"
        result += f"Text: {top_chunk['text'][:500]}...\n\n"
        result += f"Risk Score: {top_chunk['risk_score']:.2f}\n"
        result += f"Sentiment: {top_chunk['sentiment']}\n"
        result += f"Crypto Terms: {top_chunk['crypto_terms']}\n"
        result += f"Total Crypto Mentions: {top_chunk['total_crypto_mentions']}\n"
        result += f"Currencies: {top_chunk['currencies']}\n"
        result += f"Risk Mentions: {top_chunk['risk_mentions'][:10]} (showing first 10)\n\n"
        result += f"Scam Risk Assessment:\n"
        result += f"Scam Score: {scam_score}/10\n"
        result += f"Likelihood of Scam: {likelihood}\n"
        result += "Reasoning:\n" + "\n".join([f"- {r}" for r in reasoning]) if reasoning else "Reasoning: No significant red flags detected."
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)

if __name__ == "__main__":
    root = tk.Tk()
    app = RAGApp(root)
    root.mainloop()