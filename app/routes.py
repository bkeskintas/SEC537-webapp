import os
from flask import Blueprint, current_app, render_template, render_template_string, request, redirect, url_for, session
import sqlite3
import requests
import pickle

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
    c.execute(query)  #No parameterized query
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username'] = user[1]  
        session['role'] = user[3]     
        if user[3] == 'admin':
            return redirect(url_for('main.admin_dashboard', username=username))
        else:
            return redirect(url_for('main.student_dashboard', student_id=user[0], username=username))
    else:
        return "Invalid credentials"


@main.route('/student/<student_id>')
def student_dashboard(student_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    username=session['username'] 
    role=  session['role'] 
    # Fetch all courses, grades, and comments for the student
    c.execute(f"SELECT course, grade, comments FROM grades WHERE student_id='{student_id}'")
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
    c.execute(f"SELECT course, grade, comments FROM grades WHERE student_id='{student_id}'")
    courses = c.fetchall()
    conn.close()

    return render_template('grades.html', courses=courses, username= username, role=role, student_id=student_id)


#Admin Dashboard
@main.route('/admin')
def admin_dashboard():
    #No role verification (causes Broken Access Control)
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    # Fetch all students, courses, grades, and comments
    c.execute('''SELECT u.username, g.course, g.grade, g.comments, g.id 
                 FROM grades g JOIN users u ON g.student_id = u.id''')
    grades = c.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', grades=grades)

@main.route('/admin/edit/<grade_id>', methods=['GET', 'POST'])
def edit_grade(grade_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()

    if request.method == 'POST':
        grade = request.form['grade']
        
        comments = request.form['comments']
        c.execute(f"UPDATE grades SET grade='{grade}', comments='{comments}' WHERE id='{grade_id}'")
        conn.commit()
        conn.close()
        return redirect(url_for('main.admin_dashboard'))
    
    c.execute(f"SELECT course, grade, comments FROM grades WHERE id='{grade_id}'")
    grade_data = c.fetchone()
    conn.close()
    return render_template('edit_grade.html', grade_data=grade_data)

@main.route('/student/<student_id>/upload_resource', methods=['GET', 'POST'])
def upload_resource(student_id):
    username = session['username'] 
    role = session['role']
    
    if request.method == 'POST':
        #url = request.form.get('url')
        serialized_data = request.form.get('url')

        try:
            # Vulnerable to SSRF: Fetch the URL content
            response = requests.get(serialized_data, timeout=5)
            content_type = response.headers.get('Content-Type', '')

            if 'text/html' in content_type:
                content = response.text  # Display HTML content
            elif 'application/pdf' in content_type:
                content = "Preview not supported for PDFs. Download the document directly."
            else:
                content = "Unsupported file type."
        except Exception as e:
            content = f"Error fetching resource: {str(e)}"

        # Vulnerable Deserialization
        if serialized_data:
            try:
                # Vulnerable: Deserializing untrusted data without validation
                deserialized_data = pickle.loads(serialized_data)
                content += f"<br>Deserialized Data: {deserialized_data}"
            except Exception as e:
                content += f"<br>Error during deserialization: {str(e)}"

        return render_template('upload_resource.html', url=serialized_data, content=content, student_id=student_id, username=username, role=role)

    return render_template('upload_resource.html', student_id=student_id, username=username, role=role)

@main.route('/student/<student_id>/view_assignment/<course>')
def view_assignment(student_id, course):
    username = session.get('username')
    role = session.get('role')

    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute("SELECT file_data FROM assignments WHERE student_id=? AND course=?", (student_id, course))
    data = c.fetchone()
    conn.close()

    if data:
        try:
            #Vulnerable deserialization of file data
            deserialized_data = pickle.loads(data[0])
            return f"Assignment Content for {course}: {deserialized_data[:200]} (truncated)"
        except Exception as e:
            return f"Error deserializing assignment: {str(e)}", 500

    return "No assignment found for this course.", 404

@main.route('/debug')
def debug_route():
    result = 1 / 0  #Causes a ZeroDivisionError and trigger a stack trace
    return f"Result: {result}"

@main.route('/logout')
def logout():
    session.clear()
    return redirect("/")

#For SSRF -> DOS Example && Software and Data Integrity Failures -> Insecure Deserialization
@main.route('/student/<student_id>/upload_assignment/<course>', methods=['GET', 'POST'])
def upload_assignment(student_id, course):
    username = session.get('username')
    role = session.get('role')

    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()

    # Check if an assignment already exists for this student and course
    c.execute("SELECT file_name, file_data FROM assignments WHERE student_id=? AND course=?", (student_id, course))
    existing_assignment = c.fetchone()

    file_name = None
    deserialized_data = None
    if existing_assignment:
        file_name = existing_assignment[0]  # Existing file name
        try:
            # Insecure Deserialization
            deserialized_data = pickle.loads(existing_assignment[1])
        except Exception as e:
            deserialized_data = f"Error deserializing data: {str(e)}"

    if request.method == 'POST':
        uploaded_file = request.files.get('file')

        # Vulnerable: No size or type validation (SSRF)
        if uploaded_file:
            # Serialize file data and store it in the database (Insecure Serialization)
            serialized_data = pickle.dumps(uploaded_file.read())
            file_name = uploaded_file.filename
            if existing_assignment:
                # Update existing assignment
                c.execute("UPDATE assignments SET file_data=?, file_name=? WHERE student_id=? AND course=?", 
                          (serialized_data, file_name, student_id, course))
            else:
                # New assignment
                c.execute("INSERT INTO assignments (student_id, course, file_data, file_name) VALUES (?, ?, ?, ?)", 
                          (student_id, course, serialized_data, file_name))
            conn.commit()
            conn.close()
            return render_template('successfully_upload.html', 
                                   course=course, 
                                   student_id=student_id, 
                                   username=username, 
                                   role=role,)

        return "No file uploaded!", 400

    conn.close()
    return render_template('upload_assignment.html', 
                           course=course, 
                           student_id=student_id, 
                           username=username, 
                           role=role, 
                           file_name=file_name, 
                           deserialized_data=deserialized_data)
