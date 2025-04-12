import fitz
import json

def convert_pdf_to_question_bank(pdf_path, json_path):
    doc = fitz.open(pdf_path)
    questions = []
    question_id = 1

    for page in doc:
        lines = page.get_text().splitlines()
        for line in lines:
            line = line.strip()
            if "?" in line and len(line) > 10:
                question_text = line.lstrip("-•0123456789. ").strip()
                questions.append({
                    "id": question_id,
                    "question": question_text,
                    "category": detect_question_category(question_text)
                })
                question_id += 1

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)

def detect_question_category(question):
    question = question.lower()
    if "compliance" in question or "regulation" in question:
        return "Regulatory"
    elif "fraud" in question or "risk" in question:
        return "Risk"
    elif "kyc" in question or "aml" in question:
        return "KYC/AML"
    return "General"
