import sqlite3
import os

# Ensure we are in the correct directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "jobs.db")

def rebuild_structure():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. ADMIN TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    # 2. HR TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            company TEXT
        )
    """)

    # 3. USERS (CANDIDATES) TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    # 4. JOBS TABLE (The main job listings)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            skills TEXT,
            required_experience TEXT,
            required_degree TEXT
        )
    """)

    # 5. JOB REQUESTS TABLE (HR submissions for Admin approval)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hr_id INTEGER,
            job_title TEXT,
            skills TEXT,
            experience TEXT,
            degree TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. RESUME HISTORY TABLE (For user profile tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_title TEXT,
            score INTEGER,
            skill_percent REAL,
            exp_percent REAL,
            edu_percent REAL,
            resume_file TEXT
        )
    """)

    conn.commit()
    print("✅ All tables verified and structures fixed.")
    
    # Show what we have now
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Current Tables:", [t[0] for t in cursor.fetchall()])
    # Add this inside rebuild_structure() before conn.close()
    cursor.execute("INSERT INTO admin (name, email, password) VALUES (?, ?, ?)", 
               ('Admin', 'admin@test.com', 'admin123'))
    conn.commit()
    cursor.execute("ALTER TABLE resume_history ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
        print("✅ Success: 'created_at' column added to resume_history.")
    except sqlite3.OperationalError:
        print("ℹ️ Note: 'created_at' column already exists.")
    
    conn.close()

if __name__ == "__main__":
    rebuild_structure()