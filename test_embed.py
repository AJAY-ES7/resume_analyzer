from model.embeddings import semantic_similarity

resume_text = "I know Python, SQL, data analysis and reporting"
jd_text = "Looking for a data analyst with SQL and Python skills"

score = semantic_similarity(resume_text, jd_text)

print("Similarity score:", score)
