import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------
# Load Embedding Model
# ----------------------------
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------
# Degree Keywords (Rank Based)
# ----------------------------
DEGREE_KEYWORDS = {
    3: ["phd", "doctorate"],
    2: ["master", "m.tech", "mtech", "msc", "m.sc", "mba"],
    1: ["bachelor", "b.tech", "btech", "b.e", "be", "bsc", "b.sc"]
}

# ----------------------------
# Master Skill Vocabulary
# ----------------------------
MASTER_SKILLS = [
    "python", "java", "c++", "javascript", "react", "node.js",
    "flask", "django", "machine learning", "deep learning",
    "sql", "mongodb", "aws", "docker", "kubernetes",
    "html", "css", "pandas", "numpy", "tensorflow",
    "pytorch", "git", "linux"
]

# ----------------------------
# Action Verbs
# ----------------------------
ACTION_VERBS = [
    "built", "developed", "implemented", "designed",
    "led", "optimized", "created", "improved",
    "analyzed", "deployed", "automated"
]

# ----------------------------
# Extract Skills (Resume-Only Mode)
# ----------------------------
def extract_resume_skills(resume_text):
    resume_text_lower = resume_text.lower()
    return [skill for skill in MASTER_SKILLS if skill in resume_text_lower]

# ----------------------------
# Embedding Skill Matching
# ----------------------------
def embedding_skill_match(resume_text, job_skills, threshold=0.55):
    # Standardize casing for direct string matching
    resume_text_lower = resume_text.lower()

    # Split resume into chunks for semantic comparison
    resume_chunks = [
        chunk.strip()
        for chunk in re.split(r'\n|\. ', resume_text)
        if len(chunk.strip()) > 3
    ]

    # SAFETY CHECK: Handle empty or very short resumes
    if not resume_chunks:
        return [], job_skills, 0

    # Generate vector representations (requires a pre-defined embedding_model)
    resume_embeddings = embedding_model.encode(resume_chunks)
    skill_embeddings = embedding_model.encode(job_skills)

    matched = []
    missing = []

    for i, skill_embedding in enumerate(skill_embeddings):
        # --- ADDED SAFETY CHECK HERE ---
        if i >= len(job_skills):
            break
        
        skill_name = job_skills[i]

        # First, try a simple keyword check (efficient for exact matches)
        if skill_name.lower() in resume_text_lower:
            matched.append(skill_name)
            continue

        # Second, use cosine similarity for semantic matching (e.g., "Python" vs "Py")
        # skill_embedding is 1D, so we wrap it in [] to make it 2D for the similarity function
        similarities = cosine_similarity([skill_embedding], resume_embeddings)
        max_similarity = np.max(similarities)

        if max_similarity >= threshold:
            matched.append(skill_name)
        else:
            missing.append(skill_name)

    # Calculate the match ratio (avoid division by zero)
    ratio = len(matched) / len(job_skills) if job_skills else 0

    return matched, missing, ratio

# ----------------------------
# Experience Detection
# ----------------------------
def detect_experience(text):
    matches = re.findall(r'(\d+)\s*(\+)?\s*(years|year|yrs)', text.lower())
    return max([int(m[0]) for m in matches], default=0)

# ----------------------------
# Degree Detection
# ----------------------------
def detect_degree(text):
    text_lower = text.lower()
    detected_rank = 0

    for rank, keywords in DEGREE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected_rank = max(detected_rank, rank)

    return detected_rank

def get_required_degree_rank(required_degree):
    required_degree = required_degree.lower()

    for rank, keywords in DEGREE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in required_degree:
                return rank

    return 0

# ----------------------------
# Action Verb Score
# ----------------------------
def action_verb_score(text):
    text_lower = text.lower()
    count = sum(text_lower.count(verb) for verb in ACTION_VERBS)
    word_count = len(text.split())

    if word_count == 0:
        return 0

    return min((count / word_count) * 10, 1)

# ----------------------------
# Grammar Score
# ----------------------------
def grammar_score(text):
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return 1

    short_sentences = sum(1 for s in sentences if len(s.split()) < 3)
    ratio = short_sentences / len(sentences)

    return max(1 - ratio, 0)

# ----------------------------
# MAIN FUNCTION
# ----------------------------
def extract_features(resume_text, job_skills=None, required_experience=0, required_degree="bachelor"):

    word_count = len(resume_text.split())
    resume_length_score = min(word_count / 800, 1)
    action_score = action_verb_score(resume_text)
    grammar = grammar_score(resume_text)

    # -------- Resume-Only Mode --------
    if not job_skills:

        resume_skills = extract_resume_skills(resume_text)
        skill_coverage = len(resume_skills) / len(MASTER_SKILLS)

        final_score = (
            (resume_length_score * 0.25) +
            (action_score * 0.25) +
            (grammar * 0.25) +
            (skill_coverage * 0.25)
        )

        final_score = round(final_score * 100, 2)

        return {
            "mode": "resume_only",
            "extracted_skills": resume_skills,
            "experience_years": detect_experience(resume_text),
            "education_rank": detect_degree(resume_text),
            "resume_length_score": resume_length_score,
            "action_verb_score": action_score,
            "grammar_score": grammar,
            "skill_coverage": skill_coverage,
            "final_score": final_score,
            "weaknesses": []
        }

    # -------- Job Match Mode --------
    matched_skills, missing_skills, skill_match_ratio = embedding_skill_match(
        resume_text,
        job_skills
    )

    detected_experience = detect_experience(resume_text)
    experience_match = 1 if detected_experience >= required_experience else 0

    resume_degree_rank = detect_degree(resume_text)
    required_rank = get_required_degree_rank(required_degree)
    education_match = 1 if resume_degree_rank >= required_rank else 0

    final_score = (
        (skill_match_ratio * 0.40) +
        (experience_match * 0.20) +
        (education_match * 0.10) +
        (action_score * 0.10) +
        (grammar * 0.10) +
        (resume_length_score * 0.10)
    )

    final_score = round(final_score * 100, 2)

    weaknesses = []

    if skill_match_ratio < 0.5:
        weaknesses.append("Low skill match with job requirements")

    if experience_match == 0:
        weaknesses.append("Experience below required level")

    if education_match == 0:
        weaknesses.append("Required degree not satisfied")

    # ... inside extract_features function ...

    return {
        "mode": "job_match",
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "final_score": final_score,
        "skill_match_ratio": skill_match_ratio,
        "experience_match": experience_match,
        "education_match": education_match,
        # ADD THESE THREE LINES BELOW:
        "action_score": action_score,
        "grammar": grammar,
        "resume_length_score": resume_length_score,
        "weaknesses": weaknesses
    }
