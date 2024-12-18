from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('login.html')

@main.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Vulnerable SQL Query (SQL Injection)
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute(query)  # No parameterized query
    user = c.fetchone()
    conn.close()
    
    if user:
        role = user[3]
        session['username'] = user[1]  # Store username in session
        session['role'] = user[3]      # Store role in session
        if user[3] == 'admin':
            return redirect(url_for('main.admin_dashboard', username=username))
        else:
            return redirect(url_for('main.student_dashboard', student_id=user[0], username=username))
    else:
        return "Invalid credentials"


# Student Dashboard
@main.route('/student/<student_id>')
def student_dashboard(student_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    username=session['username'] 
    role=  session['role'] 
    # Fetch all courses, grades, and comments for the student
    c.execute("SELECT course, grade, comments FROM grades WHERE student_id=?", (student_id,))
    courses = c.fetchall()
    conn.close()

    return render_template('student_dashboard.html', courses=courses, username= username, role=role, student_id=student_id)

@main.route('/student/<student_id>/grades')
def grades(student_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    username=session['username'] 
    role=  session['role'] 
    # Fetch all courses, grades, and comments for the student
    c.execute("SELECT course, grade, comments FROM grades WHERE student_id=?", (student_id,))
    courses = c.fetchall()
    conn.close()

    return render_template('grades.html', courses=courses, username= username, role=role, student_id=student_id)


# Admin Dashboard
@main.route('/admin')
def admin_dashboard():
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    # Fetch all students, courses, grades, and comments
    c.execute('''SELECT u.username, g.course, g.grade, g.comments, g.id 
                 FROM grades g JOIN users u ON g.student_id = u.id''')
    grades = c.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', grades=grades)

# Edit a grade as an admin
@main.route('/admin/edit/<grade_id>', methods=['GET', 'POST'])
def edit_grade(grade_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()

    if request.method == 'POST':
        grade = request.form['grade']
        
        comments = request.form['comments'].replace("'", "''")  # Escape single quotes
        c.execute("UPDATE grades SET grade=?, comments=? WHERE id=?", (grade, comments, grade_id))
        conn.commit()
        conn.close()
        return redirect(url_for('main.admin_dashboard'))
    
    # Fetch the current grade details
    c.execute("SELECT course, grade, comments FROM grades WHERE id=?", (grade_id,))
    grade_data = c.fetchone()
    conn.close()
    return render_template('edit_grade.html', grade_data=grade_data)

@main.route('/debug')
def debug_route():
    result = 1 / 0  #Causes a ZeroDivisionError and trigger a stack trace
    return f"Result: {result}"

@main.route('/logout')
def logout():
    session.clear()
    return redirect("/")
