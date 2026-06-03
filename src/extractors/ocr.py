import io
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import pytesseract
from PIL import Image
from utils import render_page_to_image

_OCR_TIMEOUT = 30  # seconds


def _run_ocr(image):
    """Run pytesseract OCR on an image. Called in a separate thread."""
    try:
        return pytesseract.image_to_string(image, lang="chi_sim+eng")
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "tesseract not found. Install it: sudo apt install tesseract-ocr tesseract-ocr-chi-sim"
        )


def extract_text_from_page(pdf_path, page_number):
    image_bytes = render_page_to_image(pdf_path, page_number)
    image = Image.open(io.BytesIO(image_bytes))

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_ocr, image)
        try:
            text = future.result(timeout=_OCR_TIMEOUT)
        except FuturesTimeoutError:
            future.cancel()
            raise RuntimeError(f"OCR timed out after {_OCR_TIMEOUT}s on page {page_number}")

    return text
