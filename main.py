import os
import json
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Note, ChatMessage, Course, QuizResult, QuizSession
from ai_engine import (find_best_context, generate_answer, generate_quiz_question, extract_text_from_file,
                       generate_summary)
from sqlalchemy import func

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'huawei_demo_secret_key'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect DB
db.init_app(app)

# Create Tables
with app.app_context():
    db.create_all()


# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter((User.email == email) | (User.username == username)).first():
            return render_template('register.html', error="User already exists!")

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- MAIN APP ROUTES ---
@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_courses = Course.query.filter_by(user_id=session['user_id']).all()
    return render_template("courses.html", username=session.get('username'), courses=user_courses)


@app.route('/create_course', methods=['POST'])
def create_course():
    if 'user_id' not in session: return redirect(url_for('login'))
    title = request.form.get('title')
    new_course = Course(title=title, user_id=session['user_id'])
    db.session.add(new_course)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/study/<int:course_id>')
def study(course_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    course = Course.query.get_or_404(course_id)
    notes = Note.query.filter_by(course_id=course_id).all()
    history = ChatMessage.query.filter_by(course_id=course_id).order_by(ChatMessage.timestamp).all()

    return render_template("index.html",
                           course=course,
                           notes=notes,
                           history=history,
                           username=session.get('username'))


# THE UPLOAD ROUTE
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    course_id = request.form.get('course_id')
    files = request.files.getlist('file')  # <--- Must match JS formData
    saved_files_data = []

    for file in files:
        if file.filename == '': continue
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # Extract Text
        extracted_text = extract_text_from_file(save_path)

        new_note = Note(
            filename=filename,
            extracted_text=extracted_text,
            course_id=course_id
        )
        db.session.add(new_note)
        db.session.commit()

        saved_files_data.append({'id': new_note.id, 'name': filename})

    return jsonify({"message": "Files processed", "files": saved_files_data})


# THE SUMMARY ROUTE
@app.route('/api/summary', methods=['POST'])
def get_summary():
    if 'user_id' not in session: return 401

    data = request.json
    course_id = data.get('course_id')
    topic = data.get('topic', '')

    notes = Note.query.filter_by(course_id=course_id).all()
    if not notes:
        return jsonify({"summary": "No notes uploaded yet."})

    full_text = " ".join([n.extracted_text for n in notes if n.extracted_text])

    # Generate Summary
    summary_text = generate_summary(full_text, topic)

    # ---Saved to Database, so it persists in Chat History ---
    formatted_summary = f"**📝 Study Summary**\n\n{summary_text}"

    new_msg = ChatMessage(text=formatted_summary, is_user=False, course_id=course_id)
    db.session.add(new_msg)
    db.session.commit()

    return jsonify({"summary": formatted_summary})


# --- NEW OCR UPLOAD ROUTE ---
@app.route('/api/upload/ocr', methods=['POST'])
def upload_ocr_file():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401

    course_id = request.form.get('course_id')
    files = request.files.getlist('file')
    saved_data = []

    for file in files:
        if not file.filename: continue
        filename = secure_filename("OCR_" + file.filename)  # Prefix to verify it worked
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # ENGINE 2: Optical (MindSpore)
        text = extract_text_from_file(save_path)

        new_note = Note(filename=filename, extracted_text=text, course_id=course_id)
        db.session.add(new_note)
        db.session.commit()
        saved_data.append({'id': new_note.id, 'name': filename})

    return jsonify({"message": "OCR processing complete", "files": saved_data})


# --- THE CORE CHAT & QUIZ LOGIC ---
@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session: return jsonify({"response": "Login required"})

    data = request.json
    user_message = data.get('message', '')
    course_id = data.get('course_id')
    selected_note_ids = data.get('note_ids', [])

    # Capture Difficulty AND Custom Topic
    difficulty = data.get('difficulty', 'Medium')
    custom_topic = data.get('custom_topic', '')

    # Save User Message.
    msg = ChatMessage(text=user_message, is_user=True, course_id=course_id)
    db.session.add(msg)

    # Gather Text Context
    query = Note.query.filter_by(course_id=course_id)
    if selected_note_ids:
        query = query.filter(Note.id.in_(selected_note_ids))
    course_notes = query.all()

    full_text = " ".join([n.extracted_text for n in course_notes if n.extracted_text])

    if not full_text.strip():
        return jsonify({"response": "⚠️ No notes found. Please upload a PDF first."})

    # --- BRANCH 1: QUIZ MODE ---
    if user_message.lower().strip() == "/quiz" or "quiz me" in user_message.lower():

        # Call AI Engine with Difficulty AND Custom Topic
        quiz_data = generate_quiz_question(full_text, difficulty, custom_topic)

        if quiz_data:
            return jsonify({
                "response": quiz_data,
                "is_quiz": True
            })
        else:
            return jsonify({"response": "⚠️ AI could not generate a quiz. Try selecting more notes.", "is_quiz": False})

    # --- BRANCH 2: NORMAL CHAT ---
    else:
        # RAG Search (MindSpore)
        context = find_best_context(user_message, full_text)

        # Generation (Uses Gemini API for now will switch to MindsporeLLM for the Phase 2)
        response_text = generate_answer(context, user_message)

        # Save History (Normal chat should be saved)
        ai_msg = ChatMessage(text=response_text, is_user=False, course_id=course_id)
        db.session.add(ai_msg)
        db.session.commit()

        return jsonify({"response": response_text, "is_quiz": False})


# --- NEW ROUTE: START QUIZ SESSION ---
@app.route('/api/quiz/start_session', methods=['POST'])
def start_session():
    if 'user_id' not in session: return 401
    data = request.json
    course_id = data.get('course_id')
    custom_topic = data.get('custom_topic', '')

    # Count existing quizzes
    count = QuizSession.query.filter_by(course_id=course_id).count()
    new_name = f"Quiz {count + 1}"

    # Create Session with Topic
    new_session = QuizSession(
        name=new_name,
        course_id=course_id,
        custom_topic=custom_topic
    )
    db.session.add(new_session)
    db.session.commit()

    return jsonify({"session_id": new_session.id, "name": new_name})


# --- SUBMIT RESULT ---
@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz_result():
    data = request.json

    new_result = QuizResult(
        session_id=data.get('session_id'),  # Link to the session
        question=data.get('question'),
        selected_option=data.get('selected'),
        correct_option=data.get('correct'),
        is_correct=(data.get('selected') == data.get('correct')),
        difficulty=data.get('difficulty')
    )
    db.session.add(new_result)

    # Session Score
    quiz_session = QuizSession.query.get(data.get('session_id'))
    if quiz_session:
        quiz_session.total_questions += 1
        if new_result.is_correct:
            quiz_session.score += 1

    db.session.commit()
    return jsonify({"status": "saved"})


# --- VIEW HISTORY PAGE ---
@app.route('/quiz_history/<int:course_id>')
def quiz_history(course_id):
    if 'user_id' not in session: return redirect(url_for('login'))

    course = Course.query.get_or_404(course_id)

    sessions = QuizSession.query.filter_by(course_id=course_id).order_by(
        QuizSession.timestamp.desc()).all()  # Get all sessions, newest first

    return render_template('quiz_history.html', course=course, sessions=sessions)


# --- FILE MANAGEMENT ---
@app.route('/api/note/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    if 'user_id' not in session: return 401
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Deleted"})


@app.route('/api/note/<int:note_id>', methods=['PUT'])
def rename_note(note_id):
    if 'user_id' not in session: return 401
    data = request.json
    note = Note.query.get_or_404(note_id)
    note.filename = data.get('new_name')
    db.session.commit()
    return jsonify({"message": "Renamed"})


@app.route('/api/file/<int:note_id>')
def view_file(note_id):
    if 'user_id' not in session: return 401
    note = Note.query.get_or_404(note_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], note.filename)


@app.route('/api/course/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    if 'user_id' not in session: return 401
    course = Course.query.get_or_404(course_id)
    if course.user_id != session['user_id']: return 403

    Note.query.filter_by(course_id=course_id).delete()
    ChatMessage.query.filter_by(course_id=course_id).delete()

    #  delete history
    QuizSession.query.filter_by(course_id=course_id).delete()
    # QuizResult will auto-delete due to DB cascade if configured, otherwise do manually:

    db.session.delete(course)
    db.session.commit()
    return jsonify({"message": "Course deleted"})


@app.route('/api/course/<int:course_id>', methods=['PUT'])
def rename_course(course_id):
    if 'user_id' not in session: return 401
    course = Course.query.get_or_404(course_id)
    if course.user_id != session['user_id']: return 403
    course.title = request.json.get('new_title')
    db.session.commit()
    return jsonify({"message": "Renamed"})


@app.route('/api/stats', methods=['GET'])
def get_user_stats():
    if 'user_id' not in session: return 401

    course_id = request.args.get('course_id')

    # Get all quiz results for this course
    # We join QuizResult with QuizSession to filter by course
    results = db.session.query(QuizResult, QuizSession).join(QuizSession) \
        .filter(QuizSession.course_id == course_id).all()

    if not results:
        return jsonify({"has_data": False})

    # Calculate Mastery & Weaknesses
    topic_scores = {}  #
    total_correct = 0
    total_questions = 0

    for res, sess in results:
        topic = sess.custom_topic or "General"
        if topic not in topic_scores: topic_scores[topic] = []

        is_correct = 1 if res.is_correct else 0
        topic_scores[topic].append(is_correct)

        total_correct += is_correct
        total_questions += 1

    # Finds Weakest Area
    weakest_topic = "None"
    lowest_avg = 100

    for topic, scores in topic_scores.items():
        avg = sum(scores) / len(scores)
        if avg < lowest_avg:
            lowest_avg = avg
            weakest_topic = topic

    # Generate Recommendation
    mastery_pct = int((total_correct / total_questions) * 100)

    recommendation = ""
    if mastery_pct > 80:
        recommendation = "You are doing great! Try increasing quiz difficulty to 'Hard'."
    elif weakest_topic != "None":
        recommendation = (f"We noticed you are struggling with '{weakest_topic}'. Try generating a Summary "
                          f"specifically for '{weakest_topic}' to review.")
    else:
        recommendation = "Keep taking quizzes to build your profile."

    return jsonify({
        "has_data": True,
        "mastery": mastery_pct,
        "weak_area": weakest_topic,
        "recommendation": recommendation,
        "total_quizzes": len(results)
    })


if __name__ == '__main__':
    app.run(debug=True)
