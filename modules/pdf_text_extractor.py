import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
import re
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(
    pdf_path: str,
    use_ocr: bool = True,
    dpi: int = 400,
    ocr_lang: str = 'eng',
    fallback_strategy: str = 'hybrid'
) -> str:
    """
    Enhanced PDF text extraction with multiple fallback strategies.
    
    Args:
        pdf_path: Path to PDF file
        use_ocr: Whether to use OCR when needed
        dpi: Resolution for OCR
        ocr_lang: Language(s) for OCR
        fallback_strategy: 'hybrid', 'ocr-only', or 'native-only'
    
    Returns:
        Extracted text as string (empty string if extraction fails)
    """
    text = ""
    
    try:
        doc = fitz.open(pdf_path)
        
        for page in doc:
            # Strategy 1: Native text extraction
            if fallback_strategy in ['hybrid', 'native-only']:
                page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
                if page_text.strip():
                    text += page_text + "\n"
                    continue

            # Strategy 2: OCR fallback
            if use_ocr and fallback_strategy in ['hybrid', 'ocr-only']:
                try:
                    pix = page.get_pixmap(dpi=dpi)
                    img = Image.open(io.BytesIO(pix.tobytes())).convert('L')
                    
                    custom_config = f'--oem 3 --psm 6 -l {ocr_lang}'
                    page_text = pytesseract.image_to_string(img, config=custom_config)
                    
                    if page_text.strip():
                        text += page_text + "\n"
                        
                except Exception as ocr_error:
                    logger.warning(f"OCR failed: {ocr_error}")

        doc.close()
        
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        return ""
    
    return clean_extracted_text(text)

def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text"""
    if not isinstance(text, str):
        return ""
        
    # Remove unwanted characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'(?<!\n)\s+', ' ', text)  # Collapse spaces
    text = re.sub(r'\n{3,}', '\n\n', text)   # Limit newlines
    
    # Remove page numbers and headers/footers
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    return text.strip()

def extract_text_with_metadata(
    pdf_path: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Extract text with full metadata (alternative version)
    Returns dict with both text and metadata
    """
    result = {
        'text': extract_text_from_pdf(pdf_path, **kwargs),
        'metadata': {
            'source': pdf_path,
            'pages': 0,
            'methods': []
        }
    }
    
    try:
        with fitz.open(pdf_path) as doc:
            result['metadata']['pages'] = len(doc)
    except:
        pass
        
    return result

if __name__ == "__main__":
    # Example usage
    text = extract_text_from_pdf("sample.pdf")
    print(f"Extracted {len(text)} characters")