import sqlite3

def init_db():
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        profile_photo BLOB
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY,
        student_id INTEGER,
        course TEXT,
        grade TEXT,
        comments TEXT,
        FOREIGN KEY(student_id) REFERENCES users(id)
    )''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY,
            student_id INTEGER,
            course TEXT,
            file_data BLOB,
            file_name TEXT,
            FOREIGN KEY(student_id) REFERENCES users(id)
        )
    ''')

    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:  # Only insert if the table is empty
        users = [
            ('admin', 'admin123', 'admin', None),
            ('duygu', 'duygu123', 'student', None),
            ('burak', 'burak123', 'student', None)
        ]

        for user in users:
            c.execute('INSERT INTO users (username, password, role, profile_photo) VALUES (?, ?, ?, ?)', user)

    # Check if grades table is empty
    c.execute('SELECT COUNT(*) FROM grades')
    if c.fetchone()[0] == 0:  # Only insert if the table is empty
        grades = [
            (2, 'Human Computer Interaction', 'A', 'Outstanding'),
            (2, 'Cybersecurity Practices and App.', 'A', 'Great job!'),
            (2, 'Fundamentals of Computing', 'A', 'Outstanding'),
            (2, 'Math', 'A', 'Great job!'),
            (2, 'Physics', 'A', 'Outstanding'),
            (3, 'Math', 'C', 'Needs improvement'),
            (3, 'Chemistry', 'B', 'Good progress')
        ]
        for grade in grades:
            c.execute('INSERT INTO grades (student_id, course, grade, comments) VALUES (?, ?, ?, ?)', grade)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
