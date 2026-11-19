import sqlite3


# -----------------------------
# JOB RECOMMENDATIONS
# -----------------------------
def recommend_jobs(user_skills):

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT job_title, skills FROM jobs")
    jobs = cursor.fetchall()

    recommendations = []

    # Normalize resume skills
    user_skills = [skill.strip().lower() for skill in user_skills]

    for job in jobs:

        title = job[0]

        # Normalize job skills from database
        job_skills = job[1].lower()
        job_skills = job_skills.replace(";", ",")
        job_skills = job_skills.split(",")

        job_skills = [skill.strip() for skill in job_skills]

        # Skill overlap
        overlap = len(set(user_skills).intersection(set(job_skills)))

        if overlap >= 1:
            recommendations.append(title)

    conn.close()

    return recommendations[:5]


# -----------------------------
# YOUTUBE RECOMMENDATIONS
# -----------------------------
def recommend_videos(score, missing_skills):

    videos = []

    if score < 60:

        for skill in missing_skills[:3]:
            videos.append(
                f"https://www.youtube.com/results?search_query={skill}+tutorial"
            )

    else:

        videos.append(
            "https://www.youtube.com/results?search_query=how+to+improve+resume"
        )

        videos.append(
            "https://www.youtube.com/results?search_query=technical+interview+preparation"
        )

    return videos
