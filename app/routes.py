from flask import Blueprint, Response, current_app, render_template, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import requests
import pickle
from jinja2.utils import urlize
from time import perf_counter

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
    role= session['role'] 
    # Fetch all courses, grades, and comments for the student
    c.execute(f"SELECT course, grade, comments FROM grades WHERE student_id='{student_id}'")
    courses = c.fetchall()

    c = conn.cursor()
    c.execute('SELECT profile_photo FROM users WHERE id = ?', (student_id,))

    result = c.fetchone()
    if result:
        profile_photo = result[0]
    conn.close()
    

    return render_template('student_dashboard.html', courses=courses, username= username, role=role, student_id=student_id, profile_photo=profile_photo)

@main.route('/student/<student_id>/grades')
def grades(student_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    username=session['username'] 
    role=  session['role'] 
    # Fetch all courses, grades, and comments for the student
    c.execute(f"SELECT course, grade, comments FROM grades WHERE student_id='{student_id}'")
    courses = c.fetchall()
    c = conn.cursor()
    c.execute('SELECT profile_photo FROM users WHERE id = ?', (student_id,))
    
    result = c.fetchone()
    if result:
        profile_photo = result[0]
    conn.close()

    return render_template('grades.html', courses=courses, username= username, role=role, student_id=student_id, profile_photo=profile_photo)


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

@main.route('/debug')
def debug_route():
    result = 1 / 0  #Causes a ZeroDivisionError and trigger a stack trace
    return f"Result: {result}"

@main.route('/lol')
def lol_route():
   for i in range(3):
        text = "abc@" + "." * (i+1)*5000 + "!"
   lenValue = len(text)
   begin = perf_counter()
   urlize(text)
   DURATION = perf_counter() - begin
   print(f"{lenValue}: took {DURATION} seconds!")  #Causes a ZeroDivisionError and trigger a stack trace
   return f"Result: {DURATION}"

@main.route('/logout')
def logout():
    session.clear()
    return redirect("/")
    
#For Identificaiton and Authentication Failures -> users can set passw like '123'
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template('register.html')
        
        try:
            with sqlite3.connect('vulnerable.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password, role, profile_photo) VALUES (?, ?, ?, ?)", (username, password, 'student', None))
                conn.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('main.index'))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another one.", "danger")
            return render_template('register.html')
        except sqlite3.OperationalError:
            flash("Database is currently locked. Please try again later.", "danger")
            return render_template('register.html')

    return render_template('register.html')



#For SSRF -> DOS Example && Software and Data Integrity Failures -> Insecure Deserialization
@main.route('/student/<student_id>/upload_assignment/<course>', methods=['GET', 'POST'])
def upload_assignment(student_id, course):
    username = session.get('username')
    role = session.get('role')

    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()
    c.execute('SELECT profile_photo FROM users WHERE id = ?', (student_id,))
    
    result = c.fetchone()
    if result:
        profile_photo = result[0]
  
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
                                   role=role, profile_photo=profile_photo)

        return "No file uploaded!", 400

    conn.close()
    return render_template('upload_assignment.html', 
                           course=course, 
                           student_id=student_id, 
                           username=username, 
                           role=role, 
                           file_name=file_name, 
                           deserialized_data=deserialized_data, profile_photo=profile_photo)

@main.route('/upload_photo/<student_id>', methods=['GET', 'POST'])
def upload_photo(student_id):
    username = session.get('username')
    role = session.get('role')
    profile_photo = None

    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()

    # Fetch the current profile photo
    c.execute('SELECT profile_photo FROM users WHERE id = ?', (student_id,))
    result = c.fetchone()
    if result:
        profile_photo = result[0]
    conn.close()

    if request.method == 'POST':
        photo_url = request.form.get('photo_url')
        print(photo_url)
        
        if photo_url:
            try:
                # Fetch the image data from the provided URL
                response = requests.get(photo_url, timeout=5)
                response.raise_for_status()  # Raise an HTTPError for bad responses
                file_data = response.content  # Binary content of the image

                # Store the image in the database
                conn = sqlite3.connect('vulnerable.db')
                c = conn.cursor()
                c.execute('UPDATE users SET profile_photo = ? WHERE id = ?', (file_data, student_id))
                conn.commit()
                conn.close()

                flash('Profile photo uploaded successfully!')
                return redirect(url_for('main.upload_photo', student_id=student_id))

            except requests.exceptions.RequestException as e:
                flash(f'Failed to fetch the photo from the URL: {str(e)}')
                return redirect(url_for('main.upload_photo', student_id=student_id))

        flash('No photo URL provided!')
        return redirect(url_for('main.upload_photo', student_id=student_id))

    return render_template('upload_photo.html', username=username, role=role, student_id=student_id, profile_photo=profile_photo)

@main.route('/get_profile_photo/<student_id>')
def get_profile_photo(student_id):
    conn = sqlite3.connect('vulnerable.db')
    c = conn.cursor()

    # Fetch the profile photo from the database
    c.execute('SELECT profile_photo FROM users WHERE id = ?', (student_id,))
    result = c.fetchone()
    conn.close()

    if result and result[0]:
        # Return the binary data as an image
        return Response(result[0], mimetype='image/jpeg')
    else:
        # Return a default image if no profile photo is found
        return redirect(url_for('static', filename='user.png'))
