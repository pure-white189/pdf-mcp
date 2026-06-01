import io

import pytesseract
from PIL import Image
from utils import render_page_to_image


def extract_text_from_page(pdf_path, page_number):
    image_bytes = render_page_to_image(pdf_path, page_number)
    image = Image.open(io.BytesIO(image_bytes))
    try:
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "tesseract not found. Install it: sudo apt install tesseract-ocr tesseract-ocr-chi-sim"
        )
    return text
