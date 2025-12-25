# handles the c onnection to the modelArts.
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the database variable
db = SQLAlchemy()


# 1. The User Table (Login Info)
# Add this class to models.py
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_user = db.Column(db.Boolean, default=True) # True = User, False = AI
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # In a real app, hash passwords! For the demo, plain text is risky but fast.
    password = db.Column(db.String(120), nullable=False)

    # Relationships (Links to other tables)
    notes = db.relationship('Note', backref='owner', lazy=True)
    quiz_results = db.relationship('QuizResult', backref='student', lazy=True)


# 2. The Note Table (Uploaded PDFs)
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Store the text extracted from the PDF here for RAG
    extracted_text = db.Column(db.Text, nullable=True)

    # Link to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# 3. The Quiz Result Table (Progress Tracking)
class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100))
    score = db.Column(db.Integer)

    # Link to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)