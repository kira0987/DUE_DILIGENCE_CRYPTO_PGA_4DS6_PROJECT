from core.extractor import extract_text_from_pdf, save_text_to_file
from core.cleaner import clean_text_and_detect_sections
from core.chunker import chunk_and_embed
from core.indexer import save_faiss_index
from core.matcher import match_questions_with_rag
from core.responder import generate_answers_rag
from core.exporter import export_to_pptx

INPUT_PDF = "data/PIF.pdf"
TEXT_OUTPUT = "data/PIF_extracted.txt"
CLEANED_OUTPUT = "data/PIF_cleaned.txt"
INDEX_OUTPUT = "embeddings/PIF.index"
QUESTION_FILE = "questions/questions.json"
ANSWER_OUTPUT = "answers/PIF_answers.json"
PPTX_OUTPUT = "answers/PIF_report.pptx"

if __name__ == "__main__":
    print("📄 Étape 1 : Extraction PDF")
    text = extract_text_from_pdf(INPUT_PDF)
    save_text_to_file(text, TEXT_OUTPUT)

    print("🧹 Étape 2 : Nettoyage + structuration")
    cleaned_text, sections = clean_text_and_detect_sections(text)
    save_text_to_file(cleaned_text, CLEANED_OUTPUT)

    print("✂️ Étape 3 : Chunking + Embeddings")
    chunks, index = chunk_and_embed(cleaned_text, sections)
    save_faiss_index(index, INDEX_OUTPUT)

    print("🔍 Étape 4 : Matching avec RAG")
    matched = match_questions_with_rag(QUESTION_FILE, index, chunks)

    print("🤖 Étape 5 : Génération de réponses")
    answers = generate_answers_rag(matched)
    
    print("💾 Étape 6 : Sauvegarde JSON + Rapport")
    with open(ANSWER_OUTPUT, "w", encoding="utf-8") as f:
        import json
        json.dump(answers, f, indent=4, ensure_ascii=False)

    export_to_pptx(answers, PPTX_OUTPUT)

    print("✅ Pipeline terminé avec succès.")
