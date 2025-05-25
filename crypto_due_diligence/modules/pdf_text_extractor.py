import fitz  # PyMuPDF for digital PDFs
import pytesseract  # OCR for scanned PDFs
from pdf2image import convert_from_path  # Convert scanned PDFs to images
import os

# Set Tesseract OCR path (Windows users may need to change this)
# Uncomment & modify the below line if Tesseract isn't detected automatically
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_digital_pdf(pdf_path):
    """
    Extracts text from a digital (non-scanned) PDF using PyMuPDF.
    :param pdf_path: Path to the PDF file
    :return: Extracted text as a string
    """
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text("text") + "\n"

    return text.strip()


def extract_text_from_scanned_pdf(pdf_path):
    """
    Extracts text from a scanned PDF using OCR (Tesseract).
    :param pdf_path: Path to the PDF file
    :return: Extracted text as a string
    """
    images = convert_from_path(pdf_path)
    extracted_text = ""

    for image in images:
        extracted_text += pytesseract.image_to_string(image) + "\n"

    return extracted_text.strip()


def extract_text_from_pdf(pdf_path):
    """
    Determines whether a PDF is digital or scanned, then extracts text accordingly.
    :param pdf_path: Path to the PDF file
    :return: Extracted text as a string
    """
    text = extract_text_from_digital_pdf(pdf_path)

    # If the extracted text is mostly empty, assume it's a scanned PDF
    if len(text.strip()) < 50:  # Threshold to detect scanned PDFs
        print(f"📄 {pdf_path} seems scanned, using OCR...")
        text = extract_text_from_scanned_pdf(pdf_path)
    else:
        print(f"📄 {pdf_path} is digital, extracting text directly...")

    return text.strip()


if __name__ == "__main__":
    pdf_file = "test_pdfs/testpdf.pdf"  # Change this to your actual file path
    extracted_text = extract_text_from_pdf(pdf_file)

    # Save the extracted text to a file
    output_path = "test_pdfs/extracted/testpdf_text.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    print(f"✅ Extracted text saved to {output_path}")