import pdfplumber


def extract_text_from_page(page) -> str:
    content = page.extract_text(layout=True)
    if content:
        text = content.strip()
        # 只压缩连续3行以上的空行，保留代码缩进
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
    else:
        text = ""
    return text


def extract_text_from_pdf(pdf_path) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += extract_text_from_page(page)
            text += "\n"
    return text
