from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# 1. User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relationships
    courses = db.relationship('Course', backref='student', lazy=True)


# 2. Course
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships (Notes, Messages, and NOW Quizzes)
    notes = db.relationship('Note', backref='course', lazy=True)
    messages = db.relationship('ChatMessage', backref='course', lazy=True)
    quizzes = db.relationship('QuizResult', backref='course', lazy=True)  # <--- Added This


# 3. Chat Message
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)


# 4. Notes
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)


# 5. Quiz Results (Corrected)
class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100))  # e.g., "Calculus Integration"
    score = db.Column(db.Integer)  # e.g., 85
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Linked to COURSE, not just User.
    # We can always find the user via: quiz.course.student
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)