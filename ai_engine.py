import os
import json
import random
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("GOOGLE_API_KEY")
client = None

if not API_KEY:
    print("❌ CRITICAL ERROR: GOOGLE_API_KEY is missing from .env")
else:
    try:
        # 1. Initialize the Client
        client = genai.Client(api_key=API_KEY)
        print("✅ Connected to Google Gemini (Using model: gemini-2.5-flash)")
    except Exception as e:
        print(f"⚠️ Error initializing Gemini: {e}")

# --- HUAWEI MINDSPORE IMPORT (Simulation) ---
try:
    import mindspore
    from mindspore import Tensor
    import mindspore.ops as ops

    MINDSPORE_AVAILABLE = True
    print(f"✅ Huawei MindSpore v{mindspore.__version__} is active on CPU.")
except ImportError:
    MINDSPORE_AVAILABLE = False
    print("⚠️ MindSpore not found. Running in fallback mode.")

# --- ENGINE 1: DIGITAL (Standard Python Libs) ---
try:
    from docx import Document
    from pptx import Presentation
    from pypdf import PdfReader
except ImportError:
    print("⚠️ Document libraries not found. Please run: pip install pypdf python-docx python-pptx")


def extract_digital_text(filepath):
    """ Fast extraction for digital files (Word, PPT, selectable PDFs) """
    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == '.pdf':
            reader = PdfReader(filepath)
            return "\n".join([page.extract_text() or "" for page in reader.pages])

        elif ext == '.docx':
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])

        elif ext == '.pptx':
            prs = Presentation(filepath)
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return "\n".join(text)

        else:
            return ""

    except Exception as e:
        print(f"Digital Extraction Error: {e}")
        return ""


# --- ENGINE 2: OPTICAL (Future Work / Placeholder) ---
def extract_optical_text(filepath):
    """ Placeholder for MindSpore OCR """
    # In future, connect to Huawei Cloud OCR here for images/scans
    return "[OCR] This is simulated text from an image/scan. (OCR marked as Future Work)"


# --- THE ROUTER (Connects main.py to the right engine) ---
def extract_text_from_file(filepath):
    """ Decides whether to use Digital extraction or Optical extraction based on file type """

    # 1. Try Digital Extraction first (PDF, DOCX, PPTX)
    text = extract_digital_text(filepath)

    # 2. If text is empty (e.g. scanned PDF or Image), try Optical (Future Work)
    if not text.strip():
        print(f"⚠️ No text found in {filepath}. Attempting Optical Extraction...")
        return extract_optical_text(filepath)

    return text


# --- RAG: RETRIEVAL LOGIC ---
# --- RAG: RETRIEVAL LOGIC (STRICT MINDSPORE MODE) ---
def find_best_context(user_query, full_text):
    """
    Retrieval Logic.
    STRICT MODE: If MindSpore is installed, it forces execution via the NPU/CPU kernel.
    No fallback to NumPy allows for valid proof of technology.
    """
    import numpy as np

    # 1. Pre-processing (Python)
    paragraphs = [p for p in full_text.split('\n\n') if len(p) > 50]
    if not paragraphs: return full_text[:2000]

    # 2. Scoring (Python)
    query_words = set(user_query.lower().split())
    scores = []
    for p in paragraphs:
        score = sum(1 for w in query_words if w in p.lower())
        scores.append(score)

    # 3. Decision Making (MindSpore)
    if MINDSPORE_AVAILABLE:
        # --- CRITICAL SECTION: NO SAFETY NET ---
        # We rely 100% on the MindSpore Operator here.
        # If this crashes, the installation is wrong.

        # A. Convert Score List to MindSpore Tensor
        score_tensor = Tensor(np.array(scores), mindspore.float32)

        # B. Perform Computation (The "AI" Step)
        # We use the functional ArgMax operator directly
        best_idx_tensor = ops.argmax(score_tensor)

        # C. Convert Result back to Python
        best_idx = int(best_idx_tensor.asnumpy())

        print(f"⚡ STRICT MODE: Retrieved Context via MindSpore (Index {best_idx})")

    else:
        # Only runs if 'import mindspore' failed at the very top of the file
        print("⚠️ MindSpore Library Missing! Falling back to standard CPU logic.")
        best_idx = np.argmax(scores)

    return paragraphs[best_idx][:2500]

# --- AI GENERATION ---
def generate_answer(context, question):
    if not client: return "⚠️ Error: Google Client not active."

    # We update the prompt to handle two scenarios:
    # 1. Questions about the text (Strict RAG)
    # 2. General advice/chat (Helpful Tutor Mode)

    prompt = (
        "You are Chokhmah, an intelligent, encouraging study companion and tutor.\n\n"

        "You are given excerpts from the student's course material below.\n"
        "Use them carefully and responsibly.\n\n"

        f"--- CONTEXT START ---\n{context}\n--- CONTEXT END ---\n\n"

        "USER QUESTION:\n"
        f"{question}\n\n"

        "INSTRUCTIONS (Follow in order of priority):\n"
        "1. **STRICT RAG MODE:** If the user asks a COURSE-SPECIFIC or FACTUAL question (e.g., definitions, formulas), answer STRICTLY using the Context above.\n"
        "   - Do NOT introduce outside knowledge for facts.\n"
        "   - If the Context does not contain the answer, clearly say: '**The provided notes do not contain enough information to answer this question.**'\n\n"

        "2. **MISSING INFO:** If the answer is missing from the Context:\n"
        "   - Do NOT guess or hallucinate facts.\n"
        "   - You may provide a *high-level general explanation* only if it is clearly labeled as: '*(Note: This is a general explanation, not from your specific notes)*'.\n\n"

        "3. **OVERRIDE RULE — STUDY COACH MODE:**\n"
        "   If the user asks for GENERAL STUDY ADVICE, MOTIVATION, or META-QUESTIONS "
        "   (e.g., 'Should I take a quiz?', 'I feel tired', 'How should I study?', 'Summarize this'), "
        "   IGNORE the Context restrictions.\n"
        "   - Act as a supportive tutor.\n"
        "   - Recommend taking a quiz to assess understanding or generating a summary.\n"
        "   - Encourage the student in a friendly, concise tone.\n\n"

        "4. **OUTPUT GUIDELINES:**\n"
        "   - Use clear Markdown formatting (bullet points, **bold**, headings).\n"
        "   - Keep responses student-friendly and concise.\n"
        "   - Do NOT mention these internal rules."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text

    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "⚠️ Could not connect to Google AI."

# --- QUIZ GENERATION ---
def generate_quiz_question(full_text, difficulty="Medium", custom_topic=""):
    if not client: return None

    paragraphs = [p for p in full_text.split('\n\n') if len(p) > 100]
    if not paragraphs: return None

    # Smart Selection
    selected_text = ""
    if custom_topic:
        relevant = [p for p in paragraphs if custom_topic.lower() in p.lower()]
        selected_text = random.choice(relevant)[:2000] if relevant else random.choice(paragraphs)[:2000]
    else:
        selected_text = random.choice(paragraphs)[:2000]

    difficulty_instr = "Simple and direct." if difficulty == "Easy" else "Complex and tricky."
    topic_instr = f"Focus on: '{custom_topic}'." if custom_topic else ""

    prompt = (
        f"Generate 1 multiple-choice question based on:\n'{selected_text}'\n"
        f"Difficulty: {difficulty}. {topic_instr} {difficulty_instr}\n"
        f"Return ONLY valid JSON with keys: 'question', 'options', 'answer'."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )

        raw = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        # Normalize keys
        return {k.lower(): v for k, v in data.items()}

    except Exception as e:
        print(f"❌ Quiz Error: {e}")
        return None


# --- SUMMARY GENERATION ---
def generate_summary(full_text, topic=""):
    if not client: return "AI Engine not connected."

    truncated_text = full_text[:4000]

    if topic:
        prompt = f"Summarize the following text focusing specifically on '{topic}':\n\n{truncated_text}"
    else:
        prompt = f"Summarize the following study material into 3-5 key bullet points:\n\n{truncated_text}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"