import joblib
import pandas as pd
import matplotlib.pyplot as plt

# Load model and scaler
model = joblib.load("resume_logistic_model.pkl")
scaler = joblib.load("scaler.pkl")

# Label mapping
labels = {
    0: "Poor Match",
    1: "Average Match",
    2: "Strong Match"
}

# Sample input
sample_input = pd.DataFrame([{
    "skill_match_ratio": 0.75,
    "semantic_similarity": 0.80,
    "experience_match": 1,
    "education_match": 1,
    "project_match": 1,
    "resume_length_score": 0.85,
    "keyword_density": 0.70
}])

# Scale input
scaled_input = scaler.transform(sample_input)

# Predict
prediction = model.predict(scaled_input)[0]
probabilities = model.predict_proba(scaled_input)[0]

score = round(max(probabilities) * 100, 2)

print("\n===== Resume Evaluation Result =====")
print("Match Level:", labels[prediction])
print("Confidence Score:", score, "%")

# Prepare pie chart
pie_labels = ["Poor Match", "Average Match", "Strong Match"]
pie_values = probabilities * 100

plt.figure()
plt.pie(pie_values, labels=pie_labels, autopct='%1.1f%%')
plt.title("Resume Match Probability Distribution")
plt.show()
