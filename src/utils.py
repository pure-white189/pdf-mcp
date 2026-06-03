import fitz


def normalize_path(path: str) -> str:
    """Convert Windows path to WSL path if needed.

    Examples:
        G:\\folder\\file.pdf -> /mnt/g/folder/file.pdf
        C:\\Users\\name\\doc.pdf -> /mnt/c/Users/name/doc.pdf
        /mnt/g/folder/file.pdf -> /mnt/g/folder/file.pdf (unchanged)
    """
    # Already a Linux path, return as-is
    if path.startswith("/"):
        return path

    # Windows path: convert drive letter and backslashes
    if len(path) >= 2 and path[1] == ":":
        drive = path[0].lower()
        rest = path[2:].replace("\\", "/")
        return f"/mnt/{drive}{rest}"

    # Unknown format, return as-is
    return path


def render_page_to_image(pdf_path, page_number, resolution=200):
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    pix = page.get_pixmap(dpi=resolution)
    image_bytes = pix.tobytes("png")
    doc.close()
    return image_bytes
