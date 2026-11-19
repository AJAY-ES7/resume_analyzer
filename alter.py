import sqlite3
import os

# Set the path to your database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "jobs.db")

def get_admin_credentials():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Select email and password from the admin table
        cursor.execute("SELECT email, password FROM admin")
        admin = cursor.fetchone()
        
        if admin:
            print(f"Admin Email: {admin[0]}")
            print(f"Admin Password: {admin[1]}")
        else:
            print("No admin user found in the database.")
            
        conn.close()
    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    get_admin_credentials()