def hybrid_score(semantic_score, matched_skills, total_required):
    """
    semantic_score: float (0–1)
    matched_skills: int
    total_required: int
    """

    if total_required == 0:
        skill_score = 0
    else:
        skill_score = matched_skills / total_required

    final_score = (0.6 * semantic_score) + (0.4 * skill_score)

    return {
        "final": round(final_score * 100, 2),
        "semantic": round(semantic_score * 100, 2),
        "skill": round(skill_score * 100, 2)
    }
