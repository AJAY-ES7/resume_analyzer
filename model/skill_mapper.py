from model.embeddings import semantic_similarity

def semantic_skill_match(resume_skills, jd_skills, threshold=0.65):
    """
    Match skills semantically instead of exact matching
    """
    matched = []
    missing = []

    for jd_skill in jd_skills:
        found = False
        for res_skill in resume_skills:
            sim = semantic_similarity(jd_skill, res_skill)
            if sim >= threshold:
                matched.append(jd_skill)
                found = True
                break
        if not found:
            missing.append(jd_skill)

    return matched, missing
