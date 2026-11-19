import sqlite3

def setup_database():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    
    # Create the table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resume_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        job_title TEXT,
        score REAL,
        skill_percent REAL,
        exp_percent REAL,
        edu_percent REAL,
        resume_file TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    setup_database()
