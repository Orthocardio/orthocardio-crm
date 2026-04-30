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
        } else if (data.type === "contact_update") {
            loadContacts();
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
            const btn = document.createElement("button");
            const isActive = currentContactPhone === c.phone_number;
            
            btn.className = `w-full text-left px-4 py-4 rounded-lg transition-all duration-200 group flex flex-col gap-1 ${
                isActive 
                ? 'bg-[#0056b3]/20 border border-[#0056b3]/30' 
                : 'hover:bg-white/5 border border-transparent'
            }`;
            
            btn.onclick = () => selectContact(c.phone_number, c.name, c.is_ai_active);
            
            const badge = c.is_ai_active ? 
                `<span class="text-[9px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-black uppercase">IA</span>` : 
                `<span class="text-[9px] bg-gray-500/20 text-gray-400 px-1.5 py-0.5 rounded font-black uppercase">HUM</span>`;

            btn.innerHTML = `
                <div class="flex justify-between items-center w-full">
                    <span class="text-xs font-bold ${isActive ? 'text-white' : 'text-gray-300 group-hover:text-white'} transition-colors">${c.name || 'Desconocido'}</span>
                    ${badge}
                </div>
                <div class="text-[10px] ${isActive ? 'text-blue-300' : 'text-gray-500'} font-medium">+${c.phone_number}</div>
            `;
            list.appendChild(btn);
        });
        
        if (contacts.length === 0) {
            list.innerHTML = `<div class="p-8 text-center text-gray-600 text-xs italic border border-dashed border-white/5 rounded-xl">Sin conversaciones activas</div>`;
        }
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
    const modeText = document.getElementById("ai-mode-text");
    
    toggle.checked = isAiActive;
    label.innerText = isAiActive ? "IA ACTIVA" : "MODO MANUAL";
    label.className = `text-[9px] font-black uppercase tracking-widest ${isAiActive ? 'text-blue-500' : 'text-gray-500'}`;
    modeText.innerText = isAiActive ? "Asistente Inteligente" : "Intervención Humana";
    
    // Refresh sidebar to update active state
    loadContacts();

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
    const wrapper = document.createElement("div");
    
    // msg.sender_type = 'user', 'ai', or 'human'
    const isUser = msg.sender_type === 'user';
    const isAi = msg.sender_type === 'ai';
    
    wrapper.className = `flex w-full ${isUser ? 'justify-start' : 'justify-end'}`;
    
    const time = new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    let contentHtml = '';
    if (isAi) {
        contentHtml = `
            <div class="max-w-[80%] bg-[#1a1a1a] border border-[#0056b3]/20 rounded-2xl p-4 relative shadow-lg">
                <div class="absolute -top-3 left-4 bg-[#131313] px-2 border border-[#0056b3]/20 rounded-full">
                    <span class="text-[9px] font-black text-[#acc7ff] flex items-center gap-1 uppercase tracking-tighter">
                        <span class="material-symbols-outlined text-[12px]">smart_toy</span>
                        AI Clinical Assistant
                    </span>
                </div>
                <p class="text-sm text-gray-200 mt-1 leading-relaxed">${msg.content}</p>
                <div class="text-[9px] text-gray-600 mt-2 text-left font-bold uppercase tracking-widest">${time}</div>
            </div>
        `;
    } else if (isUser) {
        contentHtml = `
            <div class="max-w-[80%] bg-[#1a1a1a] rounded-2xl p-4 border border-white/5 shadow-md">
                <p class="text-sm text-gray-300 leading-relaxed">${msg.content}</p>
                <div class="text-[9px] text-gray-600 mt-2 text-left font-bold uppercase tracking-widest">${time}</div>
            </div>
        `;
    } else {
        // Human reply
        contentHtml = `
            <div class="max-w-[80%] bg-[#0056b3] rounded-2xl p-4 shadow-xl">
                <p class="text-sm text-white leading-relaxed font-medium">${msg.content}</p>
                <div class="text-[9px] text-blue-200 mt-2 text-right font-bold uppercase tracking-widest">${time}</div>
            </div>
        `;
    }
    
    wrapper.innerHTML = contentHtml;
    history.appendChild(wrapper);
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
        const modeText = document.getElementById("ai-mode-text");
        
        label.innerText = data.is_ai_active ? "IA ACTIVA" : "MODO MANUAL";
        label.className = `text-[9px] font-black uppercase tracking-widest ${data.is_ai_active ? 'text-blue-500' : 'text-gray-500'}`;
        modeText.innerText = data.is_ai_active ? "Asistente Inteligente" : "Intervención Humana";
        
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
    } catch (e) {
        console.error("Error sending message", e);
    }
}

function handleKeyPress(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}
