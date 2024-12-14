import sqlite3

def init_db():
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS grades (student_id INTEGER, grade TEXT)''')
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('student1', 'password1', 'student')")
    c.execute("INSERT INTO grades (student_id, grade) VALUES (1, 'A')")
    c.execute("INSERT INTO grades (student_id, grade) VALUES (2, 'B')")
    conn.commit()
    conn.close()
