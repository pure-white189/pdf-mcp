import fitz


def render_page_to_image(pdf_path, page_number, resolution=200):
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    pix = page.get_pixmap(dpi=resolution)
    image_bytes = pix.tobytes("png")
    doc.close()
    return image_bytes
