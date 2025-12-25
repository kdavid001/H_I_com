/* FILE: static/script.js */

// --- 1. Global Variables & Helpers ---
// Helper to get the Course ID safely
function getCourseId() {
    const input = document.getElementById('currentCourseId');
    return input ? input.value : null;
}

// --- 2. Tab Switching Logic ---
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    document.getElementById('tab-' + tabName).classList.add('active');

    // Highlight the correct button
    const buttons = document.querySelectorAll('.tab-btn');
    if(tabName === 'summary') buttons[0].classList.add('active');
    if(tabName === 'quiz') buttons[1].classList.add('active');
    if(tabName === 'stats') buttons[2].classList.add('active');
}

// --- 3. Chat Logic ---
async function sendMessage() {
    const courseId = getCourseId();
    if (!courseId) {
        alert("Session Error: Missing Course ID");
        return;
    }

    let input = document.getElementById("userInput");
    let message = input.value.trim();
    if (!message) return;

    let chatBox = document.getElementById("chatBox");

    // 1. Show User Message
    chatBox.innerHTML += `<div class="message user">${message}</div>`;
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // 2. Show Typing Indicator
    let typingId = "typing-" + Date.now();
    chatBox.innerHTML += `<div class="message bot" id="${typingId}">Thinking...</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        // 3. Send to Backend
        let response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                course_id: courseId // <--- CRITICAL: Send ID
            })
        });
        let data = await response.json();

        // 4. Show Bot Response
        document.getElementById(typingId).remove();
        chatBox.innerHTML += `<div class="message bot">${data.response}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        if(document.getElementById(typingId)) document.getElementById(typingId).remove();
        chatBox.innerHTML += `<div class="message bot">⚠️ Error: Could not reach server.</div>`;
        console.error("Error:", error);
    }
}

// --- 4. File Upload Logic (Merged & Fixed) ---
document.getElementById('fileInput').addEventListener('change', async function(e) {
    const files = e.target.files;
    const listContainer = document.getElementById('uploadStatus');

    if (files.length === 0) return;

    // A. Visual Feedback (Show "Pending" status)
    const filesToUpload = [];
    for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // Create visual item
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        const uniqueId = 'file-' + Date.now() + '-' + i;
        fileItem.id = uniqueId;

        fileItem.innerHTML = `<span>📄 ${file.name}</span> <span class="status pending">⏳</span>`;
        listContainer.appendChild(fileItem);

        filesToUpload.push({ file: file, uiId: uniqueId });
    }

    // B. Trigger Upload
    await processUploadQueue(filesToUpload);

    // Clear input so same file can be selected again
    e.target.value = '';
});


// --- 5. New Course / Reset Logic ---
function resetCourse() {
    if(confirm("Start a new session? (This is just a visual reset for the demo)")) {
        document.getElementById("chatBox").innerHTML = `
            <div class="message bot">👋 New session started! Upload a PDF to begin.</div>
        `;
        document.getElementById('uploadStatus').innerHTML = ""; // Clear file list
        switchTab('summary');
    }
}

function startQuiz() {
    alert("Generating Quiz from uploaded notes...");
}

/* FILE: static/script.js - Part to Update */

// --- Helper: Render a File Item with Actions ---
function renderFileItem(id, name, container) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.id = `note-${id}`;

    fileItem.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px; overflow:hidden;">
            <span>📄</span>
            <a href="/api/file/${id}" target="_blank" class="file-name" id="name-${id}" title="Click to view">
                ${name}
            </a>
        </div>
        <div class="actions">
            <button onclick="renameNote(${id}, '${name}')" title="Rename">✏️</button>
            <button onclick="deleteNote(${id})" title="Delete" style="color:#e74c3c;">🗑️</button>
        </div>
    `;
    container.appendChild(fileItem);
}

// --- Updated History Loader ---
window.onload = async function() {
    const courseId = getCourseId();
    if(!courseId) return;

    try {
        const response = await fetch(`/api/history?course_id=${courseId}`);
        const data = await response.json();

        if (data.has_history) {
            // Restore File List (Now using IDs)
            const listContainer = document.getElementById('uploadStatus');
            listContainer.innerHTML = ""; // Clear list first

            if (data.files && data.files.length > 0) {
                data.files.forEach(file => {
                    renderFileItem(file.id, file.name, listContainer);
                });
            }

            // Restore Chat... (Keep existing chat logic)
            if (data.chats.length > 0) {
                const chatBox = document.getElementById("chatBox");
                chatBox.innerHTML = '';
                data.chats.forEach(chat => {
                    const role = chat.is_user ? 'user' : 'bot';
                    chatBox.innerHTML += `<div class="message ${role}">${chat.text}</div>`;
                });
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }
    } catch (e) { console.log("No history found."); }
};

// --- Updated Upload Processor ---
async function processUploadQueue(queue) {
    const courseId = getCourseId();
    // ... (keep FormData creation logic) ...
    const formData = new FormData();
    formData.append('course_id', courseId);
    queue.forEach(item => formData.append('file', item.file));

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            // Clear the "Pending" list items
            document.getElementById('uploadStatus').innerHTML = "";

            // Re-render the list with the confirmed IDs from server
            data.files.forEach(file => {
                renderFileItem(file.id, file.name, document.getElementById('uploadStatus'));
            });

            switchTab('summary');
        } else {
            alert("Upload failed: " + data.error);
        }
    } catch (error) {
        console.error(error);
    }
}

// --- NEW FUNCTIONS: Delete & Rename ---

async function deleteNote(id) {
    if(!confirm("Are you sure you want to delete this note?")) return;

    try {
        const response = await fetch(`/api/note/${id}`, { method: 'DELETE' });

        if (response.ok) {
            // Remove from UI immediately
            document.getElementById(`note-${id}`).remove();
        } else {
            alert("Failed to delete.");
        }
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
            // Update UI
            document.getElementById(`name-${id}`).textContent = newName;
            // Update the onclick event to have the new name for next time
            const btn = document.querySelector(`#note-${id} button[title="Rename"]`);
            btn.setAttribute('onclick', `renameNote(${id}, '${newName}')`);
        } else {
            alert("Failed to rename.");
        }
    } catch (e) { console.error(e); }
}

