import os
from utils.pdf_reader import extract_pdf_text
from utils.docx_reader import extract_docx_text
from utils.text_cleaner import clean_text

def extract_resume_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_pdf_text(file_path)
    elif ext == ".docx":
        text = extract_docx_text(file_path)
    elif ext == ".txt":
        text = open(file_path, "r", encoding="utf-8").read()
    else:
        raise ValueError("Unsupported file format")

    return clean_text(text)
