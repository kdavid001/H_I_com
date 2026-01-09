// --- Global Variables & State ---
let quizState = {
    total: 0,
    current: 0,
    difficulty: 'Medium',
    topic: '',
    sessionId: null,
    active: false
};

function getCourseId() {
    const input = document.getElementById('currentCourseId');
    return input ? input.value : null;
}

function scrollToBottom() {
    var chatBox = document.getElementById("chatBox");
    if(chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

// --- Tab & UI Logic ---
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    const tab = document.getElementById('tab-' + tabName);
    if(tab) tab.classList.add('active');

    const buttons = document.querySelectorAll('.tab-btn');
    if(buttons.length > 0) {
        if(tabName === 'summary') buttons[0].classList.add('active');
        if(tabName === 'quiz') buttons[1].classList.add('active');
        if(tabName === 'stats') buttons[2].classList.add('active');
    }
        if (tabName === 'stats') {
        loadStats(); // <--- Trigger the calculation
    }
}


// ---UPDATED appendMessage FUNCTION ---
function appendMessage(text, sender) {
    const chatBox = document.getElementById('chatBox');
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);

    // CASE A: Saved Quiz Data
    if (typeof text === 'string' && text.includes("[QUIZ_DATA]")) {
        try {
            const quizJson = JSON.parse(text.replace("[QUIZ_DATA]", "").trim());
            renderInteractiveQuiz(quizJson, msgDiv);
            chatBox.appendChild(msgDiv);
            scrollToBottom();
            return;
        } catch (e) {
            console.error("Error parsing history quiz:", e);
        }
    }

    // CASE B: Live API Response (Object)
    else if (typeof text === 'object' && text !== null) {
        if (text.question) {
            renderInteractiveQuiz(text, msgDiv);
        } else {
             msgDiv.innerText = "⚠️ Invalid Quiz Object";
        }
    }

    // CASE C: Normal Text (Fixed)
    else {
        // Render Text
        if (sender === 'bot') {
            msgDiv.innerHTML = marked.parse(text);

            const btn = document.createElement("button");
            btn.innerHTML = "🔊"; // Or use an SVG icon
            btn.className = "voice-btn"; // Add CSS for this class!
            btn.style.marginLeft = "10px";
            btn.style.cursor = "pointer";
            btn.style.border = "none";
            btn.style.background = "transparent";

            // On Click -> Read Aloud
            btn.onclick = () => speakText(text);

            msgDiv.appendChild(btn);

            // OPTIONAL: Auto-speak immediately - will set for Blind people
            // speakText(text);

        } else {
            msgDiv.innerText = text;
        }
    }

    chatBox.appendChild(msgDiv);
    scrollToBottom();
}
function speakText(text) {
    window.speechSynthesis.cancel();

    // Create a temporary div to strip HTML tags
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = marked.parse(text); // Ensure markdown is parsed first
    const cleanText = tempDiv.innerText;

    const utterance = new SpeechSynthesisUtterance(cleanText);

    // TWEAK 1: Speed and Pitch for natural flow
    utterance.rate = 1.0;
    utterance.pitch = 1.05;

    // TWEAK 2: Find the "Premium" Browser Voice
    const voices = window.speechSynthesis.getVoices();

    // Priority List: Look for "Google", then "Premium", then "Samantha" (Mac)
    const preferredVoice = voices.find(v =>
        v.name.includes("Google US English") ||
        v.name.includes("Samantha") ||
        v.name.includes("Natural")
    );

    if (preferredVoice) {
        utterance.voice = preferredVoice;
        console.log("Using Voice:", preferredVoice.name); // Check console to see what it picked
    }

    window.speechSynthesis.speak(utterance);
}
// This function fixes the history when you reload the page
window.onload = function() {
    // Scroll to bottom
    scrollToBottom();

    // Parse Markdown for existing history messages
    const botMessages = document.querySelectorAll('.message.bot');

    botMessages.forEach(msg => {
        if (msg.classList.contains('quiz-bubble') || msg.querySelector('button')) {
            return; // Skip quizzes
        }

        // If it contains the raw QUIZ tag, render it as a quiz
        if (msg.innerText.includes("[QUIZ_DATA]")) {
            const rawText = msg.innerText;
            msg.innerText = ""; // Clear raw text
            try {
                const quizJson = JSON.parse(rawText.replace("[QUIZ_DATA]", "").trim());
                renderInteractiveQuiz(quizJson, msg);
            } catch(e) { console.error("History Parse Error", e); }
        }
        // Otherwise, it's a text message -> Convert Markdown to HTML
        else {
            if (!msg.innerHTML.includes("<p>")) {
                msg.innerHTML = marked.parse(msg.innerText);
            }
        }
    });
};
async function sendMessage() {
    const courseId = getCourseId();
    if (!courseId) return;

    let input = document.getElementById("userInput");
    let message = input.value.trim();
    if (!message) return;

    // Get checked notes
    const checkboxes = document.querySelectorAll('.note-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.value));

    appendMessage(message, 'user');
    input.value = "";

    const loadingId = "loading-" + Date.now();
    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML += `<div class="message bot" id="${loadingId}">Thinking...</div>`;
    scrollToBottom();

    try {
        let response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                course_id: courseId,
                note_ids: selectedIds
            })
        });
        let data = await response.json();

        document.getElementById(loadingId).remove();

        if (data.is_quiz) {
            appendMessage(data.response, 'bot');
        } else {
            appendMessage(data.response, 'bot');
        }

    } catch (error) {
        if(document.getElementById(loadingId)) document.getElementById(loadingId).remove();
        appendMessage("⚠️ Error: Could not reach server.", 'bot');
    }
}

// --- Quiz Logic (Session & Rendering) ---

function startQuiz() {
    document.getElementById('quiz-modal').style.display = 'flex';
}

function closeQuizModal() {
    document.getElementById('quiz-modal').style.display = 'none';
}

function renderInteractiveQuiz(quizData, containerDiv) {
    containerDiv.style.backgroundColor = "#f8f9fa";
    containerDiv.style.border = "1px solid #e9ecef";
    containerDiv.style.maxWidth = "85%";
    containerDiv.style.borderRadius = "12px";
    containerDiv.style.padding = "15px";

    const title = document.createElement('strong');
    title.innerText = "🧠 " + quizData.question;
    title.style.display = "block";
    title.style.marginBottom = "15px";
    title.style.color = "#333";
    containerDiv.appendChild(title);

    const optionsDiv = document.createElement('div');
    optionsDiv.style.display = "flex";
    optionsDiv.style.flexDirection = "column";
    optionsDiv.style.gap = "10px";

    quizData.options.forEach(option => {
        const btn = document.createElement('button');
        btn.innerText = option;
        btn.style.padding = "10px 15px";
        btn.style.border = "1px solid #ced4da";
        btn.style.borderRadius = "8px";
        btn.style.background = "white";
        btn.style.color = "#000000";
        btn.style.fontWeight = "500";
        btn.style.cursor = "pointer";
        btn.style.textAlign = "left";
        btn.style.fontSize = "14px";
        btn.style.transition = "all 0.2s";

        btn.onclick = async function() {
            const allBtns = optionsDiv.querySelectorAll('button');
            allBtns.forEach(b => b.disabled = true);

            const isCorrect = option.includes(quizData.answer);
            if (isCorrect) {
                btn.style.backgroundColor = "#d4edda";
                btn.style.borderColor = "#28a745";
                btn.innerText += " ✅";
            } else {
                btn.style.backgroundColor = "#f8d7da";
                btn.style.borderColor = "#dc3545";
                btn.innerText += " ❌";
                allBtns.forEach(b => {
                    if (b.innerText.includes(quizData.answer)) {
                        b.style.backgroundColor = "#d4edda";
                        b.style.fontWeight = "bold";
                    }
                });
            }

            if (quizState.active && quizState.sessionId) {
                try {
                    await fetch('/api/quiz/submit', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            session_id: quizState.sessionId,
                            question: quizData.question,
                            selected: option,
                            correct: quizData.answer,
                            difficulty: quizState.difficulty
                        })
                    });
                } catch (e) { console.error(e); }
            }

            if (quizState.active) {
                setTimeout(() => fetchNextQuestion(), 1500);
            }
        };
        optionsDiv.appendChild(btn);
    });
    containerDiv.appendChild(optionsDiv);
}

async function startCustomQuiz() {
    const count = parseInt(document.getElementById('quiz-count').value);
    const difficulty = document.querySelector('input[name="difficulty"]:checked').value;
    const topic = document.getElementById('quiz-topic').value;
    const courseId = getCourseId();

    try {
        const res = await fetch('/api/quiz/start_session', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                course_id: courseId,
                custom_topic: topic // ADD THIS
    })
});
        const data = await res.json();

        quizState = {
            total: count, current: 0, difficulty: difficulty,
            topic: topic, sessionId: data.session_id, active: true
        };

        closeQuizModal();
        appendMessage(`🏁 Starting "${data.name}" (${count} Qs)...`, 'bot');
        await fetchNextQuestion();
    } catch(e) {
        alert("Error starting quiz session");
    }
}

async function fetchNextQuestion() {
    if (quizState.current >= quizState.total) {
        finishQuizSession();
        return;
    }
    quizState.current++;

    const loadingId = 'loading-' + Date.now();
    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML += `<div class="message bot quiz-bubble" id="${loadingId}">Generating Q${quizState.current}...</div>`;
    scrollToBottom();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: "/quiz",
                course_id: getCourseId(),
                difficulty: quizState.difficulty,
                custom_topic: quizState.topic
            })
        });
        const data = await response.json();
        document.getElementById(loadingId).remove();

        if (data.is_quiz) renderQuizForSession(data.response);

    } catch (e) { console.error(e); }
}

function renderQuizForSession(quizData) {
    const chatBox = document.getElementById('chatBox');
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'bot', 'quiz-bubble');
    renderInteractiveQuiz(quizData, msgDiv);
    chatBox.appendChild(msgDiv);
    scrollToBottom();
}

function finishQuizSession() {
    quizState.active = false;
    const bubbles = document.querySelectorAll('.quiz-bubble');
    bubbles.forEach(el => el.remove());
    appendMessage("✅ Quiz session finished. Check 'Review Quizzes' to see results.", 'bot');
    alert("🎉 Quiz Complete! Results saved to history.");
}

// --- SUMMARY LOGIC (NEW) ---
async function fetchSummary() {
    const courseId = getCourseId();
    const topicInput = document.getElementById('summary-topic');
    const topic = topicInput ? topicInput.value.trim() : "";

    // User Feedback in Chat
    const loadingId = "loading-" + Date.now();
    const chatBox = document.getElementById("chatBox");

    let loadingText = topic
        ? `Generating summary for "<b>${topic}</b>"...`
        : "Generating full course summary...";

    chatBox.innerHTML += `<div class="message bot" id="${loadingId}">${loadingText} <div class="spinner"></div></div>`;
    scrollToBottom();

    try {
        const res = await fetch('/api/summary', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ course_id: courseId, topic: topic })
        });
        const data = await res.json();

        // Remove Loader
        document.getElementById(loadingId).remove();

        // Render in Chat (appendMessage will handle the Markdown)
        appendMessage(data.summary, 'bot');

    } catch (e) {
        console.error(e);
        if(document.getElementById(loadingId)) document.getElementById(loadingId).remove();
        appendMessage("⚠️ Error generating summary. Please try again.", 'bot');
    }
}


// --- UPLOAD LOGIC ---
// Click Upload
async function handleFileSelect(inputElement) {
    const files = inputElement.files;
    if (files.length === 0) return;
    await processUploadQueue(Array.from(files));
    inputElement.value = '';
}

// Drag & Drop
const dropzone = document.getElementById('dropzone');
if(dropzone) {
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
    });
    dropzone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) await processUploadQueue(Array.from(files));
    });
}

// The Upload Processor
async function processUploadQueue(files) {
    const courseId = getCourseId();
    const formData = new FormData();
    formData.append('course_id', courseId);
    files.forEach(file => formData.append('file', file));

    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = `
        <div style="display:flex; align-items:center; color:#666; font-size:13px;">
            <div class="spinner"></div> 
            <span>Extracting text & processing... please wait.</span>
        </div>
    `;

    try {
        const response = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await response.json();

        statusDiv.innerHTML = "";

        if (response.ok) {
            const listContainer = document.getElementById('fileList');
            if (listContainer.innerHTML.includes("No notes uploaded")) {
                listContainer.innerHTML = "";
            }
            data.files.forEach(file => renderFileItem(file.id, file.name, listContainer));
            switchTab('summary');
        } else {
            alert("Upload failed: " + (data.error || "Unknown error"));
            statusDiv.innerHTML = "";
        }
    } catch (error) {
        console.error(error);
        statusDiv.innerHTML = "<small style='color:red'>⚠️ Connection Error</small>";
    }
}
function renderFileItem(id, name, container) {
    const li = document.createElement('li');
    li.className = 'file-item';
    li.id = `note-${id}`;
    li.innerHTML = `
        <div class="file-info">
            <input type="checkbox" class="note-checkbox" value="${id}" checked>
            <span id="name-${id}" title="${name}">
                ${name.length > 15 ? name.substring(0,15)+'...' : name}
            </span>
        </div>
        <div class="file-actions">
            <button onclick="renameNote(${id}, '${name}')" title="Rename">✏️</button>
            <button onclick="deleteNote(${id})" title="Delete" class="delete-btn">🗑️</button>
        </div>
    `;
    container.appendChild(li);
}

async function deleteNote(id) {
    if(!confirm("Remove this note?")) return;
    try {
        const response = await fetch(`/api/note/${id}`, { method: 'DELETE' });
        if (response.ok) document.getElementById(`note-${id}`).remove();
    } catch (e) { console.error(e); }
}

async function renameNote(id, oldName) {
    const newName = prompt("Enter new filename:", oldName);
    if (!newName || newName === oldName) return;
    try {
        const response = await fetch(`/api/note/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName })
        });
        if (response.ok) {
            const textSpan = document.getElementById(`name-${id}`);
            if(textSpan) {
                textSpan.innerText = newName.length > 15 ? newName.substring(0,15)+'...' : newName;
                textSpan.title = newName;
            }
            const btn = document.querySelector(`#note-${id} button[title="Rename"]`);
            if(btn) btn.setAttribute('onclick', `renameNote(${id}, '${newName}')`);
        }
    } catch (e) { console.error(e); }
}

window.onload = scrollToBottom;


window.onload = function() {
    scrollToBottom();

    const botMessages = document.querySelectorAll('.message.bot');

    botMessages.forEach(msg => {
        if (msg.querySelector('button') || msg.querySelector('.spinner')) {
            return;
        }

        const rawText = msg.innerText;
        if (rawText.includes("[QUIZ_DATA]")) {
            msg.innerText = "";
            try {
                const jsonString = rawText.replace("[QUIZ_DATA]", "").trim();
                const quizJson = JSON.parse(jsonString);
                renderInteractiveQuiz(quizJson, msg);
            } catch (e) {
                console.error("Error restoring quiz:", e);
                msg.innerText = "⚠️ Error loading quiz.";
            }
        }

        else {
            if (!msg.innerHTML.includes("<p>")) {
                msg.innerHTML = marked.parse(rawText);
            }
        }
    });
};


/* --- AUDIO FEATURES ->Still needs some adjustments  --- */

//  SPEECH TO TEXT (User Voice)
let recognition;
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false; // Stop after one sentence
    recognition.lang = 'en-US';

    recognition.onstart = function() {
        document.getElementById('micBtn').style.backgroundColor = "#dc3545"; // Turn Red
        document.getElementById('userInput').placeholder = "Listening...";
    };

    recognition.onend = function() {
        document.getElementById('micBtn').style.backgroundColor = "#6c757d"; // Reset Grey
        document.getElementById('userInput').placeholder = "Ask a question...";
        sendMessage(); // Auto-send when done speaking!
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('userInput').value = transcript;
    };
} else {
    console.log("Web Speech API not supported in this browser.");
}

function toggleRecording() {
    if (recognition) recognition.start();
    else alert("Your browser does not support voice input. Try Chrome/Edge.");
}




async function loadStats() {
    const courseId = getCourseId();
    const statsTab = document.getElementById('tab-stats');

    statsTab.innerHTML = "<em>🔄 Analyzing your performance patterns...</em>";

    try {
        const res = await fetch(`/api/stats?course_id=${courseId}`);
        const data = await res.json();

        if (!data.has_data) {
            statsTab.innerHTML = "<h3>📊 Progress Tracking</h3><p>Take a quiz to see your learning analysis here!</p>";
            return;
        }

        // Render the "Expert Feedback"
        statsTab.innerHTML = `
            <h3>📊 Adaptive Learning Profile</h3>
            
            <div class="stat-item">
                <span class="stat-label">Course Mastery</span>
                <span class="${data.mastery > 70 ? 'good' : 'bad'}">${data.mastery}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${data.mastery}%; background: ${data.mastery > 70 ? '#4caf50' : '#f44336'}"></div>
            </div>
            
            <div class="stat-item" style="margin-top: 15px;">
                <span class="stat-label">⚠️ Detected Gap</span>
                <span class="bad">${data.weak_area}</span>
            </div>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #2196f3;">
                <strong style="color:#1565c0; display:block; margin-bottom:5px;">🤖 AI Tutor Recommendation:</strong>
                <span style="font-size: 13px; color: #333;">${data.recommendation}</span>
            </div>
        `;
    } catch(e) {
        console.error(e);
        statsTab.innerHTML = "Error loading stats.";
    }
}

