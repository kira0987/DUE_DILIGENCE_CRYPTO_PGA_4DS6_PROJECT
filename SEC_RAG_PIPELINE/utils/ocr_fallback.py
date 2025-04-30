# utils/ocr_fallback.py
from PIL import Image
import pytesseract
import io

def ocr_if_needed(text):
    # Placeholder for scanned image detection
    if len(text.strip()) < 100:
        print("🧠 Text looks too short, running OCR fallback...")
        try:
            image = Image.open(io.BytesIO(text.encode()))
            return pytesseract.image_to_string(image)
        except:
            return text
    return text
