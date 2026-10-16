from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "student_management_secret_123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(100), nullable=False)

# ---- extra tables (courses, attendance, results, labs, library) ----
from models_extra import create_models
m = create_models(db)
Course, Enrollment, Attendance = m["Course"], m["Enrollment"], m["Attendance"]
Result, Lab, LabRecord = m["Result"], m["Lab"], m["LabRecord"]
Book, BookIssue = m["Book"], m["BookIssue"]
attendance_percentage, cgpa = m["attendance_percentage"], m["cgpa"]

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        if User.query.filter_by(email=email).first():
            flash("Email already exists!")
            return redirect('/register')
        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Registered! Please login")
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            if user.role == 'teacher':
                return redirect('/teacher')
            else:
                return redirect('/student')
        else:
            flash("Invalid email or password!")
    return render_template('login.html')

@app.route('/teacher', methods=['GET','POST'])
def teacher_dashboard():
    if session.get('role') != 'teacher':
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        db.session.add(Student(name=name, email=email, course=course))
        db.session.commit()
        flash("Student Added!")
    students = Student.query.all()
    return render_template('teacher_dashboard.html', students=students)

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/login')
    students = Student.query.all()
    return render_template('student_dashboard.html', students=students)

@app.route('/delete/<int:id>')
def delete(id):
    if session.get('role') != 'teacher':
        return redirect('/login')
    student = Student.query.get(id)
    if student:
        db.session.delete(student)
        db.session.commit()
    return redirect('/teacher')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)