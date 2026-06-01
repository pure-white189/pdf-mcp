import os

import fitz
from formatter import markdown_format
from detector import detect_pdf_type
from extractors.vision import extract_text_from_image, bytes_to_base64_str
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pdf-reader")


def _validate_pdf_path(pdf_path: str) -> str | None:
    """Check if the path points to a valid PDF file. Returns error string or None."""
    if not os.path.exists(pdf_path):
        return f"Error: file not found: {pdf_path}"
    if not pdf_path.lower().endswith(".pdf"):
        return f"Error: not a PDF file: {pdf_path}"
    return None


@mcp.tool()
def pdf_extract(pdf_path: str) -> str:
    """Extract all text content from a PDF file as Markdown.
    Use this to read the full content of a PDF document.
    The pdf_path should be a Linux/WSL path (e.g. /mnt/c/Users/...).
    """
    err = _validate_pdf_path(pdf_path)
    if err:
        return err
    try:
        return markdown_format(pdf_path)
    except Exception as e:
        return f"Error extracting PDF: {e}"


@mcp.tool()
def pdf_extract_pages(pdf_path: str, start_page: int, end_page: int) -> str:
    """Extract text content from a specific page range of a PDF file.
    Pages are 1-indexed (first page = 1).
    Use this when you only need certain pages instead of the whole document.
    The pdf_path should be a Linux/WSL path (e.g. /mnt/c/Users/...).
    """
    err = _validate_pdf_path(pdf_path)
    if err:
        return err
    if start_page < 1:
        return "Error: start_page must be >= 1"
    if end_page < start_page:
        return "Error: end_page must be >= start_page"
    try:
        return markdown_format(pdf_path, start_page=start_page, end_page=end_page)
    except Exception as e:
        return f"Error extracting pages: {e}"


@mcp.tool()
def pdf_detect_type(pdf_path: str) -> str:
    """Detect the type of a PDF without extracting content.
    Returns the overall document type and per-page type breakdown.
    Useful for checking if a PDF is text-based, scanned, or mixed before extraction.
    The pdf_path should be a Linux/WSL path (e.g. /mnt/c/Users/...).
    """
    err = _validate_pdf_path(pdf_path)
    if err:
        return err
    try:
        result = detect_pdf_type(pdf_path)
    except Exception as e:
        return f"Error detecting PDF type: {e}"

    doc_type = result["doctype"]
    pages = result["pages"]
    summary = f"Document type: {doc_type}\nTotal pages: {len(pages)}\n\nPage breakdown:\n"
    for i, p in enumerate(pages):
        summary += f"  Page {i + 1}: {p['pagetype']}\n"
    return summary


@mcp.tool()
def pdf_extract_images(pdf_path: str, page_number: int) -> str:
    """Extract and describe all embedded images on a specific PDF page.
    Pages are 1-indexed (first page = 1).
    Uses vision AI to describe what each image shows.
    The pdf_path should be a Linux/WSL path (e.g. /mnt/c/Users/...).
    """
    err = _validate_pdf_path(pdf_path)
    if err:
        return err
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return f"Error opening PDF: {e}"

    page_idx = page_number - 1
    if page_idx < 0 or page_idx >= len(doc):
        doc.close()
        return f"Error: page {page_number} out of range (total {len(doc)} pages)"

    page = doc[page_idx]
    image_list = page.get_images(full=True)
    doc.close()

    if not image_list:
        return f"Page {page_number}: no embedded images found."

    results = []
    for img_idx, img_info in enumerate(image_list):
        xref = img_info[0]
        try:
            img_doc = fitz.open(pdf_path)
            base_image = img_doc.extract_image(xref)
            img_doc.close()
            image_bytes = base_image["image"]
            base64_str = bytes_to_base64_str(image_bytes)
            description = extract_text_from_image(base64_str)
            results.append(f"Image {img_idx + 1} on page {page_number}:\n{description}")
        except Exception as e:
            results.append(f"Image {img_idx + 1} on page {page_number}: error — {e}")

    return "\n\n".join(results)


mcp.run(transport="stdio")
