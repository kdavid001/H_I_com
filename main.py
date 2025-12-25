import os
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash  # <--- THE SECURITY TOOLS
from models import db, User, Note, ChatMessage

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'huawei_demo_secret_key'  # Required for sessions

# CONFIG: Uploads
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect DB
db.init_app(app)

# Create Tables (Run this once)
with app.app_context():
    db.create_all()


# --- AUTH ROUTES (Login & Register) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # User can login with Email OR Username
        identifier = request.form.get('identifier')  # "identifier" can be email or username
        password = request.form.get('password')

        # 1. Find user by Email OR Username
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()

        # 2. Check Password Hash
        # We don't compare strings. We use the secure check function.
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials. Please try again.")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 1. Check if user exists
        user_exists = User.query.filter((User.email == email) | (User.username == username)).first()
        if user_exists:
            return render_template('register.html', error="User already exists! Try logging in.")

        # 2. Hash the Password (The "Hashing" Part)
        # This turns "password123" into "pbkdf2:sha256:260000$..."
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        # 3. Create User
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Send them to login page

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MAIN APP ROUTES (Protected) ---
# --- ADD THESE IMPORTS ---
from models import db, User, Note, ChatMessage, Course


# --- UPDATE HOME ROUTE ---
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Show the Course Dashboard instead of the Chat Interface
    user_courses = Course.query.filter_by(user_id=session['user_id']).all()
    return render_template("courses.html", username=session.get('username'), courses=user_courses)


# --- NEW ROUTE: CREATE COURSE ---
@app.route('/create_course', methods=['POST'])
def create_course():
    if 'user_id' not in session: return redirect(url_for('login'))

    title = request.form.get('title')
    new_course = Course(title=title, user_id=session['user_id'])
    db.session.add(new_course)
    db.session.commit()

    return redirect(url_for('home'))


# --- NEW ROUTE: STUDY MODE (The Chat Interface) ---
@app.route('/study/<int:course_id>')
def study(course_id):
    if 'user_id' not in session: return redirect(url_for('login'))

    course = Course.query.get_or_404(course_id)
    # Pass the course_id to the template so JavaScript can use it
    return render_template("index.html", course=course, username=session.get('username'))


# --- 1. UPDATED UPLOAD ROUTE (Returns ID now) ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401

    course_id = request.form.get('course_id')
    if not course_id: return jsonify({"error": "Missing Course ID"}), 400

    files = request.files.getlist('file')
    saved_files_data = []  # Changed list to store objects

    for file in files:
        if file.filename == '': continue
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        new_note = Note(
            filename=filename,
            extracted_text="Processing...",
            course_id=course_id
        )
        db.session.add(new_note)
        db.session.commit()  # Commit immediately to get the ID

        # Store ID and Name to send back to frontend
        saved_files_data.append({'id': new_note.id, 'name': filename})

    return jsonify({"message": "Files saved", "files": saved_files_data})


# --- 2. UPDATED HISTORY ROUTE (Returns ID now) ---
@app.route('/api/history')
def get_history():
    if 'user_id' not in session: return jsonify({"has_history": False})

    course_id = request.args.get('course_id')

    notes = Note.query.filter_by(course_id=course_id).order_by(Note.upload_date.desc()).all()
    chats = ChatMessage.query.filter_by(course_id=course_id).all()

    # Return objects with ID and Name
    notes_data = [{'id': n.id, 'name': n.filename} for n in notes]

    return jsonify({
        "has_history": True,
        "files": notes_data,
        "chats": [{"text": c.text, "is_user": c.is_user} for c in chats]
    })


# --- 3. NEW ROUTE: DELETE NOTE ---
@app.route('/api/note/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401

    note = Note.query.get_or_404(note_id)

    # Optional: Verify ownership logic here if needed

    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Deleted successfully"})


# --- 4. NEW ROUTE: RENAME NOTE ---
@app.route('/api/note/<int:note_id>', methods=['PUT'])
def rename_note(note_id):
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    new_name = data.get('new_name')

    note = Note.query.get_or_404(note_id)
    note.filename = new_name
    db.session.commit()

    return jsonify({"message": "Renamed successfully"})

# --- UPDATED API: CHAT (Requires Course ID) ---
@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session: return jsonify({"response": "Login required"})

    data = request.json
    user_message = data.get('message')
    course_id = data.get('course_id')  # <--- GET ID

    # Save User Msg
    msg = ChatMessage(text=user_message, is_user=True, course_id=course_id)
    db.session.add(msg)

    # Simulate AI
    import time
    time.sleep(1)
    ai_text = f"Simulated Answer for course {course_id}: {user_message}"

    # Save AI Msg
    ai_msg = ChatMessage(text=ai_text, is_user=False, course_id=course_id)
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({"response": ai_text})


# --- NEW ROUTE: VIEW/DOWNLOAD FILE ---
@app.route('/api/file/<int:note_id>')
def view_file(note_id):
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401

    # 1. Get the note from DB to find its filename
    note = Note.query.get_or_404(note_id)

    # 2. Serve the file from the uploads folder
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            note.filename,
            as_attachment=False  # False = View in Browser (PDF), True = Force Download
        )
    except FileNotFoundError:
        return "File not found on server", 404


# --- NEW ROUTE: DELETE COURSE ---
@app.route('/api/course/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401

    course = Course.query.get_or_404(course_id)

    # Security: Ensure the course belongs to the current user
    if course.user_id != session['user_id']:
        return jsonify({"error": "Forbidden"}), 403

    # 1. Delete all related Notes
    Note.query.filter_by(course_id=course_id).delete()

    # 2. Delete all related Chats
    ChatMessage.query.filter_by(course_id=course_id).delete()

    # 3. Delete all related Quizzes
    QuizResult.query.filter_by(course_id=course_id).delete()

    # 4. Finally, delete the Course
    db.session.delete(course)
    db.session.commit()

    return jsonify({"message": "Course deleted"})


# --- NEW ROUTE: RENAME COURSE ---
@app.route('/api/course/<int:course_id>', methods=['PUT'])
def rename_course(course_id):
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401

    course = Course.query.get_or_404(course_id)

    if course.user_id != session['user_id']:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json
    course.title = data.get('new_title')
    db.session.commit()

    return jsonify({"message": "Renamed"})





if __name__ == '__main__':
    app.run(debug=True)