let currentContactPhone = null;
let ws = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    loadContacts();
    setupWebSocket();
});

function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "new_message") {
            // Update sidebar (move to top, etc)
            loadContacts();
            
            // If the message belongs to the active chat, append it
            if (currentContactPhone === data.phone_number) {
                appendMessage(data.message);
                scrollToBottom();
            }
        }
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected. Reconnecting in 3s...");
        setTimeout(setupWebSocket, 3000);
    };
}

async function loadContacts() {
    try {
        const res = await fetch('/api/contacts');
        const contacts = await res.json();
        
        const list = document.getElementById("contact-list");
        list.innerHTML = "";
        
        contacts.forEach(c => {
            const div = document.createElement("div");
            div.className = `contact-item ${currentContactPhone === c.phone_number ? 'active' : ''}`;
            div.onclick = () => selectContact(c.phone_number, c.name, c.is_ai_active);
            
            const badge = c.is_ai_active ? 
                `<span class="badge-ai">🤖 IA</span>` : 
                `<span class="badge-human">👤 Humano</span>`;

            div.innerHTML = `
                <div class="contact-name">${c.name || 'Desconocido'} ${badge}</div>
                <div class="contact-phone">+${c.phone_number}</div>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        console.error("Error loading contacts", e);
    }
}

async function selectContact(phone, name, isAiActive) {
    currentContactPhone = phone;
    
    document.getElementById("empty-state").style.display = "none";
    document.getElementById("chat-area").style.display = "flex";
    
    document.getElementById("active-contact-name").innerText = name || "Desconocido";
    document.getElementById("active-contact-phone").innerText = `+${phone}`;
    
    // Set toggle state
    const toggle = document.getElementById("ai-toggle");
    const label = document.getElementById("ai-status-label");
    toggle.checked = isAiActive;
    label.innerText = isAiActive ? "🤖 IA Activa" : "👤 Modo Humano";
    
    // Highlight sidebar item
    document.querySelectorAll('.contact-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');

    // Load messages
    try {
        const res = await fetch(`/api/contacts/${phone}/messages`);
        const messages = await res.json();
        
        const history = document.getElementById("chat-history");
        history.innerHTML = "";
        
        messages.forEach(msg => appendMessage(msg));
        scrollToBottom();
    } catch (e) {
        console.error("Error loading messages", e);
    }
}

function appendMessage(msg) {
    const history = document.getElementById("chat-history");
    const div = document.createElement("div");
    
    // msg.sender = 'user', 'ai', or 'human'
    let className = 'msg-user';
    if (msg.sender === 'ai') className = 'msg-ai';
    if (msg.sender === 'human') className = 'msg-human';
    
    div.className = `message ${className}`;
    
    const time = new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    div.innerHTML = `
        ${msg.content}
        <span class="msg-time">${time}</span>
    `;
    
    history.appendChild(div);
}

function scrollToBottom() {
    const history = document.getElementById("chat-history");
    history.scrollTop = history.scrollHeight;
}

async function toggleAiMode() {
    if (!currentContactPhone) return;
    
    try {
        const res = await fetch(`/api/contacts/${currentContactPhone}/toggle_ai`, { method: 'POST' });
        const data = await res.json();
        
        const label = document.getElementById("ai-status-label");
        label.innerText = data.is_ai_active ? "🤖 IA Activa" : "👤 Modo Humano";
        
        loadContacts(); // Update badges in sidebar
    } catch (e) {
        console.error("Error toggling AI mode", e);
    }
}

async function sendMessage() {
    if (!currentContactPhone) return;
    
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text) return;
    
    input.value = "";
    
    try {
        await fetch(`/api/contacts/${currentContactPhone}/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
        });
        
        // Note: the websocket will broadcast our message back to us to append it
        // However, if AI is active and we send a manual message, we should probably toggle AI off automatically?
        // For now, the user uses the toggle switch explicitly.
    } catch (e) {
        console.error("Error sending message", e);
    }
}

function handleKeyPress(e) {
    if (e.key === "Enter") {
        sendMessage();
    }
}
