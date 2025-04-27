# scripts/visualize_graph.py
import pickle
import networkx as nx
from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components

GRAPH_PATH = "data/graph.pkl"

def visualize_graph():
    if not GRAPH_PATH or not GRAPH_PATH.endswith('.pkl'):
        st.error("⚠️ Invalid graph path.")
        return

    try:
        with open(GRAPH_PATH, "rb") as f:
            G = pickle.load(f)
    except Exception as e:
        st.error(f"❌ Failed to load graph: {e}")
        return

    if G.number_of_nodes() == 0:
        st.warning("⚠️ Graph is empty. Nothing to visualize.")
        return
    
    st.success(f"✅ Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    # Create a pyvis Network
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", notebook=False)

    # Set better physics layout
    net.barnes_hut()

    # Add nodes and edges
    for node, data in G.nodes(data=True):
        label = node  # You can customize label here if needed
        title = "<br>".join(data.get("concepts", [])) if "concepts" in data else node
        net.add_node(node, label=label, title=title)

    for source, target in G.edges():
        net.add_edge(source, target)

    # Save the graph to a temporary HTML file
    path = "data/graph.html"
    net.write_html(path)


    # Display the HTML inside Streamlit
    HtmlFile = open(path, 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height=800, width=1000)
