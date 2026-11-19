def generate_recommendations(missing_skills, semantic_score):
    recommendations = []

    # Skill-based recommendations
    if missing_skills:
        recommendations.append(
            "Consider learning or highlighting these skills: " +
            ", ".join(missing_skills)
        )

    # Semantic score-based advice
    if semantic_score < 50:
        recommendations.append(
            "Your resume content does not strongly align with the job description. "
            "Try rewriting experience using keywords from the job description."
        )
    elif semantic_score < 70:
        recommendations.append(
            "Your resume partially matches the job description. "
            "Improve alignment by emphasizing relevant responsibilities and projects."
        )
    else:
        recommendations.append(
            "Your resume matches the job description well. Minor improvements can further strengthen it."
        )

    # Generic AI-style advice
    recommendations.append(
        "Use action verbs, measurable results, and job-specific terminology to improve impact."
    )

    return recommendations
