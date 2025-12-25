import os
from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
from models import db, User, Note, QuizResult
# Ensure ai_service has these functions (or dummy versions)
from ai_service import generate_summary_from_modelarts

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CONFIG: Where to save uploaded PDFs
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect the DB to the App
db.init_app(app)

# Create Tables (Run once)
with app.app_context():
    db.create_all()


# --- ROUTES ---

@app.route('/')
def home():
    return render_template("index.html")


# --- ROUTE 1: Upload File (Saves PDF + DB Metadata) ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)  # 1. Save PDF to disk

        # 2. Simulate Text Extraction (In real life, PyPDF2 goes here)
        extracted_text_simulation = f"Text extracted from {filename}..."

        # 3. Call AI Service (Optional: Generate Summary immediately)
        # summary = generate_summary_from_modelarts(extracted_text_simulation)

        # 4. Save to Database
        # We use User ID 1 for the demo
        new_note = Note(filename=filename, extracted_text=extracted_text_simulation, user_id=1)
        db.session.add(new_note)
        db.session.commit()

        return jsonify({
            "message": "File saved successfully",
            "filename": filename
            # "summary": summary  <-- Uncomment if you want summary sent back immediately
        })


# --- ROUTE 2: Chat (The Missing Piece!) ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')

    # [Logic]: Here you would call ModelArts with the context of the last uploaded file

    # [Simulation for Demo]:
    import time
    time.sleep(1)  # Fake thinking time

    response_text = f"I found this answer in your notes regarding '{user_message}': [Simulated MindSpore Response]"

    return jsonify({"response": response_text})


# --- ROUTE 3: History (Restores Session) ---
@app.route('/api/history', methods=['GET'])
def get_history():
    # Fetch last upload for User 1
    last_note = Note.query.filter_by(user_id=1).order_by(Note.id.desc()).first()

    if last_note:
        return jsonify({
            "has_history": True,
            "last_file": last_note.filename,
            # If you added ChatMessage table, you would fetch chats here
            "chats": []
        })
    else:
        return jsonify({"has_history": False})


if __name__ == '__main__':
    app.run(debug=True)