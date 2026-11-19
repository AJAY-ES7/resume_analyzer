# Add this inside rebuild_structure() before conn.close()
cursor.execute("INSERT INTO admin (name, email, password) VALUES (?, ?, ?)", 
               ('Admin', 'admin@test.com', 'admin123'))
conn.commit()