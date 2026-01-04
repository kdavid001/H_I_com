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

    # Relationships
    notes = db.relationship('Note', backref='course', lazy=True, cascade="all, delete-orphan")
    messages = db.relationship('ChatMessage', backref='course', lazy=True, cascade="all, delete-orphan")

    # NEW: Link to Quiz Sessions (Groups of questions)
    quiz_sessions = db.relationship('QuizSession', backref='course', lazy=True, cascade="all, delete-orphan")


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


# 5. NEW: Quiz Session (The "Folder" for a set of questions)
class QuizSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # e.g., "Quiz 1"
    custom_topic = db.Column(db.String(150))  # e.g., "Vectors" (Optional)
    score = db.Column(db.Integer, default=0)  # Total correct answers
    total_questions = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    # Relationship to get specific questions in this session
    results = db.relationship('QuizResult', backref='session', lazy=True, cascade="all, delete-orphan")


# 6. UPDATED: Quiz Results (Individual Questions)
class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Link to the Session (Parent)
    session_id = db.Column(db.Integer, db.ForeignKey('quiz_session.id'), nullable=False)

    question = db.Column(db.String(500))
    selected_option = db.Column(db.String(200))
    correct_option = db.Column(db.String(200))
    is_correct = db.Column(db.Boolean)
    difficulty = db.Column(db.String(50))  # e.g., "Hard"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)