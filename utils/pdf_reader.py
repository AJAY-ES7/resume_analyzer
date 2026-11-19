from pdfminer.high_level import extract_text

def extract_pdf_text(path):
    try:
        text = extract_text(path)
        return text if text else ""
    except Exception:
        return ""
