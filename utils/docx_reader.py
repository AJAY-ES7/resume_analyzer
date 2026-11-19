import docx

def extract_docx_text(path):
    try:
        doc = docx.Document(path)
        fullText = [para.text for para in doc.paragraphs]
        return "\n".join(fullText)
    except Exception:
        return ""
