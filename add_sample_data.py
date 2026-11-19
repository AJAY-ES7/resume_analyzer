import sqlite3

conn = sqlite3.connect("jobs.db")
cursor = conn.cursor()

# -------- ADD USERS --------
users = [
    ("Ajay", "ajay@gmail.com"),
    ("Rahul", "rahul@gmail.com"),
    ("Meera", "meera@gmail.com"),
    ("Arun", "arun@gmail.com")
]

cursor.executemany(
    "INSERT INTO users (name,email) VALUES (?,?)",
    users
)

# -------- ADD HR --------
hrs = [
    ("Priya HR", "priya.hr@company.com"),
    ("Vikram HR", "vikram.hr@company.com"),
    ("Sneha HR", "sneha.hr@company.com")
]

cursor.executemany(
    "INSERT INTO hr (name,email) VALUES (?,?)",
    hrs
)

conn.commit()
conn.close()

print("Sample users and HR added successfully")
