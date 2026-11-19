import re
import nltk

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_keywords(text):
    tokens = re.findall(r"[a-zA-Z]+", text)
    return list(set(tokens))
