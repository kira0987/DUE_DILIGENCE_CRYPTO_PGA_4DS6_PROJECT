import sys
import os

# 🔧 Ajouter le chemin parent au sys.path pour accéder à core/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from core.extractor import extract_text
from core.cleaner import clean_text_and_detect_sections
from core.chunker import chunk_sections, embed_chunks
from core.indexer import enrich_chunks
from core.matcher import load_questions, match_question_to_chunks
from core.responder import generate_answer
from core.ppt_generator import generate_ppt

st.set_page_config(page_title="🧠 Crypto Due Diligence", layout="wide")

st.title("📊 Crypto Due Diligence Assistant")
st.markdown("Téléversez un white paper pour générer des réponses aux questions de due diligence.")

# Téléversement du PDF
uploaded_file = st.file_uploader("📎 Choisissez un fichier PDF", type="pdf")

if uploaded_file is not None:
    pdf_path = f"data/{uploaded_file.name}"
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ Fichier enregistré : {uploaded_file.name}")

    # Extraction du texte
    st.info("🔍 Extraction du texte...")
    raw_text = extract_text(pdf_path)

    # Nettoyage et détection des sections
    cleaned_text, sections = clean_text_and_detect_sections(raw_text)
    st.success(f"✅ {len(sections)} sections détectées.")

    # Chunking et embeddings
    st.info("🧩 Découpage et embeddings...")
    base_chunks = chunk_sections(sections)
    enriched_chunks = enrich_chunks(base_chunks)
    embeddings = embed_chunks(enriched_chunks)
    st.success(f"✅ {len(enriched_chunks)} chunks enrichis.")

    # Chargement de la banque de questions
    questions_path = "questions/questions.json"
    questions = load_questions(questions_path)

    # Génération des réponses
    st.info("🧠 Génération des réponses...")
    answers = {}
    for q in questions:
        top_chunks = match_question_to_chunks(q["question"], enriched_chunks, embeddings)
        answer = generate_answer(q["question"], top_chunks)
        answers[q["id"]] = {"question": q["question"], "answer": answer}

    st.success("✅ Réponses générées !")

    # Affichage des réponses
    st.subheader("📝 Réponses aux questions")
    for q_id, content in answers.items():
        st.markdown(f"**Q{q_id}**: {content['question']}")
        st.markdown(content["answer"])
        st.markdown("---")

    # Bouton pour générer le PPT
    if st.button("📤 Générer PowerPoint"):
        ppt_path = f"answers/{uploaded_file.name.replace('.pdf', '_report.pptx')}"
        generate_ppt(answers, ppt_path)
        with open(ppt_path, "rb") as f:
            st.download_button("📥 Télécharger le rapport PowerPoint", f, file_name=os.path.basename(ppt_path))
