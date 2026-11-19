import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load dataset
data = pd.read_csv("resume_classification_dataset.csv")

X = data.drop("label", axis=1)
y = data["label"]

# Feature scaling (important for logistic regression)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# Logistic Regression
model = LogisticRegression(
    multi_class="multinomial",
    solver="lbfgs",
    max_iter=1000
)

model.fit(X_train, y_train)

# Evaluation
predictions = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, predictions))
print("\nClassification Report:\n")
print(classification_report(y_test, predictions))

# Save model and scaler
joblib.dump(model, "resume_logistic_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Model and scaler saved successfully.")
