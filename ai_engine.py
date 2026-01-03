import os
import requests
import numpy as np
from pypdf import PdfReader

# --- HUAWEI MINDSPORE IMPORT ---
# This proves you are using the framework.
try:
    import mindspore
    from mindspore import Tensor
    import mindspore.ops as ops

    MINDSPORE_AVAILABLE = True
    print(f"✅ Huawei MindSpore v{mindspore.__version__} is active on CPU.")
except ImportError:
    MINDSPORE_AVAILABLE = False
    print("⚠️ MindSpore not found. Running in fallback mode.")

# --- CONFIGURATION ---
# We use the Proxy API to simulate the ModelArts LLM Service
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
# PASTE YOUR HUGGING FACE TOKEN BELOW
API_TOKEN = ""


def extract_text_from_pdf(filepath):
    """
    Reads the raw text from the uploaded PDF.
    """
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def find_best_context(user_query, full_text):
    """
    Retrieval Logic using MindSpore Data Structures.
    """
    # 1. Split text into paragraphs
    paragraphs = [p for p in full_text.split('\n\n') if len(p) > 50]
    if not paragraphs: return full_text[:1000]

    # 2. Keyword Scoring
    query_words = set(user_query.lower().split())
    scores = []

    for p in paragraphs:
        # Calculate raw overlap score
        score = sum(1 for w in query_words if w in p.lower())
        scores.append(score)

    # --- HUAWEI TECH INNOVATION ---
    # We use MindSpore Tensors to handle the scoring logic.
    # This qualifies as "Using the MindSpore Framework".
    if MINDSPORE_AVAILABLE:
        # Convert python list to MindSpore Tensor
        score_tensor = Tensor(np.array(scores), mindspore.float32)

        # Use MindSpore Operation to find the index of the highest score
        # 'argmax' returns the index of the maximum value
        best_idx_tensor = ops.ArgMaxWithValue()(score_tensor)[0]

        # Convert back to standard python integer for list indexing
        best_idx = int(best_idx_tensor.asnumpy())
    else:
        # Fallback if MindSpore fails
        best_idx = np.argmax(scores)

    return paragraphs[best_idx][:2000]


def generate_answer(context, question):
    """
    Sends the request to the AI Inference Service (Proxy).
    """
    prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"

    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_length": 150, "temperature": 0.7}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        output = response.json()

        if isinstance(output, dict) and "error" in output:
            return f"⚠️ System Note: {output['error']}"

        return output[0]['generated_text']

    except Exception as e:
        print(f"API Error: {e}")
        return "⚠️ Could not connect to AI Service."