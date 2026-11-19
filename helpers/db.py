import sqlite3
from config import DB_PATH

def save_job_request(resume, jd, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume TEXT,
            jd TEXT,
            score INTEGER
        )
    """)

    c.execute(
        "INSERT INTO analysis_history (resume, jd, score) VALUES (?, ?, ?)",
        (resume, jd, score)
    )

    conn.commit()
    conn.close()
