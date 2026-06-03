from concurrent.futures import ThreadPoolExecutor, as_completed

from detector import detect_page_type
from extractors.ocr import extract_text_from_page as extract_ocr
from extractors.text import extract_text_from_page as extract_text
from extractors.vision import extract_text_from_page as extract_vision

# Pages that call external APIs / OCR benefit from parallelism.
# text and blank pages are fast enough to do inline.
_MAX_WORKERS = 4


def _extract_heavy(pdf_path, page_index, ptype):
    """Extract a scanned or mixed page (slow path). Returns (page_index, text)."""
    try:
        if ptype == "scanned":
            text = extract_ocr(pdf_path, page_index)
        else:
            text = extract_vision(pdf_path, page_index)
        return page_index, text
    except Exception as e:
        return page_index, f"(error: {e})"


def markdown_format(pdf_path, start_page=None, end_page=None):
    import pdfplumber

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            start = (start_page - 1) if start_page else 0
            end = end_page if end_page else total
            start = max(0, start)
            end = min(total, end)

            if start >= total:
                return f"Error: start_page {start_page} exceeds total pages ({total})"

            # Pass 1: detect types, extract text/blank pages immediately
            results = {}  # page_index -> text
            heavy_tasks = []  # (page_index, ptype) for parallel extraction

            for i in range(start, end):
                page = pdf.pages[i]
                page_info = detect_page_type(page)
                ptype = page_info["pagetype"]

                if ptype == "text":
                    try:
                        results[i] = extract_text(page)
                    except Exception as e:
                        results[i] = f"(error: {e})"
                elif ptype == "blank":
                    results[i] = "(blank)"
                else:
                    # scanned or mixed — defer to thread pool
                    heavy_tasks.append((i, ptype))

        # Pass 2: parallel extraction for heavy pages (outside pdfplumber context)
        if heavy_tasks:
            with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
                futures = {
                    pool.submit(_extract_heavy, pdf_path, idx, pt): idx
                    for idx, pt in heavy_tasks
                }
                for future in as_completed(futures):
                    idx, text = future.result()
                    results[idx] = text

        # Assemble in page order
        content = ""
        for i in range(start, end):
            text = results.get(i, "(no data)")
            content += f"--- Page {i + 1} ---\n{text}\n\n"

    except Exception as e:
        return f"Error opening PDF: {e}"

    return content
