let currentNotebook = "";
let savedNotes = [];

// --- NAVIGATION & UI ---

function goHome() {
    currentNotebook = "";
    document.getElementById('notebook-select').value = "";
    document.getElementById('source-panel').classList.add('d-none');
    document.getElementById('audio-panel').classList.add('d-none');
    document.getElementById('custom-player-ui').classList.add('d-none');
    document.getElementById('custom-player-ui').classList.remove('d-flex');
    document.getElementById('generate-audio-btn').classList.remove('d-none');
    document.getElementById('chat-input').disabled = true;
    document.getElementById('send-btn').disabled = true;
    document.getElementById('current-notebook-title').innerText = "Select a notebook to start";
    document.getElementById('chat-box').innerHTML = '<div class="text-center text-muted mt-5"><p>Welcome to GrantheX. Upload a document and start asking questions.</p></div>';
    document.getElementById('guide-summary').innerText = "Upload a document to generate a summary.";
    document.getElementById('guide-questions').innerHTML = '<span class="text-muted small">No questions yet.</span>';
    savedNotes = [];
    renderNotes();
}

function createNotebook() {
    const name = document.getElementById('new-notebook-name').value;
    if (!name) return alert("Enter a name!");

    fetch('/api/create_notebook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
    }).then(res => res.json()).then(data => {
        if (data.status === "success") window.location.reload(); 
    });
}

function loadNotebook() {
    currentNotebook = document.getElementById('notebook-select').value;
    const isSelected = currentNotebook !== "";
    
    document.getElementById('source-panel').classList.toggle('d-none', !isSelected);
    document.getElementById('chat-input').disabled = !isSelected;
    document.getElementById('send-btn').disabled = !isSelected;
    document.getElementById('current-notebook-title').innerText = isSelected ? `Notebook: ${currentNotebook}` : "Select a notebook to start";
    
    document.getElementById('custom-player-ui').classList.add('d-none');
    document.getElementById('custom-player-ui').classList.remove('d-flex');
    document.getElementById('generate-audio-btn').classList.remove('d-none');

    if (isSelected) {
        document.getElementById('audio-panel').classList.remove('d-none');
        fetchGuide();
        fetchHistory(); 
        fetchNotes(); // Load pinned notes
        switchTab('guide'); // Default to guide view
    } else {
        document.getElementById('audio-panel').classList.add('d-none');
        document.getElementById('chat-box').innerHTML = '<div class="text-center text-muted mt-5"><p>Welcome to GrantheX. Upload a document and start asking questions.</p></div>';
    }
}

function switchTab(tabName) {
    const guideTab = document.getElementById('guide-tab');
    const notesTab = document.getElementById('notes-tab');
    const guidePanel = document.getElementById('guide-panel');
    const notesPanel = document.getElementById('notes-panel');

    if (tabName === 'guide') {
        guideTab.classList.add('active');
        notesTab.classList.remove('active');
        guidePanel.classList.remove('d-none');
        notesPanel.classList.add('d-none');
    } else {
        notesTab.classList.add('active');
        guideTab.classList.remove('active');
        notesPanel.classList.remove('d-none');
        guidePanel.classList.add('d-none');
    }
}

// --- SOURCES & OVERVIEWS ---

async function uploadSource() {
    const fileInput = document.getElementById('file-upload');
    if (!fileInput.files[0] || !currentNotebook) return alert("Select a file first.");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const btn = document.querySelector('button[onclick="uploadSource()"]');
    btn.innerText = "Processing...";
    btn.disabled = true;

    try {
        const response = await fetch(`/api/upload/${currentNotebook}`, { method: 'POST', body: formData });
        const data = await response.json();
        alert(data.message || data.error);
        fetchGuide(); 
    } catch (err) {
        alert("Upload failed.");
    } finally {
        btn.innerText = "Upload Source";
        btn.disabled = false;
        fileInput.value = "";
    }
}

async function fetchGuide() {
    document.getElementById('guide-summary').innerText = "Generating summary...";
    document.getElementById('guide-questions').innerHTML = "";
    try {
        const response = await fetch(`/api/guide/${currentNotebook}`);
        const data = await response.json();
        if (data.summary) {
            document.getElementById('guide-summary').innerText = data.summary;
            document.getElementById('guide-questions').innerHTML = data.questions.map(q => 
                `<button class="btn btn-sm btn-outline-secondary text-start" onclick="document.getElementById('chat-input').value='${q.replace(/'/g, "\\'")}'; sendMessage();">${q}</button>`
            ).join('');
        }
    } catch (err) {
        document.getElementById('guide-summary').innerText = "Summary not available.";
    }
}

async function generateAudio() {
    if (!currentNotebook) return;
    const btn = document.getElementById('generate-audio-btn');
    btn.innerText = "⏳ Generating...";
    btn.disabled = true;

    try {
        const response = await fetch(`/api/podcast/${currentNotebook}`, { method: 'POST' });
        const data = await response.json();
        if (data.status === "success") {
            const player = document.getElementById('podcast-player');
            player.src = data.audio_url;
            document.getElementById('custom-player-ui').classList.remove('d-none');
            document.getElementById('custom-player-ui').classList.add('d-flex');
            btn.classList.add('d-none'); 
            player.play();
            document.getElementById('play-icon').innerText = "⏸";
        } else {
            alert("Failed to generate audio.");
        }
    } catch (err) {
        alert("Audio generation error.");
    } finally {
        if (btn) { btn.innerText = "🎧 Generate Deep Dive"; btn.disabled = false; }
    }
}

function exportNotebook() {
    if (!currentNotebook) return;
    window.location.href = `/api/export/${currentNotebook}`;
}

// --- NOTES (PINBOARD) LOGIC ---

async function fetchNotes() {
    try {
        const response = await fetch(`/api/notes/${currentNotebook}`);
        savedNotes = await response.json();
        renderNotes();
    } catch (err) { console.error("Could not load notes."); }
}

async function syncNotes() {
    try {
        await fetch(`/api/notes/${currentNotebook}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: savedNotes })
        });
    } catch (err) { console.error("Could not save notes."); }
}

function pinText(btn) {
    const text = decodeURIComponent(btn.getAttribute('data-text'));
    savedNotes.push(text);
    syncNotes();
    renderNotes();
    switchTab('notes'); // Instantly show the user their pinned note
    
    const original = btn.innerHTML;
    btn.innerHTML = "✅ Pinned";
    setTimeout(() => btn.innerHTML = original, 2000);
}

function addCustomNote() {
    const input = document.getElementById('new-note-text');
    const text = input.value.trim();
    if (!text) return;
    
    savedNotes.push(text);
    syncNotes();
    renderNotes();
    input.value = "";
}

function deleteNote(index) {
    savedNotes.splice(index, 1);
    syncNotes();
    renderNotes();
}

function renderNotes() {
    const container = document.getElementById('notes-container');
    if (savedNotes.length === 0) {
        container.innerHTML = '<div class="text-center text-muted small mt-4">No saved notes yet. Pin responses from the chat!</div>';
        return;
    }
    
    container.innerHTML = savedNotes.map((note, index) => `
        <div class="note-card border rounded p-3 shadow-sm markdown-body small">
            <button class="btn btn-sm btn-danger py-0 px-2 delete-note-btn" onclick="deleteNote(${index})" title="Delete Note">×</button>
            ${marked.parse(note)}
        </div>
    `).reverse().join(''); // Reverse to show newest at top

    if (window.MathJax) {
        MathJax.typesetPromise([container]).catch(err => console.log('MathJax error:', err));
    }
}

// --- CHAT & HISTORY ---

async function fetchHistory() {
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '<div class="text-center text-muted mt-5">Loading history...</div>';
    try {
        const response = await fetch(`/api/history/${currentNotebook}`);
        const history = await response.json();
        chatBox.innerHTML = '';
        if (history.length === 0) {
            chatBox.innerHTML = '<div class="text-center text-muted mt-5"><p>Welcome to GrantheX. Upload a document and start asking questions.</p></div>';
        } else {
            history.forEach(msg => appendMessage(msg.role, msg.content));
        }
    } catch (err) {
        chatBox.innerHTML = '<div class="text-center text-danger mt-5">Failed to load history.</div>';
    }
}

function appendMessage(role, content) {
    const chatBox = document.getElementById('chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = role === 'user' ? "mb-4 text-end msg-container" : "mb-4 text-start msg-container";
    
    const htmlContent = role === 'user' ? content : marked.parse(content);
    const bubbleClass = role === 'user' ? "bg-primary text-white p-3 rounded d-inline-block text-start" : "bg-white border p-3 rounded d-inline-block shadow-sm w-100 markdown-body text-start";
    
    // Build Hover Actions (Added the Pin button!)
    let actionsHtml = `<div class="msg-actions shadow-sm">
        <button class="btn btn-sm btn-light py-0 px-2" onclick="copyText(this)" data-text="${encodeURIComponent(content)}" title="Copy">📋 Copy</button>
        <button class="btn btn-sm btn-light py-0 px-2 border-start" onclick="pinText(this)" data-text="${encodeURIComponent(content)}" title="Pin to Notes">📌 Pin</button>`;
    if (role === 'user') {
        actionsHtml += `<button class="btn btn-sm btn-light py-0 px-2 border-start" onclick="editPrompt(this)" data-text="${encodeURIComponent(content)}" title="Edit">✏️ Edit</button>`;
    }
    actionsHtml += `</div>`;

    msgDiv.innerHTML = `<span class="${bubbleClass}" style="max-width: 90%;">${htmlContent}</span>${actionsHtml}`;
    chatBox.appendChild(msgDiv);
    
    if (window.MathJax && window.MathJax.typesetPromise) {
        MathJax.typesetPromise([msgDiv]).catch(err => console.log('MathJax error:', err));
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query || !currentNotebook) return;

    appendMessage('user', query);
    input.value = '';
    
    const chatBox = document.getElementById('chat-box');
    const loadingId = "loading-" + Date.now();
    chatBox.innerHTML += `<div id="${loadingId}" class="mb-3 text-start"><span class="bg-secondary text-white p-2 rounded d-inline-block">GrantheX is thinking...</span></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch(`/api/chat/${currentNotebook}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await response.json();
        document.getElementById(loadingId).remove();
        if (data.answer) appendMessage('assistant', data.answer);
    } catch (err) {
        document.getElementById(loadingId).innerText = "Error connecting to Groq API.";
    }
}

// --- CUSTOM AUDIO SCRUBBER & HELPERS ---

function copyText(btn) {
    const text = decodeURIComponent(btn.getAttribute('data-text'));
    navigator.clipboard.writeText(text);
    const original = btn.innerHTML;
    btn.innerHTML = "✅ Copied";
    setTimeout(() => btn.innerHTML = original, 2000);
}

function editPrompt(btn) {
    const text = decodeURIComponent(btn.getAttribute('data-text'));
    const input = document.getElementById('chat-input');
    input.value = text;
    input.focus();
}

function formatTime(seconds) {
    if (isNaN(seconds) || !isFinite(seconds)) return "0:00";
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
}

function toggleAudio() {
    const player = document.getElementById('podcast-player');
    const icon = document.getElementById('play-icon');
    if (player.paused) {
        player.play();
        icon.innerText = "⏸"; icon.style.marginLeft = "0px"; 
    } else {
        player.pause();
        icon.innerText = "▶"; icon.style.marginLeft = "2px"; 
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const player = document.getElementById('podcast-player');
    const scrubber = document.getElementById('audio-scrubber');
    
    player.addEventListener('loadedmetadata', () => {
        scrubber.max = Math.floor(player.duration);
        document.getElementById('audio-duration').innerText = formatTime(player.duration);
    });
    player.addEventListener('timeupdate', () => {
        scrubber.value = Math.floor(player.currentTime);
        document.getElementById('audio-current-time').innerText = formatTime(player.currentTime);
    });
    scrubber.addEventListener('input', () => {
        player.currentTime = scrubber.value;
    });
    player.addEventListener('ended', () => {
        document.getElementById('play-icon').innerText = "▶";
        document.getElementById('play-icon').style.marginLeft = "2px";
        scrubber.value = 0;
        document.getElementById('audio-current-time').innerText = "0:00";
    });
});