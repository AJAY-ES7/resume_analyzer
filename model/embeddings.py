from sentence_transformers import SentenceTransformer, util

# Load model once (important for performance)
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str):
    """
    Convert text into vector embedding
    """
    return model.encode(text, convert_to_tensor=True)

def semantic_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts
    Returns value between 0 and 1
    """
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    score = util.cos_sim(emb1, emb2)
    return float(score)
