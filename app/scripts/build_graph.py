import os
import glob
import networkx as nx
import spacy
import pickle
from tqdm import tqdm

# --- Settings ---
CHUNK_DIR = "data/chunks/"
GRAPH_PATH = "data/graph.pkl"

# Load Spacy NLP model
nlp = spacy.load("en_core_web_sm")

def extract_key_concepts(text):
    """Extract entities and noun chunks from text."""
    doc = nlp(text)
    entities = [ent.text.strip().lower() for ent in doc.ents if len(ent.text) > 2]
    noun_chunks = [chunk.text.strip().lower() for chunk in doc.noun_chunks if len(chunk.text) > 2]
    return list(set(entities + noun_chunks))

def main():
    # --- Load Existing Graph if Available ---
    if os.path.exists(GRAPH_PATH):
        print("🔄 Loading existing graph...")
        with open(GRAPH_PATH, "rb") as f:
            G = pickle.load(f)
    else:
        print("🆕 No previous graph found. Starting fresh.")
        G = nx.Graph()

    # --- Load Chunks from CHUNK_DIR directly ---
    chunk_files = sorted(glob.glob(os.path.join(CHUNK_DIR, "*.txt")))

    if not chunk_files:
        print("🚫 No chunks found. Saving empty graph.")
        os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)
        with open(GRAPH_PATH, "wb") as f:
            pickle.dump(G, f)
        return

    print(f"🔎 Found {len(chunk_files)} chunks to add to the graph.")

    existing_nodes = set(G.nodes())
    concept_index = {}

    # --- Add Only New Nodes ---
    for file in tqdm(chunk_files, desc="🔎 Processing chunks"):
        chunk_id = os.path.basename(file)

        if chunk_id in existing_nodes:
            continue  # Skip already existing nodes

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        concepts = extract_key_concepts(text)

        if not concepts:
            continue

        G.add_node(chunk_id, text=text, concepts=concepts)

        for concept in concepts:
            if concept not in concept_index:
                concept_index[concept] = []
            concept_index[concept].append(chunk_id)

    # --- Add Only New Edges ---
    for concept, related_chunks in tqdm(concept_index.items(), desc="🔗 Building new edges"):
        for i in range(len(related_chunks)):
            for j in range(i + 1, len(related_chunks)):
                if not G.has_edge(related_chunks[i], related_chunks[j]):
                    G.add_edge(related_chunks[i], related_chunks[j])

    print(f"✅ Graph now has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    # --- Save Updated Graph ---
    os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)
    with open(GRAPH_PATH, "wb") as f:
        pickle.dump(G, f)

    print(f"✅ Graph updated and saved to {GRAPH_PATH}")
    print("🏁 Graph update complete!")

# --- Main Entry ---
if __name__ == "__main__":
    main()
