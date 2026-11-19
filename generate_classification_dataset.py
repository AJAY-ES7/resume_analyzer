import random
import csv

OUTPUT_FILE = "resume_classification_dataset.csv"
NUM_SAMPLES = 1000

def assign_label(skill_match, semantic, experience):
    # Add slight randomness for realism
    base_score = (skill_match * 0.6) + (semantic * 0.3) + (experience * 0.1)
    noise = random.uniform(-0.05, 0.05)
    final_value = base_score + noise

    if final_value > 0.75:
        return 2  # Strong
    elif final_value >= 0.45:
        return 1  # Average
    else:
        return 0  # Poor

data = []

for _ in range(NUM_SAMPLES):
    skill_match_ratio = round(random.uniform(0.0, 1.0), 2)
    semantic_similarity = round(random.uniform(0.3, 0.95), 2)

    experience_match = random.choice([0, 1])
    education_match = random.choice([0, 1])
    project_match = random.choice([0, 1])

    resume_length_score = round(random.uniform(0.4, 1.0), 2)
    keyword_density = round(random.uniform(0.3, 1.0), 2)

    label = assign_label(skill_match_ratio, semantic_similarity, experience_match)

    data.append([
        skill_match_ratio,
        semantic_similarity,
        experience_match,
        education_match,
        project_match,
        resume_length_score,
        keyword_density,
        label
    ])

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "skill_match_ratio",
        "semantic_similarity",
        "experience_match",
        "education_match",
        "project_match",
        "resume_length_score",
        "keyword_density",
        "label"
    ])
    writer.writerows(data)

print("Classification dataset generated successfully.")
