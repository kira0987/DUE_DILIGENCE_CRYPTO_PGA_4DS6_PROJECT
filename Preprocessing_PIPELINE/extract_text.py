import json
import os
import fitz
import pytesseract
from pdf2image import convert_from_path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_to_txt(file_path, output_dir):
    """Extract text from JSON, PDF, or TXT files."""
    try:
        if file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            text = " ".join(str(value) for value in data.values() if isinstance(value, str))
        elif file_path.endswith(".pdf"):
            with fitz.open(file_path) as doc:
                text = "".join(page.get_text() for page in doc)
            if len(text.strip()) < 10:
                logging.info("PyMuPDF extracted insufficient text. Falling back to Tesseract OCR.")
                images = convert_from_path(file_path, threads=4)
                text = "\n".join(pytesseract.image_to_string(img) for img in images)
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError("Unsupported file type. Use JSON, PDF, or TXT.")
        
        output_txt = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(file_path))[0]}_extracted.txt")
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(text)
        logging.info(f"Text extracted to: {output_txt}")
        return output_txt
    except Exception as e:
        logging.error(f"Failed to extract text from {file_path}: {str(e)}")
        raise