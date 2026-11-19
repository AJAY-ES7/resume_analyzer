from flask import send_file
import openpyxl
from openpyxl.styles import Font, PatternFill
import io

from flask import Flask, render_template, request, redirect, url_for,session
from PyPDF2 import PdfReader
import sqlite3

from feature_extractor import extract_features
from recommendation_engine import recommend_jobs, recommend_videos

app = Flask(__name__)

app.secret_key = "resumeai_secret"


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, job_title FROM jobs")
    jobs = cursor.fetchall()
    conn.close()
    
    return render_template("index.html", jobs=jobs)

# ---------------- RESUME ANALYSIS ----------------
@app.route("/predict_form", methods=["POST"])
def predict_form():
    
    if session.get("role") != "user":
        return redirect("/login")
    resume_file = request.files.get("resume_file")

    if not resume_file:
        return "Please upload a resume"

    reader = PdfReader(resume_file)
    resume_text = ""
    for page in reader.pages:
        resume_text += page.extract_text() or ""

    job_id = request.form.get("job_id")

    # -------- JOB MATCH MODE --------
    if job_id:
        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_title, skills, required_experience, required_degree FROM jobs WHERE id=?",
            (job_id,)
        )
        job = cursor.fetchone()
        conn.close()

        if not job:
            return "Job not found"

        job_title = job[0]
        job_skills = [s.strip() for s in job[1].split(",")]
        req_exp = job[2]
        req_deg = job[3]

        features = extract_features(resume_text, job_skills, req_exp, req_deg)

    # -------- RESUME ONLY MODE --------
    else:
        features = extract_features(resume_text)
        job_title = None

    score = features.get("final_score", 0)
    mode = features.get("mode")

    # -------- RECOMMENDATIONS --------
    if mode == "resume_only":
        user_skills = features.get("extracted_skills", [])
        video_recommendations = [
            "https://www.youtube.com/results?search_query=resume+writing+tutorial",
            "https://www.youtube.com/results?search_query=how+to+build+a+strong+resume",
            "https://www.youtube.com/results?search_query=resume+tips+for+freshers"
        ]

        weaknesses = []
        if len(user_skills) < 4:
            weaknesses.append("Very few technical skills mentioned")
        if score < 60:
            weaknesses.append("Resume structure could be improved")
        if score < 40:
            weaknesses.append("Add projects and achievements")
        
        features["weaknesses"] = weaknesses

    else:
        matched = features.get("matched_skills", [])
        missing = features.get("missing_skills", [])
        user_skills = matched + missing
        video_recommendations = recommend_videos(score, missing)

    job_recommendations = recommend_jobs(user_skills)
    features["job_recommendations"] = job_recommendations
    features["video_recommendations"] = video_recommendations

    return render_template("result.html", features=features, job_title=job_title)


# ---------------- HR DASHBOARD ----------------
@app.route("/hr_dashboard")
def hr_dashboard():
    # Check if user is HR
    if session.get("role") != "hr":
        return redirect("/login")

    # Fetch jobs to display
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, job_title FROM jobs")
    jobs = cursor.fetchall()
    conn.close()
    
    return render_template("hr_dashboard.html", jobs=jobs)

# ---------------- HR RESUME UPLOAD ----------------
@app.route("/hr/upload", methods=["POST"])
def hr_upload():
    job_id = request.form.get("job_id")
    resumes = request.files.getlist("resumes")

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT job_title, skills, required_experience, required_degree FROM jobs WHERE id=?",
        (job_id,)
    )
    job = cursor.fetchone()
    conn.close()

    if not job:
        return "Job not found"

    job_skills = [s.strip() for s in job[1].split(",")]
    req_exp = job[2]
    req_deg = job[3]

    candidates = []

    for resume in resumes:
        reader = PdfReader(resume)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        features = extract_features(text, job_skills, req_exp, req_deg)
        missing_skills = features.get("missing_skills", [])

        # FIXED INDENTATION HERE (Line 172 area)
        candidates.append({
            "name": resume.filename,
            "score": features.get("final_score", 0),
            "skill_match": round(features.get("skill_match_ratio", 0) * 100, 1),
            "experience": features.get("experience_match", "No"),
            "education": features.get("education_match", "No"),
            "missing": ", ".join(missing_skills[:3]) if missing_skills else "None"
        })

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return render_template("candidate_ranking.html", candidates=candidates)

@app.route("/download_excel")
def download_excel():

    candidates = request.args.get("data")

    if not candidates:
        return "No candidate data available"

    candidates = eval(candidates)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ranked Candidates"

    headers = [
        "Rank",
        "Candidate",
        "Skill Match %",
        "Experience",
        "Education",
        "Skill Gaps",
        "Final Score",
        "Status"
    ]

    ws.append(headers)

    header_font = Font(bold=True)

    for cell in ws[1]:
        cell.font = header_font

    for i, c in enumerate(candidates, start=1):

        if c["score"] > 75:
            status = "Shortlisted"
            fill = PatternFill(start_color="C6EFCE", fill_type="solid")

        elif c["score"] > 50:
            status = "Review"
            fill = PatternFill(start_color="FFEB9C", fill_type="solid")

        else:
            status = "Reject"
            fill = PatternFill(start_color="FFC7CE", fill_type="solid")

        row = [
            i,
            c["name"],
            c["skill_match"],
            c["experience"],
            c["education"],
            c["missing"],
            c["score"],
            status
        ]

        ws.append(row)

        for cell in ws[i+1]:
            cell.fill = fill

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name="ranked_candidates.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    # 1. Security Check
    if session.get("role") != "admin":
        return redirect("/login")

    # 2. Logic to fetch data
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM hr")
    hr_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs")
    job_count = cursor.fetchone()[0]
    conn.close()

    # 3. Return Template
    return render_template(
        "admin_dashboard.html",
        user_count=user_count,
        hr_count=hr_count,
        job_count=job_count
    )

# ---------------- ADMIN USERS ----------------
@app.route("/admin/users")
def admin_users():

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()

    return render_template("admin_users.html", users=users)


# ---------------- ADMIN HR ----------------
@app.route("/admin/hr")
def admin_hr():

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM hr")
    hrs = cursor.fetchall()

    conn.close()

    return render_template("admin_hr.html", hrs=hrs)


# ---------------- ADMIN JOBS ----------------
@app.route("/admin/jobs")
def admin_jobs():

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()

    conn.close()

    return render_template("admin_jobs.html", jobs=jobs)

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()

    conn.close()

    return redirect("/admin")
@app.route("/delete_hr/<int:hr_id>")
def delete_hr(hr_id):

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM hr WHERE id=?", (hr_id,))
    conn.commit()

    conn.close()

    return redirect("/admin")
@app.route("/delete_job/<int:job_id>")
def delete_job(job_id):

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    conn.commit()

    conn.close()

    return redirect("/admin")
@app.route("/add_job", methods=["POST"])
def add_job():

    title = request.form["title"]
    skills = request.form["skills"]
    exp = request.form["experience"]
    degree = request.form["degree"]

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO jobs(job_title, skills, required_experience, required_degree) VALUES(?,?,?,?)",
        (title, skills, exp, degree)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
@app.route("/edit_job/<int:job_id>", methods=["POST"])
def edit_job(job_id):

    title = request.form["title"]
    skills = request.form["skills"]
    exp = request.form["experience"]
    degree = request.form["degree"]

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET job_title=?, skills=?, required_experience=?, required_degree=?
        WHERE id=?
        """,
        (title, skills, exp, degree, job_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
@app.route("/signup/user", methods=["GET","POST"])
def signup_user():

    if request.method == "POST":

        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("jobs.db")
        c = conn.cursor()

        c.execute(
        "INSERT INTO users(first_name,last_name,email,password) VALUES(?,?,?,?)",
        (first,last,email,password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup_user.html")
@app.route("/signup/hr", methods=["GET","POST"])
def signup_hr():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        company = request.form["company"]
        password = request.form["password"]

        conn = sqlite3.connect("jobs.db")
        c = conn.cursor()

        c.execute(
        "INSERT INTO hr(name,email,company,password) VALUES(?,?,?,?)",
        (name,email,company,password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup_hr.html")
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("jobs.db")
        c = conn.cursor()

        # check admin
        admin = c.execute(
        "SELECT * FROM admin WHERE email=? AND password=?",
        (email,password)).fetchone()

        if admin:
            session["role"] = "admin"
            return redirect("/admin")

        # check HR
        hr = c.execute(
        "SELECT * FROM hr WHERE email=? AND password=?",
        (email,password)).fetchone()

        if hr:
            session["role"] = "hr"
            return redirect("/hr_dashboard")

        # check user
        user = c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email,password)).fetchone()

        if user:
            session["role"] = "user"
            return redirect("/")

        return "Invalid login"

    return render_template("login.html")
@app.route("/signup_choice")
def signup_choice():
    return render_template("signup_choice.html")





# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)