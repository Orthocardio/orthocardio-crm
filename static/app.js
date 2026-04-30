let currentContactPhone = null;
let currentTab = 'crm';
let currentChannel = 'whatsapp';
let currentView = 'list'; // 'list' or 'pipeline'
let ws = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    loadContacts();
    setupWebSocket();
    startWatchdogSimulation();
    switchTab('crm');
});

function switchTab(tabId) {
    currentTab = tabId;
    const tabs = ['crm', 'marketing', 'telemetry'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const view = document.getElementById(`tab-${t}`);
        if (t === tabId) {
            btn.classList.add('tab-active');
            btn.classList.remove('text-gray-500');
            view.classList.remove('hidden');
        } else {
            btn.classList.remove('tab-active');
            btn.classList.add('text-gray-500');
            view.classList.add('hidden');
        }
    });

    if (tabId === 'marketing') loadMarketingCampaigns();
}

function setListView(view) {
    currentView = view;
    const listBtn = document.getElementById('view-btn-list');
    const pipeBtn = document.getElementById('view-btn-pipeline');
    const chatHist = document.getElementById('chat-history');
    const pipeView = document.getElementById('pipeline-view');
    const inputArea = document.getElementById('input-area');
    const chatHeader = document.getElementById('chat-header');

    if (view === 'pipeline') {
        listBtn.className = 'flex-1 py-1.5 text-[9px] font-black uppercase tracking-tighter bg-carbon-900 text-gray-500 rounded-lg border border-white/5 transition-all';
        pipeBtn.className = 'flex-1 py-1.5 text-[9px] font-black uppercase tracking-tighter bg-clinical-500 text-white rounded-lg transition-all';
        chatHist.classList.add('hidden');
        pipeView.classList.remove('hidden');
        inputArea.classList.add('hidden');
        chatHeader.classList.add('hidden');
        renderPipeline();
    } else {
        pipeBtn.className = 'flex-1 py-1.5 text-[9px] font-black uppercase tracking-tighter bg-carbon-900 text-gray-500 rounded-lg border border-white/5 transition-all';
        listBtn.className = 'flex-1 py-1.5 text-[9px] font-black uppercase tracking-tighter bg-clinical-500 text-white rounded-lg transition-all';
        pipeView.classList.add('hidden');
        chatHist.classList.remove('hidden');
        if (currentContactPhone) {
            inputArea.classList.remove('hidden');
            chatHeader.classList.remove('hidden');
        }
    }
}

function switchChannel(channel) {
    currentChannel = channel;
    const channels = ['whatsapp', 'instagram', 'messenger'];
    channels.forEach(c => {
        const btn = document.getElementById(`chan-${c}`);
        if (c === channel) {
            btn.classList.add('channel-tab-active');
            btn.classList.remove('text-gray-500');
        } else {
            btn.classList.remove('channel-tab-active');
            btn.classList.add('text-gray-500');
        }
    });
    // Filter contacts based on channel (simulated for now)
    loadContacts();
}

function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => addLog("SYSTEM", "Conexión táctica con el Búnker Central establecida.");

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === "new_message") {
                loadContacts();
                if (currentContactPhone === data.phone_number) {
                    appendMessage(data.message);
                    scrollToBottom();
                }
                addLog("WATCHDOG", `Intercepción de mensaje en canal +${data.phone_number}`);
            } else if (data.type === "contact_update") {
                loadContacts();
            }
        } catch (e) {
            console.error("Error procesando WS data", e);
        }
    };

    ws.onclose = () => {
        addLog("WARNING", "Señal perdida. Reintentando reconexión...");
        setTimeout(setupWebSocket, 3000);
    };
}

async function loadContacts() {
    try {
        const res = await fetch('/api/contacts');
        const data = await res.json();
        
        // Fix: Ensure data is an array
        const contacts = Array.isArray(data) ? data : [];
        
        const list = document.getElementById("contact-list");
        list.innerHTML = "";

        if (contacts.length === 0) {
            list.innerHTML = '<div class="p-12 text-center text-gray-700 text-[10px] uppercase tracking-widest italic">Sin nodos detectados en este canal</div>';
            return;
        }

        contacts.forEach(c => {
            const isActive = currentContactPhone === c.phone_number;
            const item = document.createElement("div");
            
            // WhatsApp Web Style classes
            item.className = `flex items-center gap-4 p-4 cursor-pointer border-b border-white/5 transition-all duration-200 ${isActive ? 'bg-carbon-800' : 'hover:bg-carbon-800/40'}`;
            
            item.onclick = () => selectContact(c);
            
            // Icon based on channel
            let channelIcon = 'chat';
            let iconColor = 'text-whatsapp';
            if (c.phone_number.endsWith('1')) { channelIcon = 'photo_camera'; iconColor = 'text-instagram'; }
            if (c.phone_number.endsWith('2')) { channelIcon = 'send'; iconColor = 'text-messenger'; }

            const statusColor = c.status === 'COLD_LEAD' ? 'bg-amber-500' : 'bg-green-500';
            const specialty = c.role || 'Especialista';

            item.innerHTML = `
                <div class="relative flex-shrink-0">
                    <div class="w-12 h-12 rounded-full clinical-gradient border border-white/5 flex items-center justify-center text-clinical-400 font-bold uppercase text-lg shadow-inner">
                        ${(c.name || "?").charAt(0)}
                    </div>
                    <div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 ${statusColor} rounded-full border-2 border-carbon-900"></div>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-baseline mb-0.5">
                        <span class="text-sm font-bold text-white truncate pr-2">${c.name || 'Desconocido'}</span>
                        <span class="text-[9px] text-gray-500 font-mono">14:02</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <div class="flex items-center gap-1.5 overflow-hidden">
                            <span class="material-symbols-outlined text-[12px] ${iconColor}">${channelIcon}</span>
                            <span class="text-[11px] text-gray-500 truncate font-medium">${specialty}</span>
                        </div>
                        ${c.is_ai_active ? '<span class="text-[8px] bg-clinical-500/10 text-clinical-400 px-1 rounded font-black tracking-tighter">IA</span>' : ''}
                    </div>
                </div>
            `;
            list.appendChild(item);
        });

        if (currentView === 'pipeline') renderPipeline(contacts);
    } catch (e) {
        addLog("ERROR", `Error en red de contactos: ${e.message}`);
    }
}

function renderPipeline(contactsArray) {
    if (!contactsArray) {
        fetch('/api/contacts').then(r => r.json()).then(data => renderPipeline(data));
        return;
    }
    
    const stages = {
        'PENDING': document.getElementById('pipe-pending'),
        'COLD_LEAD': document.getElementById('pipe-followup'),
        'HOT_LEAD': document.getElementById('pipe-quote'),
        'CONVERTED': document.getElementById('pipe-won')
    };
    
    // Clear columns
    Object.values(stages).forEach(el => el.innerHTML = "");
    
    contactsArray.forEach(c => {
        const stage = c.status || 'PENDING';
        const container = stages[stage] || stages['PENDING'];
        
        const card = document.createElement("div");
        card.className = "p-4 bg-carbon-800 border border-white/5 rounded-xl shadow-lg hover:border-clinical-500/50 cursor-pointer transition-all";
        card.onclick = () => { setListView('list'); selectContact(c); };
        
        card.innerHTML = `
            <div class="text-[10px] font-bold text-white mb-1">${c.name || 'Desconocido'}</div>
            <div class="text-[9px] text-gray-500 font-mono mb-3">${c.role || 'Especialista'}</div>
            <div class="flex justify-between items-center">
                <span class="text-[8px] text-clinical-400 font-black uppercase tracking-tighter">${c.hospital || 'Nodo Activo'}</span>
                <span class="material-symbols-outlined text-xs text-gray-600">drag_indicator</span>
            </div>
        `;
        container.appendChild(card);
    });
}

async function selectContact(contact) {
    currentContactPhone = contact.phone_number;
    
    document.getElementById("empty-state").classList.add("hidden");
    document.getElementById("chat-header").classList.remove("hidden");
    document.getElementById("input-area").classList.remove("hidden");
    
    document.getElementById("active-name").innerText = contact.name || "Desconocido";
    document.getElementById("active-details").innerText = `${contact.role || 'ESPECIALISTA'} | ${contact.hospital || 'NODO ACTIVO'}`;
    document.getElementById("active-avatar").innerText = (contact.name || "?").charAt(0);
    
    // Icon color update
    let channelIcon = 'chat';
    let iconColor = 'text-whatsapp';
    if (contact.phone_number.endsWith('1')) { channelIcon = 'photo_camera'; iconColor = 'text-instagram'; }
    if (contact.phone_number.endsWith('2')) { channelIcon = 'send'; iconColor = 'text-messenger'; }
    const iconEl = document.getElementById("active-channel-icon");
    iconEl.innerText = channelIcon;
    iconEl.className = `material-symbols-outlined text-[14px] ${iconColor}`;

    // AI toggle
    const toggle = document.getElementById("ai-toggle");
    const label = document.getElementById("ai-mode-label");
    const dot = document.getElementById("ai-indicator-dot");
    toggle.checked = contact.is_ai_active;
    label.innerText = contact.is_ai_active ? "IA ACTIVA" : "MODO MANUAL";
    label.className = `text-[9px] font-black uppercase tracking-widest ${contact.is_ai_active ? 'text-clinical-400' : 'text-gray-500'}`;
    dot.className = `w-2 h-2 rounded-full ${contact.is_ai_active ? 'bg-clinical-500 animate-pulse' : 'bg-gray-700'}`;
    
    loadContacts();
    loadMessages(contact.phone_number);
    addLog("USER", `Abriendo túnel de comunicación con ${contact.name || contact.phone_number}`);
}

async function loadMessages(phone) {
    try {
        const res = await fetch(`/api/contacts/${phone}/messages`);
        const data = await res.json();
        
        // Fix: Robust handling of non-array responses
        if (!Array.isArray(data)) {
            console.warn("Respuesta de mensajes no es un array:", data);
            addLog("ERROR", `Error recuperando historial: El servidor no devolvió una lista.`);
            return;
        }

        const history = document.getElementById("chat-history");
        history.innerHTML = "";
        data.forEach(msg => appendMessage(msg));
        scrollToBottom();
    } catch (e) {
        addLog("ERROR", `Error recuperando historial: ${e.message}`);
    }
}

function appendMessage(msg) {
    const history = document.getElementById("chat-history");
    const wrapper = document.createElement("div");
    const isUser = msg.sender_type === 'user';
    const isAi = msg.sender_type === 'ai';
    const isHuman = msg.sender_type === 'human';
    
    wrapper.className = `flex w-full ${isUser ? 'justify-start' : 'justify-end'} mb-2`;
    const time = new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    let bubbleClass = isUser ? 'bg-carbon-800 text-gray-200 message-bubble-user' : 
                      isAi ? 'bg-carbon-800 border border-clinical-500/20 text-gray-200 message-bubble-ai' : 
                      'bg-clinical-600 text-white message-bubble-human';
    
    let content = `
        <div class="max-w-[75%] px-4 py-2 rounded-2xl shadow-md ${bubbleClass} relative">
            ${isAi ? '<div class="text-[8px] font-black text-clinical-400 mb-1 uppercase flex items-center gap-1"><span class="material-symbols-outlined text-[10px]">smart_toy</span> AI Agent</div>' : ''}
            <p class="text-sm leading-relaxed">${msg.content}</p>
            <div class="text-[9px] ${isHuman ? 'text-blue-200' : 'text-gray-500'} mt-1 text-right font-mono">${time}</div>
        </div>
    `;
    
    wrapper.innerHTML = content;
    history.appendChild(wrapper);
}

async function sendMessage() {
    if (!currentContactPhone) return;
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text) return;
    
    input.value = "";
    addLog("SYSTEM", `Transmitiendo instrucción a +${currentContactPhone}...`);
    
    try {
        await fetch(`/api/contacts/${currentContactPhone}/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
        });
    } catch (e) {
        addLog("ERROR", `Falla en transmisión: ${e.message}`);
    }
}

function handleKeyPress(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

async function toggleAiMode() {
    if (!currentContactPhone) return;
    try {
        const res = await fetch(`/api/contacts/${currentContactPhone}/toggle_ai`, { method: 'POST' });
        const data = await res.json();
        addLog("WATCHDOG", `Modo IA ${data.is_ai_active ? 'ACTIVADO' : 'DESACTIVADO'} para +${currentContactPhone}`);
        loadContacts();
        
        const label = document.getElementById("ai-mode-label");
        const dot = document.getElementById("ai-indicator-dot");
        label.innerText = data.is_ai_active ? "IA ACTIVA" : "MODO MANUAL";
        label.className = `text-[9px] font-black uppercase tracking-widest ${data.is_ai_active ? 'text-clinical-400' : 'text-gray-500'}`;
        dot.className = `w-2 h-2 rounded-full ${data.is_ai_active ? 'bg-clinical-500 animate-pulse' : 'bg-gray-700'}`;
    } catch (e) {
        console.error(e);
    }
}

function addLog(type, message) {
    const container = document.getElementById("watchdog-logs");
    if (!container) return;
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
    const colors = { SYSTEM: 'text-gray-500', WATCHDOG: 'text-clinical-400', USER: 'text-white', WARNING: 'text-amber-500', ERROR: 'text-red-500' };
    
    const line = document.createElement("div");
    line.className = `log-line mb-1 ${colors[type] || 'text-gray-400'}`;
    line.innerHTML = `<span class="opacity-30">[${time}]</span> <span class="font-bold">[${type}]</span> ${message}`;
    container.prepend(line);
    if (container.children.length > 40) container.lastChild.remove();
}

function startWatchdogSimulation() {
    const events = [
        ["WATCHDOG", "Analizando sentimientos en hilo omnicanal..."],
        ["SYSTEM", "Resiliency Engine: 100% Health"],
        ["WATCHDOG", "Interceptando lead desde Instagram Direct."],
        ["SYSTEM", "Sincronización de threads completada."],
        ["WATCHDOG", "IA detectó urgencia clínica en mensaje 04."],
    ];
    setInterval(() => {
        if (Math.random() > 0.8) {
            const ev = events[Math.floor(Math.random() * events.length)];
            addLog(ev[0], ev[1]);
        }
    }, 5000);
}

function scrollToBottom() {
    const history = document.getElementById("chat-history");
    history.scrollTop = history.scrollHeight;
}

function closeOverlay() { document.getElementById("overlay").classList.add("hidden"); }
