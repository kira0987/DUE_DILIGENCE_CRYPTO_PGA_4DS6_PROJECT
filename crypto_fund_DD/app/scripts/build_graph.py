# scripts/build_graph.py

import os
import glob
import pickle
import networkx as nx
import spacy
from tqdm import tqdm

# --- Settings ---
CHUNK_DIR = "data/chunks/"      # Where your text chunks are stored
GRAPH_PATH = "data/graph.pkl"   # Where the graph will be saved

# --- Build Graph Function ---
def build_graph():
    print("🔄 Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")  # Small and fast English model
    print("✅ spaCy model loaded.")

    # --- Load Chunks ---
    chunk_files = sorted(glob.glob(os.path.join(CHUNK_DIR, "*.txt")))

    if not chunk_files:
        raise RuntimeError("❌ No chunks found in 'data/chunks/'. Please make sure your document is processed and chunked first!")

    print(f"📝 Found {len(chunk_files)} chunks to build the graph.")

    G = nx.Graph()  # Initialize empty graph
    concept_index = {}  # Mapping: concept -> list of chunk IDs

    # --- Helper to Extract Key Concepts ---
    def extract_key_concepts(text):
        """Extract named entities and noun chunks from text."""
        doc = nlp(text)
        entities = [ent.text.strip().lower() for ent in doc.ents if len(ent.text) > 2]
        noun_chunks = [chunk.text.strip().lower() for chunk in doc.noun_chunks if len(chunk.text) > 2]
        return list(set(entities + noun_chunks))

    # --- Step 1: Create Nodes ---
    for file in tqdm(chunk_files, desc="🔎 Extracting concepts from chunks"):
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        chunk_id = os.path.basename(file)
        concepts = extract_key_concepts(text)

        if not concepts:
            continue  # Skip empty

        # Add chunk node with attributes
        G.add_node(chunk_id, text=text, concepts=concepts)

        # Build concept index
        for concept in concepts:
            if concept not in concept_index:
                concept_index[concept] = []
            concept_index[concept].append(chunk_id)

    print(f"✅ Created {G.number_of_nodes()} nodes.")

    # --- Step 2: Create Edges ---
    for concept, related_chunks in tqdm(concept_index.items(), desc="🔗 Building edges"):
        for i in range(len(related_chunks)):
            for j in range(i + 1, len(related_chunks)):
                G.add_edge(related_chunks[i], related_chunks[j])

    print(f"✅ Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    # --- Save Graph ---
    os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)
    with open(GRAPH_PATH, "wb") as f:
        pickle.dump(G, f)

    print(f"✅ Graph saved to {GRAPH_PATH}")
    print("🏁 Graph building complete!")

# --- Entry Point ---
def main():
    build_graph()

if __name__ == "__main__":
    main()
