import os
import json
import fitz
import pytesseract
from pdf2image import convert_from_path
import docx
from bs4 import BeautifulSoup
import requests
import logging
import boto3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

textract_client = boto3.client('textract', region_name='us-east-1')

def extract_text_from_pdf_with_textract(file_path):
    try:
        with open(file_path, 'rb') as pdf_file:
            response = textract_client.detect_document_text(Document={'Bytes': pdf_file.read()})
        text = "\n".join([item["Text"] for item in response["Blocks"] if item["BlockType"] == "LINE"])
        return text
    except Exception as e:
        logging.error(f"AWS Textract failed for {file_path}: {str(e)}")
        return ""

def extract_text_to_txt(file_path, output_dir):
    try:
        if file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            text = " ".join(str(value) for value in data.values() if isinstance(value, str))
        elif file_path.endswith(".pdf"):
            with fitz.open(file_path) as doc:
                text = "".join(page.get_text() for page in doc)
            if len(text.strip()) < 10:
                logging.info("PyMuPDF extracted insufficient text. Using AWS Textract.")
                text = extract_text_from_pdf_with_textract(file_path)
            if len(text.strip()) < 10:
                logging.info("Textract insufficient. Converting PDF to images for OCR.")
                images = convert_from_path(file_path)
                text = "\n".join(pytesseract.image_to_string(img) for img in images)
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file_path.endswith(".html"):
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, 'html.parser')
                text = soup.get_text(separator=' ')
        else:
            raise ValueError("Unsupported file type. Use JSON, PDF, TXT, DOCX, or HTML.")
        
        output_txt = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(file_path))[0]}_extracted.txt")
        os.makedirs(output_dir, exist_ok=True)
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(text)
        logging.info(f"Text extracted to: {output_txt}")
        return output_txt
    except Exception as e:
        logging.error(f"Failed to extract text from {file_path}: {str(e)}")
        raise