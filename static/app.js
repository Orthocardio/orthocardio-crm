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
        const contacts = Array.isArray(data) ? data : [];
        
        const list = document.getElementById("contact-list");
        list.innerHTML = "";

        if (contacts.length === 0) {
            list.innerHTML = '<div class="p-12 text-center text-gray-700 text-[10px] uppercase tracking-widest italic">Sin nodos detectados</div>';
            return;
        }

        contacts.forEach(c => {
            const isActive = currentContactPhone === c.phone_number;
            const item = document.createElement("div");
            item.className = `flex items-center gap-4 p-4 cursor-pointer border-b border-white/5 transition-all duration-200 ${isActive ? 'bg-carbon-800' : 'hover:bg-carbon-800/40'}`;
            item.onclick = () => selectContact(c);
            
            let channelIcon = 'chat';
            let iconColor = 'text-whatsapp';
            if (c.phone_number.endsWith('1')) { channelIcon = 'photo_camera'; iconColor = 'text-instagram'; }
            if (c.phone_number.endsWith('2')) { channelIcon = 'send'; iconColor = 'text-messenger'; }

            const statusColor = c.status === 'COLD_LEAD' ? 'bg-amber-500' : (c.status === 'HOT_LEAD' ? 'bg-red-500' : 'bg-green-500');
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
    
    Object.values(stages).forEach(el => { if(el) el.innerHTML = ""; });
    
    contactsArray.forEach(c => {
        const stage = c.status || 'PENDING';
        const container = stages[stage] || stages['PENDING'];
        if (!container) return;
        
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

async function loadMarketingCampaigns() {
    const grid = document.getElementById("marketing-grid");
    if (!grid) return;
    
    grid.innerHTML = '<div class="p-20 text-center col-span-full opacity-30 italic">Sincronizando con el Motor Creativo...</div>';
    
    try {
        const res = await fetch('/api/marketing/campaigns');
        const campaigns = await res.json();
        
        grid.innerHTML = "";
        campaigns.forEach(camp => {
            const card = document.createElement("div");
            card.className = "glass rounded-3xl overflow-hidden border border-white/5 group hover:border-clinical-500/50 transition-all duration-500";
            card.innerHTML = `
                <div class="relative h-48 overflow-hidden">
                    <img src="${camp.image_url}" class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700 scale-110 group-hover:scale-100"/>
                    <div class="absolute inset-0 bg-gradient-to-t from-carbon-900 to-transparent opacity-60"></div>
                    <div class="absolute top-4 right-4 bg-carbon-900/80 backdrop-blur-md px-3 py-1 rounded-full border border-white/10">
                        <span class="text-[8px] font-black text-clinical-400 uppercase tracking-widest">${camp.status}</span>
                    </div>
                </div>
                <div class="p-6">
                    <div class="text-[10px] text-clinical-500 font-black uppercase tracking-widest mb-2">${camp.target_region}</div>
                    <h3 class="text-lg font-bold text-white mb-3 leading-tight">${camp.copy_headline}</h3>
                    <p class="text-[11px] text-gray-500 line-clamp-2 mb-6">${camp.copy_body}</p>
                    
                    <div class="bg-carbon-900 rounded-xl p-4 mb-6 border border-white/5">
                        <div class="flex items-center gap-2 mb-2 text-[9px] text-gray-600 font-mono uppercase">
                            <span class="material-symbols-outlined text-[12px]">auto_awesome</span> Nano Banana Prompt
                        </div>
                        <p class="text-[10px] text-gray-400 italic leading-relaxed">"${camp.nano_banana_prompt}"</p>
                    </div>
                    
                    <div class="flex gap-3">
                        <button class="flex-1 bg-clinical-500 text-white py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-clinical-400 transition-all">Aprobar</button>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        grid.innerHTML = '<div class="p-20 text-center col-span-full text-red-500 text-xs uppercase font-black">Falla en Sincronización</div>';
    }
}

async function selectContact(contact) {
    currentContactPhone = contact.phone_number;
    document.getElementById("empty-state").classList.add("hidden");
    document.getElementById("chat-header").classList.remove("hidden");
    document.getElementById("input-area").classList.remove("hidden");
    document.getElementById("active-name").innerText = contact.name || "Desconocido";
    document.getElementById("active-details").innerText = `${contact.role || 'ESPECIALISTA'} | ${contact.hospital || 'NODO ACTIVO'}`;
    document.getElementById("active-avatar").innerText = (contact.name || "?").charAt(0);
    
    let channelIcon = 'chat';
    let iconColor = 'text-whatsapp';
    if (contact.phone_number.endsWith('1')) { channelIcon = 'photo_camera'; iconColor = 'text-instagram'; }
    if (contact.phone_number.endsWith('2')) { channelIcon = 'send'; iconColor = 'text-messenger'; }
    const iconEl = document.getElementById("active-channel-icon");
    iconEl.innerText = channelIcon;
    iconEl.className = `material-symbols-outlined text-[14px] ${iconColor}`;

    const toggle = document.getElementById("ai-toggle");
    const label = document.getElementById("ai-mode-label");
    const dot = document.getElementById("ai-indicator-dot");
    toggle.checked = contact.is_ai_active;
    label.innerText = contact.is_ai_active ? "IA ACTIVA" : "MODO MANUAL";
    label.className = `text-[9px] font-black uppercase tracking-widest ${contact.is_ai_active ? 'text-clinical-400' : 'text-gray-500'}`;
    dot.className = `w-2 h-2 rounded-full ${contact.is_ai_active ? 'bg-clinical-500 animate-pulse' : 'bg-gray-700'}`;
    
    loadContacts();
    loadMessages(contact.phone_number);
    addLog("USER", `Abriendo túnel con ${contact.name || contact.phone_number}`);
}

async function loadMessages(phone) {
    try {
        const res = await fetch(`/api/contacts/${phone}/messages`);
        const data = await res.json();
        if (!Array.isArray(data)) return;
        const history = document.getElementById("chat-history");
        history.innerHTML = "";
        data.forEach(msg => appendMessage(msg));
        scrollToBottom();
    } catch (e) {
        addLog("ERROR", `Error en historial: ${e.message}`);
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
    let bubbleClass = isUser ? 'bg-carbon-800 text-gray-200' : isAi ? 'bg-carbon-800 border border-clinical-500/20 text-gray-200' : 'bg-clinical-600 text-white';
    wrapper.innerHTML = `<div class="max-w-[75%] px-4 py-2 rounded-2xl shadow-md ${bubbleClass} relative">${isAi ? '<div class="text-[8px] font-black text-clinical-400 mb-1 uppercase flex items-center gap-1"><span class="material-symbols-outlined text-[10px]">smart_toy</span> AI Agent</div>' : ''}<p class="text-sm leading-relaxed">${msg.content}</p><div class="text-[9px] mt-1 text-right font-mono">${time}</div></div>`;
    history.appendChild(wrapper);
}

async function sendMessage() {
    if (!currentContactPhone) return;
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    addLog("SYSTEM", `Transmitiendo a +${currentContactPhone}...`);
    try {
        await fetch(`/api/contacts/${currentContactPhone}/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
        });
    } catch (e) {
        addLog("ERROR", `Falla: ${e.message}`);
    }
}

function handleKeyPress(e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }

async function toggleAiMode() {
    if (!currentContactPhone) return;
    try {
        const res = await fetch(`/api/contacts/${currentContactPhone}/toggle_ai`, { method: 'POST' });
        const data = await res.json();
        addLog("WATCHDOG", `Modo IA ${data.is_ai_active ? 'ACTIVADO' : 'DESACTIVADO'}`);
        loadContacts();
    } catch (e) {}
}

function addLog(type, message) {
    const container = document.getElementById("watchdog-logs");
    if (!container) return;
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
    const line = document.createElement("div");
    line.className = `log-line mb-1 ${type === 'ERROR' ? 'text-red-500' : (type === 'WATCHDOG' ? 'text-clinical-400' : 'text-gray-400')}`;
    line.innerHTML = `<span class="opacity-30">[${time}]</span> <span class="font-bold">[${type}]</span> ${message}`;
    container.prepend(line);
}

function startWatchdogSimulation() {
    setInterval(() => {
        if (Math.random() > 0.9) addLog("WATCHDOG", "Analizando sentimientos clínicos...");
    }, 10000);
}

function scrollToBottom() { const h = document.getElementById("chat-history"); h.scrollTop = h.scrollHeight; }
function closeOverlay() { document.getElementById("overlay").classList.add("hidden"); }
