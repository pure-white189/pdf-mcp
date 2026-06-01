import pdfplumber


def detect_page_type(page) -> dict:
    """
    判断单页PDF的类型
    返回: {"pagetype": "text" / "mixed" / "scanned" / "blank"}
    """
    text = page.extract_text()
    char_count = len(text) if text else 0
    image_count = len(page.images)

    if char_count > 50 and image_count == 0:
        return {"pagetype": "text"}
    elif char_count > 50 and image_count >= 1:
        return {"pagetype": "mixed"}
    elif char_count <= 50 and image_count >= 2:
        return {"pagetype": "scanned"}
    elif char_count <= 50 and image_count == 1:
        return {"pagetype": "mixed"}
    else:
        return {"pagetype": "blank"}


def detect_pdf_type(pdf_path: str) -> dict:
    """
    检测PDF的类型
    返回: {"doctype": "text" / "mixed" / "blank", "pages": page_types}
    """
    scan_count = 0
    text_count = 0
    mixed_count = 0
    blank_count = 0
    try:
        with pdfplumber.open(pdf_path) as doc:
            page_types = [detect_page_type(page) for page in doc.pages]
    except Exception as e:
        raise ValueError(f"Cannot open PDF: {e}") from e

    for pt in page_types:
        if pt["pagetype"] == "scanned":
            scan_count += 1
        elif pt["pagetype"] == "text":
            text_count += 1
        elif pt["pagetype"] == "mixed":
            mixed_count += 1
        else:
            blank_count += 1
    if mixed_count > 0 or scan_count > 0:
        return {"doctype": "mixed", "pages": page_types}
    elif text_count > 0:
        return {"doctype": "text", "pages": page_types}
    else:
        return {"doctype": "blank", "pages": page_types}
