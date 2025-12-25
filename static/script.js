/* FILE: script.js */

// --- 1. Tab Switching Logic ---
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show the specific tab content
    document.getElementById('tab-' + tabName).classList.add('active');

    // Add active class to the clicked button (finding by text/onclick would be complex, so we use event target logic or simple index match)
    // Simple approach: Find the button that calls this function with this tabName
    const buttons = document.querySelectorAll('.tab-btn');
    if(tabName === 'summary') buttons[0].classList.add('active');
    if(tabName === 'quiz') buttons[1].classList.add('active');
    if(tabName === 'stats') buttons[2].classList.add('active');
}

// --- 2. New Course / Reset Logic ---
function resetCourse() {
    if(confirm("Start a new course? This will clear current chat and stats.")) {
        // Clear chat
        document.getElementById("chatBox").innerHTML = `
            <div class="message bot">
                👋 New session started! Upload a PDF to begin.
            </div>
        `;
        // Reset File Input
        document.getElementById("fileInput").value = "";
        document.querySelector('.file-upload-btn').textContent = "📄 Upload PDF Material";

        // Reset Stats (Visual only for demo)
        document.querySelector('.good').textContent = "0%";
        document.querySelector('.progress-fill').style.width = "0%";

        // Switch to Summary Tab
        switchTab('summary');
    }
}

// --- 3. Chat & API Logic ---
async function sendMessage() {
    let input = document.getElementById("userInput");
    let message = input.value.trim();
    if (!message) return;

    let chatBox = document.getElementById("chatBox");

    // Append User Message
    chatBox.innerHTML += `<div class="message user">${message}</div>`;
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // Simulate Typing
    let typingId = "typing-" + Date.now();
    chatBox.innerHTML += `<div class="message bot" id="${typingId}">Thinking...</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        // CALL FLASK API (Make sure your app.py is running)
        let response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        let data = await response.json();

        // Remove Typing Indicator
        document.getElementById(typingId).remove();

        // Append Bot Response
        chatBox.innerHTML += `<div class="message bot">${data.response}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        document.getElementById(typingId).remove();
        chatBox.innerHTML += `<div class="message bot">⚠️ Demo Mode: Backend not connected. <br> You said: "${message}"</div>`;
        console.error("Error:", error);
    }
}

// --- 4. File Upload Logic ---
document.getElementById('fileInput').addEventListener('change', function(e) {
    const label = document.querySelector('.file-upload-btn');
    if (e.target.files.length > 0) {
        const fileName = e.target.files[0].name;
        label.textContent = '✓ ' + fileName;
        label.style.background = '#4caf50'; // Green to show success

        // Auto-switch to Summary Tab to show "Processing"
        switchTab('summary');
        document.querySelector('.placeholder-text').textContent = `Processing "${fileName}" via MindSpore...`;
    }
});

function startQuiz() {
    alert("Generating Quiz from uploaded notes...");
    // Logic to trigger quiz generation would go here
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file first.");
        return;
    }

    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append('file', file);

    // Show loading state
    const btnLabel = document.querySelector('.file-upload-btn');
    btnLabel.textContent = "⏳ Uploading...";

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            btnLabel.textContent = "✓ " + data.filename;
            btnLabel.style.background = "#4caf50";

            // Auto-switch to Summary
            switchTab('summary');
            document.querySelector('.placeholder-text').textContent = "File saved securely. MindSpore is processing...";
        } else {
            alert("Upload failed: " + data.error);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Connection error.");
    }
}

// Add this to window.onload to restore session
window.onload = async function() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        if (data.has_history) {
            // Restore the UI state
            document.querySelector('.file-upload-btn').textContent = "✓ " + data.last_file;
            document.querySelector('.file-upload-btn').style.background = "#4caf50";

            // Add a "Welcome Back" message
            document.getElementById("chatBox").innerHTML += `
                <div class="message bot">Welcome back! I've reloaded your notes on <b>${data.last_file}</b>.</div>
            `;
        }
    } catch (e) {
        console.log("No previous history found.");
    }
};