# 🧠 Chokhmah AI | Huawei ICT Competition 2025-2026
### *Personalized Learning Intelligence (PLI) Platform*

![Huawei MindSpore](https://img.shields.io/badge/Powered%20By-Huawei%20MindSpore-c0392b?style=for-the-badge&logo=huawei)
![Python Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask)
![Status](https://img.shields.io/badge/Phase-1%20Prototype-success?style=for-the-badge)

**Chokhmah AI** is an adaptive study companion designed to solve the "Cold Start" problem in education. Unlike traditional tools that require weeks to learn a student's habits, Chokhmah uses **Retrieval-Augmented Imitation Learning** to instantly "imitate" the expert logic found in uploaded course materials, providing immediate, grounded tutoring.

---

## 🚀 Key Features (Phase 1)

* **📚 Intelligent Ingestion:** Drag-and-drop support for **PDF, Word (.docx), and PowerPoint (.pptx)**.
* **🧠 Hybrid RAG Architecture:** Uses local tensor processing (MindSpore-inspired) for data retrieval + Cloud AI for generation.
* **🎯 Targeted Summaries:** Generate full course overviews or ask for specific topics (e.g., *"Summarize only Chapter 3 formulas"*).
* **📊 Heuristic Adaptive Quizzing:**
    * Tracks performance per topic (e.g., "Vectors" vs. "Calculus").
    * Automatically detects "Knowledge Gaps" and recommends specific study actions.
* **♿ Accessibility First:** Built-in **Text-to-Speech** (Read Aloud) and **Voice Input** for hands-free studying.

---

## 🛠️ Tech Stack & Huawei Integration

| Component | Technology Used | Role in Chokhmah |
| :--- | :--- | :--- |
| **Backend Framework** | Python (Flask) | Main application logic and API routing. |
| **AI Processing** | **Huawei MindSpore** (Hybrid) | Tensor operations for text chunking & retrieval logic. |
| **Generative Model** | Google Gemini 2.5 Flash | High-speed inference for natural language generation. |
| **Database** | SQLite (SQLAlchemy) | Stores User Data, Quiz History, and Session Context. |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Responsive UI with real-time markdown rendering. |

---

## ⚙️ Installation Guide for Teammates

Follow these steps to set up the project locally.

### 1. Prerequisite: MindSpore & Drivers
If you are running on **Linux/Ascend Hardware**, install the CANN toolkit first:
* [MindSpore Installation Guide](https://www.mindspore.cn/install/en)
* [CANN Toolkit Download](https://www.hiascend.com/en/software/cann/community)

### 2. Clone the Repository
```bash
git clone [https://github.com/kdavid001/H_I_com.git](https://github.com/kdavid001/H_I_com.git)
cd H_I_com

```

### 3. Create a Virtual Environment (Recommended)

This keeps our dependencies clean. **Note: Python 3.9 is required for the Windows command below.**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```

### 4. Install Dependencies

**⚠️ IMPORTANT: Choose your OS below**

#### 🪟 For Windows Users (Python 3.9)

Run this command first to install MindSpore (CPU Version) correctly:

```bash
pip install [https://ms-release.obs.cn-north-4.myhuaweicloud.com/2.6.0/MindSpore/cpu/x86_64/mindspore-2.6.0-cp39-cp39-win_amd64.whl](https://ms-release.obs.cn-north-4.myhuaweicloud.com/2.6.0/MindSpore/cpu/x86_64/mindspore-2.6.0-cp39-cp39-win_amd64.whl) --trusted-host ms-release.obs.cn-north-4.myhuaweicloud.com -i [https://repo.huaweicloud.com/repository/pypi/simple](https://repo.huaweicloud.com/repository/pypi/simple)

```

*Then, open `requirements.txt`, **remove** the line starting with `mindspore @ ...` (which is for Mac), and run:*

```bash
pip install -r requirements.txt

```

#### 🍎 For Mac (Apple Silicon) Users

The `requirements.txt` is already set up for you. Just run:

```bash
pip install -r requirements.txt

```

### 5. Set up Environment Variables

Create a file named `.env` in the root folder. You need a Google Gemini API Key for the chatbot to work.

```bash
# Create a file named .env and add this line:
GOOGLE_API_KEY=your_actual_api_key_here

```

### 6. Run the Application

```bash
python main.py

```

Open your browser and go to: `http://127.0.0.1:5000`

---

## 📂 Project Structure

* **`main.py`**: The Flask server. Handles routes for Uploads, Chat, and Database logic.
* **`ai_engine.py`**: The "Brain". Contains the **Hybrid Pipeline**:
* `extract_text_from_file`: Handles PDF/DOCX/PPTX.
* `find_best_context`: The Retrieval (RAG) logic.
* `generate_answer`: Connects to LLM.


* **`models.py`**: Database schemas (User, Course, Note, QuizSession).
* **`static/`**:
* `script.js`: Handles Drag&Drop, Voice Logic, and Markdown rendering.
* `style.css`: All visual styling.


* **`templates/`**: HTML files (`index.html`, `quiz_history.html`, etc.).

---

## 🔮 Future Roadmap (Phase 2)

* [ ] **Deep Reinforcement Learning:** Replace heuristic rules with an RL Agent trained via **MindSpore RL**.
* [ ] **OCR Integration:** Use **MindSpore OCR** to read handwritten notes.
* [ ] **Knowledge Graphing:** Visual mapping of concept dependencies.

---

*Built for the Huawei ICT Competition 2025-2026*
