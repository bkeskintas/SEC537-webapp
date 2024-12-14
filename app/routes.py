from flask import Blueprint, render_template, request, redirect, url_for
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
        if role == 'admin':
            return redirect(url_for('main.admin_dashboard', username=username))
        else:
            return redirect(url_for('main.student_dashboard', student_id=user[0]))
    else:
        return "Invalid credentials"

@main.route('/admin/<username>')
def admin_dashboard(username):
    # No role verification
    return f"Welcome Admin {username}! You can edit grades."

@main.route('/student/<student_id>')
def student_dashboard(student_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute(f"SELECT grade, username FROM grades JOIN users ON grades.student_id = users.id WHERE student_id={student_id}")
    data = c.fetchone()
    conn.close()
    if data:
        grade, username = data
        # Reflect username directly into HTML (vulnerable to XSS)
        return f"<h1>Welcome, {username}!</h1><p>Your grade is: {grade}</p>"
    else:
        return "No grade found"


        


