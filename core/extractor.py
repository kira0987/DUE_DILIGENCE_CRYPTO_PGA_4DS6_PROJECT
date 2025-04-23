import os
import fitz  # PyMuPDF
import easyocr
from docx import Document

def extract_text(filepath: str) -> str:
    """
    Extracts text from a file, depending on its type (PDF, image, DOCX, or TXT).

    Args:
        filepath (str): Path to the input file.

    Returns:
        str: Extracted text content.
    """
    ext = os.path.splitext(filepath)[-1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(filepath)

    elif ext in [".jpg", ".jpeg", ".png"]:
        return extract_text_from_image(filepath)

    elif ext == ".docx":
        return extract_text_from_docx(filepath)

    elif ext == ".txt":
        return extract_text_from_txt(filepath)

    else:
        raise ValueError(f"❌ Unsupported file type: {ext}")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts full text from a PDF using PyMuPDF (fitz).
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"❌ File does not exist: {pdf_path}")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"❌ Unable to open PDF: {e}")

    if doc.page_count == 0:
        raise ValueError("⚠️ PDF is empty or corrupted")

    full_text = []
    for page_num in range(len(doc)):
        try:
            page = doc[page_num]
            text = page.get_text("text") or ""
            full_text.append(f"\n--- Page {page_num + 1} ---\n{text.strip()}")
        except Exception as e:
            print(f"⚠️ Could not read page {page_num + 1}: {e}")

    doc.close()
    extracted = "\n".join(full_text).strip()

    if not extracted:
        raise ValueError("⚠️ No text could be extracted from the PDF")

    print(f"✅ Extracted {len(full_text)} pages from '{os.path.basename(pdf_path)}'")
    return extracted

def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from an image using OCR (EasyOCR).
    """
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        result = reader.readtext(image_path, detail=0)
        return "\n".join(result).strip()
    except Exception as e:
        raise RuntimeError(f"❌ OCR failed: {e}")

def extract_text_from_docx(docx_path: str) -> str:
    """
    Extracts text from a Word (.docx) document.
    """
    try:
        doc = Document(docx_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        raise RuntimeError(f"❌ Failed to read DOCX file: {e}")

def extract_text_from_txt(txt_path: str) -> str:
    """
    Reads a plain .txt file.
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"❌ Failed to read TXT file: {e}")

def save_text_to_file(text: str, output_path: str):
    """
    Saves extracted text to a file.
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Extracted text saved to '{output_path}'")
    except Exception as e:
        raise IOError(f"❌ Failed to save extracted text: {e}")
