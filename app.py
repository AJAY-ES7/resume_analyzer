import os
import sqlite3
import io
import openpyxl
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from openpyxl.styles import Font, PatternFill
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime 
from feature_extractor import extract_features
from recommendation_engine import recommend_jobs, recommend_videos



app = Flask(__name__)
app.secret_key = "resumeai_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "jobs.db")

# ---------------- CONFIGURATION ----------------
# This handles your question about the uploads folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    try:
        conn = sqlite3.connect(db_path) # Using the path from Step 2
        cursor = conn.cursor()
        cursor.execute("SELECT id, job_title FROM jobs")
        jobs = cursor.fetchall()
        conn.close()
        return render_template("index.html", jobs=jobs)
    except sqlite3.DatabaseError as e:
        # This will print the exact folder path to your screen
        return f"Database Error at {db_path}: {e}"
    if session.get("role") != "user":
        return redirect("/login")
    return render_template("index.html", jobs=jobs)

# ---------------- PROFILE PAGE (NEW) ----------------
@app.route("/profile")
def profile():
    if session.get("role") != "user":
        return redirect("/login")

    user_id = session.get("user_id")
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    # Get User Details
    cursor.execute("SELECT first_name, last_name, email FROM users WHERE id=?", (user_id,))
    user_data = cursor.fetchone()

    # Get Resume History
    cursor.execute("""
        SELECT job_title, score, skill_percent, exp_percent, edu_percent, resume_file, created_at 
        FROM resume_history 
        WHERE user_id=? 
        ORDER BY created_at DESC
    """, (user_id,))
    history = cursor.fetchall()
    conn.close()

    return render_template("profile.html", user=user_data, history=history)

# ---------------- RESUME ANALYSIS (UPDATED) ----------------
# ---------------- RESUME ANALYSIS (UPDATED) ----------------
@app.route("/predict_form", methods=["POST"])
def predict_form():
    if session.get("role") != "user":
        return redirect("/login")
    
    resume_file = request.files.get("resume_file")
    if not resume_file:
        return "Please upload a resume"

    filename = secure_filename(resume_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    resume_file.save(file_path)

    reader = PdfReader(file_path)
    resume_text = ""
    for page in reader.pages:
        resume_text += page.extract_text() or ""

    job_id = request.form.get("job_id")

    if job_id:
        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT job_title, skills, required_experience, required_degree FROM jobs WHERE id=?", (job_id,))
        job = cursor.fetchone()
        conn.close()

        if not job:
            return "Job not found"

        job_title = job[0]
        job_skills = [s.strip() for s in job[1].split(",")]
        
        # --- FIX: SAFE CONVERSION FOR EXPERIENCE ---
        try:
            # Extract digits in case the DB has "3 years" or "3+"
            req_exp = int(''.join(filter(str.isdigit, str(job[2])))) if job[2] else 0
        except (ValueError, TypeError):
            req_exp = 0
            
        features = extract_features(resume_text, job_skills, req_exp, job[3])
    else:
        features = extract_features(resume_text)
        job_title = "General Analysis"

    # --- ADD IMPROVEMENT SUGGESTIONS ---
    suggestions = features.get("weaknesses", [])
    resume_text_lower = resume_text.lower()

    if "github.com" not in resume_text_lower:
        suggestions.append("Add a GitHub profile link to showcase your technical projects.")
    
    if "linkedin.com" not in resume_text_lower:
        suggestions.append("Include a LinkedIn profile link to strengthen your professional presence.")
        
    if "portfolio" not in resume_text_lower and "http" not in resume_text_lower:
        suggestions.append("Consider adding a link to a personal portfolio or project website.")

    features["weaknesses"] = suggestions

    # Ensure other required keys for the template
    score = features.get("final_score", 0)
    features["skill_percent"] = features.get("skill_match_ratio", 0) * 100
    features["experience_match"] = features.get("experience_match", 0) * 100
    features["education_match"] = features.get("education_match", 0) * 100
    features.setdefault("action_score", 0)
    features.setdefault("grammar", 0)
    features.setdefault("resume_length_score", 0)
    features["final_score"] = score

    # SAVE TO DATABASE (Keep your existing history logic)
    user_id = session.get("user_id")
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resume_history (user_id, job_title, score, skill_percent, exp_percent, edu_percent, resume_file)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, job_title, score, features["skill_percent"] * 100, 
          features["experience_match"] * 100, features["education_match"] * 100, filename))
    conn.commit()
    conn.close()

    # Recommendations
    missing = features.get("missing_skills", [])
    user_skills = (features.get("matched_skills", []) + missing) if features.get("mode") != "resume_only" else features.get("extracted_skills", [])
    features["video_recommendations"] = recommend_videos(score, missing)
    features["job_recommendations"] = recommend_jobs(user_skills)

    return render_template("result.html", features=features, job_title=job_title)
# ---------------- LOGIN (UPDATED) ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        conn = sqlite3.connect("jobs.db")
        c = conn.cursor()

        # Check Admin
        admin = c.execute("SELECT id FROM admin WHERE email=? AND password=?", (email, password)).fetchone()
        if admin:
            session["role"] = "admin"
            session["user_id"] = admin[0]
            conn.close()
            return redirect("/admin")

        # Check HR
        hr = c.execute("SELECT id FROM hr WHERE email=? AND password=?", (email, password)).fetchone()
        if hr:
            session["role"] = "hr"
            session["user_id"] = hr[0]
            conn.close()
            return redirect("/hr_dashboard")

        # Check User
        user = c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        if user:
            session["role"] = "user"
            session["user_id"] = user[0]
            conn.close()
            return redirect("/")

        # --- THE FIX ---
        conn.close()
        flash("Invalid email or password. Please try again.", "danger")
        return redirect(url_for("login")) 
        
    return render_template("login.html")

# ---------------- HR & ADMIN ROUTES (RETAINED) ----------------
@app.route("/hr_dashboard")
def hr_dashboard():
    if session.get("role") != "hr": 
        return redirect("/login")
    
    hr_id = session.get("user_id") # Get the logged-in HR's ID
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    
    # 1. Fetch current jobs (Existing)
    cursor.execute("SELECT id, job_title FROM jobs")
    jobs = cursor.fetchall()
    
    # 2. Fetch count of requests for this HR (New)
    # This handles the "Total Requests" number on your dashboard
    cursor.execute("SELECT COUNT(*) FROM job_requests WHERE hr_id=?", (hr_id,))
    request_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Pass the new 'request_count' variable to the template
    return render_template("hr_dashboard.html", jobs=jobs, request_count=request_count)

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin": return redirect("/login")
    conn = sqlite3.connect("jobs.db"); cursor = conn.cursor()
    user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    hr_count = cursor.execute("SELECT COUNT(*) FROM hr").fetchone()[0]
    job_count = cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    return render_template("admin_dashboard.html", user_count=user_count, hr_count=hr_count, job_count=job_count)

# ... Include your other delete/add/edit routes here ...
# ---------------- ADMIN USERS ----------------
@app.route("/admin/users")
def admin_users():

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    # We concatenate first_name and last_name as the "Name" column
    cursor.execute("SELECT id, (first_name || ' ' || last_name), email FROM users")
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
def add_job_view():

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
def edit_job_view(job_id):

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

@app.route("/signup_choice")
def signup_choice():
    return render_template("signup_choice.html")
@app.route('/view_resume/<filename>')
def view_resume(filename):
    if session.get("role") != "user":
        return redirect("/login")
    
    # This serves the file from the uploads directory to the browser
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route("/logout")
def logout():
    session.clear()  # This removes everything from the session
    return redirect("/login")
@app.route("/download_excel")
def download_excel():
    # Ensure the 'data' argument is fetched and evaluated correctly
    candidates_str = request.args.get("data")

    if not candidates_str:
        return "No candidate data available"

    try:
        # Converting the string back to a list of dictionaries
        candidates = eval(candidates_str)
    except Exception as e:
        return f"Error processing data: {str(e)}"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ranked Candidates"

    headers = [
        "Rank", "Candidate", "Skill Match %", "Experience",
        "Education", "Skill Gaps", "Final Score", "Status"
    ]
    ws.append(headers)

    header_font = Font(bold=True)
    for cell in ws[1]:
        cell.font = header_font

    # This loop must be indented exactly 4 spaces from the 'def' line
    for i, c in enumerate(candidates, start=1):
        score = c.get("score", 0)
        
        # Status Logic
        if score > 75:
            status = "Shortlisted"
            fill = PatternFill(start_color="C6EFCE", fill_type="solid")
        elif score > 50:
            status = "Review"
            fill = PatternFill(start_color="FFEB9C", fill_type="solid")
        else:
            status = "Reject"
            fill = PatternFill(start_color="FFC7CE", fill_type="solid")

        # Building the row using .get() to avoid KeyErrors
        row = [
            i,
            c.get("name", "Unknown"),
            f"{c.get('skill_match', 0)}%",
            c.get("experience", "N/A"),
            c.get("education", "N/A"),
            c.get("missing", "None"),
            f"{score}%",
            status
        ]

        ws.append(row)

        # Applying the fill to the current row
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
@app.route("/hr/upload", methods=["POST"])
def hr_upload():
    if session.get("role") not in ["hr", "admin"]:
        return redirect("/login")

    job_id = request.form.get("job_id")
    resumes = request.files.getlist("resumes") # Get multiple files
    
    if not resumes or not job_id:
        return "Missing job selection or resumes"

    # Get Job Details
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    # Updated to use 'required_experience' and 'required_degree' as per your jobs.db schema
    cursor.execute("SELECT job_title, skills, required_experience, required_degree FROM jobs WHERE id=?", (job_id,))
    job = cursor.fetchone()
    
    if not job:
        conn.close()
        return "Job not found"
    
    job_title, raw_skills, raw_exp, req_deg = job
    # Convert experience to integer safely to avoid TypeError
    try:
        # This removes any non-numeric characters and converts to int
        req_exp = int(''.join(filter(str.isdigit, str(raw_exp)))) if raw_exp else 0
    except ValueError:
        req_exp = 0
    if isinstance(raw_skills, str):
        job_skills = [s.strip() for s in raw_skills.split(",") if s.strip()]
    else:
        job_skills = raw_skills
    candidates_results = []

    # Process each resume
    for file in resumes:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract Text
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Analyze using your existing feature extractor
        features = extract_features(text, job_skills, req_exp, req_deg)
        
        # Format for candidate_ranking.html
        # Inside hr_upload in app.py
        candidates_results.append({
            "name": filename.replace(".pdf", ""),
            "score": features['final_score'],
            "skill_match": round(features['skill_match_ratio'] * 100, 1),
            "experience": req_exp, 
            "education": req_deg,  # <--- MAKE SURE THIS LINE IS PRESENT
            "missing": ", ".join(features['missing_skills'][:3])
        })

    conn.close()
    
    # Sort candidates by highest score first
    candidates_results = sorted(candidates_results, key=lambda x: x['score'], reverse=True)
    
    return render_template("candidate_ranking.html", candidates=candidates_results, job_title=job_title)
@app.route("/admin/add_job", methods=["GET", "POST"])
def add_job():
    if session.get("role") != "admin": return redirect("/login")
    
    if request.method == "POST":
        title = request.form['title']
        skills = request.form['skills']
        exp = request.form['experience']
        degree = request.form['degree']
        
        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jobs (job_title, skills, required_experience, required_degree) VALUES (?,?,?,?)", 
                       (title, skills, exp, degree))
        conn.commit()
        conn.close()
        return redirect("/admin/jobs")
        
    return render_template("add_job.html") # Create a simple form template for this
@app.route("/admin/edit_job/<int:id>", methods=["GET", "POST"])
def edit_job(id):
    if session.get("role") != "admin": return redirect("/login")
    
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    
    if request.method == "POST":
        title = request.form['title']
        skills = request.form['skills']
        exp = request.form['experience']
        degree = request.form['degree']
        
        cursor.execute("UPDATE jobs SET job_title=?, skills=?, required_experience=?, required_degree=? WHERE id=?", 
                       (title, skills, exp, degree, id))
        conn.commit()
        conn.close()
        return redirect("/admin/jobs")
    
    cursor.execute("SELECT * FROM jobs WHERE id=?", (id,))
    job = cursor.fetchone()
    conn.close()
    return render_template("edit_job.html", job=job)

@app.route("/hr/request_job", methods=["GET", "POST"])
def hr_request():
    if session.get("role") != "hr":
        return redirect("/login")
    
    hr_id = session.get("user_id")
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form['title'].strip()
        skills = request.form['skills']
        # Force the input to be an integer before saving to the database
        try:
            exp = int(''.join(filter(str.isdigit, str(request.form['experience']))))
        except ValueError:
            exp = 0
        deg = request.form['degree']
        
        # 1. Duplicate Check
        cursor.execute("SELECT id FROM jobs WHERE LOWER(job_title) = LOWER(?)", (title,))
        if cursor.fetchone():
            return render_template("hr_request.html", error="This job is already active.", requests=get_hr_requests(hr_id))
        
        cursor.execute("SELECT id FROM job_requests WHERE LOWER(job_title) = LOWER(?) AND status = 'Pending'", (title,))
        if cursor.fetchone():
            return render_template("hr_request.html", error="A request for this job is already pending.", requests=get_hr_requests(hr_id))

        # 2. Get current time for the timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 3. Insert with the real timestamp instead of default
        cursor.execute("""
            INSERT INTO job_requests (hr_id, job_title, skills, experience, degree, status, created_at) 
            VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        """, (hr_id, title, skills, exp, deg, now))
        conn.commit()
        return redirect("/hr/request_job")

    # GET request logic
    my_requests = get_hr_requests(hr_id)
    conn.close()
    return render_template("hr_request.html", requests=my_requests)

# Updated Helper Function
def get_hr_requests(hr_id):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    # Replace 'N/A' with the actual column name: created_at
    cursor.execute("""
        SELECT id, job_title, skills, experience, degree, created_at, status 
        FROM job_requests 
        WHERE hr_id=?
    """, (hr_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
@app.route("/admin/view_requests")
def admin_view_requests():
    if session.get("role") != "admin":
        return redirect("/login")
    
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    # Admin sees only Pending requests to take action on
    cursor.execute("SELECT * FROM job_requests WHERE status='Pending'")
    pending = cursor.fetchall()
    conn.close()
    return render_template("admin_view_requests.html", pending=pending)

@app.route("/admin/handle_request/<int:req_id>/<action>")
def handle_request(req_id, action):
    if session.get("role") != "admin":
        return redirect("/login")
        
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    
    if action == "approve":
        # 1. Fetch the details of the request
        cursor.execute("SELECT job_title, skills, experience, degree FROM job_requests WHERE id=?", (req_id,))
        req_data = cursor.fetchone()
        
        # 2. Insert into the ACTUAL jobs table that users see
        cursor.execute("""
            INSERT INTO jobs (job_title, skills, required_experience, required_degree) 
            VALUES (?, ?, ?, ?)
        """, req_data)
        
        # 3. Mark the request as Approved
        cursor.execute("UPDATE job_requests SET status='Approved' WHERE id=?", (req_id,))
    
    elif action == "reject":
        # Just mark as rejected
        cursor.execute("UPDATE job_requests SET status='Rejected' WHERE id=?", (req_id,))
        
    conn.commit()
    conn.close()
    return redirect("/admin/view_requests")
@app.context_processor
def inject_pending_count():
    count = 0
    if session.get("role") == "admin":
        try:
            conn = sqlite3.connect("jobs.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_requests WHERE status='Pending'")
            count = cursor.fetchone()[0]
            conn.close()
        except:
            count = 0
    return dict(pending_count=count)
if __name__ == "__main__":
    app.run(debug=True)