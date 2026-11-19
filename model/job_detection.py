from .embeddings import similarity

JOB_ROLES = {
    "software engineer": ["python", "java", "git", "api", "backend", "frontend"],
    "data analyst": ["excel", "sql", "python", "visualization", "statistics"],
    "web developer": ["html", "css", "javascript", "react", "frontend"],
    "machine learning engineer": ["ml", "ai", "python", "model", "training"]
}

def detect_job_role(jd_text):
    best_role = None
    best_score = 0

    for role, keywords in JOB_ROLES.items():
        keyword_string = " ".join(keywords)
        score = similarity(jd_text, keyword_string)

        if score > best_score:
            best_score = score
            best_role = role

    return best_role
