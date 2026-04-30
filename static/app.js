let currentContactPhone = null;
let currentTab = 'crm';
let ws = null;
let logCount = 0;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    loadContacts();
    setupWebSocket();
    startWatchdogSimulation();
    
    // Auto-switch to CRM initially
    switchTab('crm');
});

function switchTab(tabId) {
    currentTab = tabId;
    
    // Update buttons
    const tabs = ['crm', 'marketing', 'telemetry'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const view = document.getElementById(`tab-${t}`);
        const sidebar = document.getElementById(`sidebar-${t}`);
        
        if (t === tabId) {
            btn.classList.add('tab-active');
            btn.classList.remove('text-gray-500');
            view.classList.remove('hidden');
            if (sidebar) sidebar.classList.remove('hidden');
        } else {
            btn.classList.remove('tab-active');
            btn.classList.add('text-gray-500');
            view.classList.add('hidden');
            if (sidebar) sidebar.classList.add('hidden');
        }
    });

    if (tabId === 'marketing') {
        loadMarketingCampaigns();
    }
}

function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        addLog("SYSTEM", "Conexión WebSocket establecida con el Búnker Central.");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "new_message") {
            loadContacts();
            if (currentContactPhone === data.phone_number) {
                appendMessage(data.message);
                scrollToBottom();
            }
            addLog("WATCHDOG", `Nuevo mensaje detectado de +${data.phone_number}`);
        } else if (data.type === "contact_update") {
            loadContacts();
        }
    };

    ws.onclose = () => {
        addLog("WARNING", "WebSocket desconectado. Reintentando en 3s...");
        setTimeout(setupWebSocket, 3000);
    };
}

async function loadContacts() {
    try {
        const res = await fetch('/api/contacts');
        const contacts = await res.json();
        
        const list = document.getElementById("contact-list");
        const countEl = document.getElementById("contact-count");
        list.innerHTML = "";
        countEl.innerText = `${contacts.length} PACIENTES`;

        if (contacts.length === 0) {
            list.innerHTML = '<div class="p-8 text-center text-gray-600 text-[10px] italic">Sin prospectos activos</div>';
            return;
        }

        contacts.forEach(c => {
            const isActive = currentContactPhone === c.phone_number;
            const item = document.createElement("div");
            item.className = `p-4 cursor-pointer border-b border-white/5 transition-all duration-300 ${isActive ? 'bg-clinical-500/10 border-l-4 border-l-clinical-500' : 'hover:bg-white/5 border-l-4 border-l-transparent'}`;
            
            item.onclick = () => selectContact(c);
            
            const specialty = c.role || (c.phone_number.endsWith('0') ? 'Columna Vertebral' : 'Artroscopia');
            const statusBadge = `<span class="text-[8px] px-1.5 py-0.5 rounded font-black uppercase ${c.status === 'COLD_LEAD' ? 'bg-amber-500/10 text-amber-500' : 'bg-green-500/10 text-green-500'}">${c.status || 'PENDING'}</span>`;
            
            item.innerHTML = `
                <div class="flex justify-between items-start mb-1">
                    <span class="text-xs font-bold ${isActive ? 'text-white' : 'text-gray-300'}">${c.name || 'Desconocido'}</span>
                    ${statusBadge}
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-[9px] text-clinical-400 font-mono uppercase tracking-tighter">${specialty}</span>
                    <span class="text-[9px] text-gray-600 font-mono">+${c.phone_number}</span>
                </div>
                <div class="mt-2 flex items-center gap-2">
                    <div class="w-1.5 h-1.5 rounded-full ${c.is_ai_active ? 'bg-clinical-400 animate-pulse' : 'bg-gray-700'}"></div>
                    <span class="text-[8px] text-gray-500 uppercase tracking-widest">${c.is_ai_active ? 'IA Gestionando' : 'Modo Manual'}</span>
                </div>
            `;
            list.appendChild(item);
        });
    } catch (e) {
        addLog("ERROR", `Falla al cargar contactos: ${e.message}`);
    }
}

async function selectContact(contact) {
    currentContactPhone = contact.phone_number;
    
    document.getElementById("empty-state").classList.add("hidden");
    document.getElementById("chat-header").classList.remove("hidden");
    document.getElementById("input-area").classList.remove("hidden");
    
    document.getElementById("active-name").innerText = contact.name || "Desconocido";
    document.getElementById("active-details").innerText = `${contact.role || 'ESPECIALISTA'} | ${contact.hospital || 'CLÍNICA'}`;
    document.getElementById("active-avatar").innerText = (contact.name || "?").charAt(0);
    
    // Update toggle
    const toggle = document.getElementById("ai-toggle");
    const label = document.getElementById("ai-mode-label");
    toggle.checked = contact.is_ai_active;
    label.innerText = contact.is_ai_active ? "IA ACTIVA" : "MODO MANUAL";
    label.className = `text-[9px] font-bold uppercase tracking-tighter ${contact.is_ai_active ? 'text-clinical-400' : 'text-gray-500'}`;
    
    loadContacts();
    loadMessages(contact.phone_number);
    addLog("USER", `Abriendo sesión táctica con ${contact.name || contact.phone_number}`);
}

async function loadMessages(phone) {
    try {
        const res = await fetch(`/api/contacts/${phone}/messages`);
        const messages = await res.json();
        const history = document.getElementById("chat-history");
        history.innerHTML = "";
        messages.forEach(msg => appendMessage(msg));
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
    
    wrapper.className = `flex w-full ${isUser ? 'justify-start' : 'justify-end'} mb-4`;
    const time = new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    let content = '';
    if (isAi) {
        content = `
            <div class="max-w-[85%] bg-carbon-800 border border-clinical-500/20 rounded-2xl p-4 shadow-xl relative">
                <div class="absolute -top-3 left-4 bg-carbon-900 border border-clinical-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <span class="material-symbols-outlined text-[10px] text-clinical-400">smart_toy</span>
                    <span class="text-[8px] font-black text-clinical-400 uppercase tracking-tighter">AI CLINICAL AGENT</span>
                </div>
                <p class="text-sm text-gray-200 leading-relaxed">${msg.content}</p>
                <div class="mt-2 text-[8px] text-gray-600 font-mono text-right">${time}</div>
            </div>
        `;
    } else if (isUser) {
        content = `
            <div class="max-w-[85%] bg-carbon-800 border border-white/5 rounded-2xl p-4 shadow-lg">
                <p class="text-sm text-gray-400 leading-relaxed">${msg.content}</p>
                <div class="mt-2 text-[8px] text-gray-700 font-mono">${time}</div>
            </div>
        `;
    } else {
        content = `
            <div class="max-w-[85%] bg-clinical-500 rounded-2xl p-4 shadow-2xl">
                <p class="text-sm text-white leading-relaxed font-medium">${msg.content}</p>
                <div class="mt-2 text-[8px] text-blue-200 font-mono text-right">${time}</div>
            </div>
        `;
    }
    
    wrapper.innerHTML = content;
    history.appendChild(wrapper);
}

async function sendMessage() {
    if (!currentContactPhone) return;
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text) return;
    
    input.value = "";
    addLog("SYSTEM", `Transmitiendo mensaje manual a +${currentContactPhone}...`);
    
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
        addLog("WATCHDOG", `Modo IA ${data.is_ai_active ? 'ACTIVADO' : 'DESACTIVADO'} para el canal +${currentContactPhone}`);
        loadContacts();
        
        const label = document.getElementById("ai-mode-label");
        label.innerText = data.is_ai_active ? "IA ACTIVA" : "MODO MANUAL";
        label.className = `text-[9px] font-bold uppercase tracking-tighter ${data.is_ai_active ? 'text-clinical-400' : 'text-gray-500'}`;
    } catch (e) {
        console.error(e);
    }
}

async function loadMarketingCampaigns() {
    const grid = document.getElementById("marketing-grid");
    grid.innerHTML = '<div class="p-20 text-center col-span-full opacity-30 italic">Sincronizando con el Motor Creativo...</div>';
    
    try {
        const res = await fetch('/api/marketing/campaigns');
        const campaigns = await res.json();
        grid.innerHTML = "";
        
        campaigns.forEach(camp => {
            const card = document.createElement("div");
            card.className = "bg-carbon-800 border border-white/5 rounded-3xl p-8 shadow-2xl transition-all hover:border-clinical-500/50 group";
            
            const statusColor = camp.status === 'APPROVED' ? 'text-green-500 bg-green-500/10' : 'text-amber-500 bg-amber-500/10';
            
            card.innerHTML = `
                <div class="flex justify-between items-start mb-6">
                    <span class="text-[10px] font-mono ${statusColor} px-3 py-1 rounded-full border border-current/20">${camp.status}</span>
                    <span class="text-[10px] text-gray-500 font-mono tracking-widest">${camp.target_region}</span>
                </div>
                <h3 class="text-xl font-black text-white mb-4 group-hover:text-clinical-400 transition-colors">${camp.copy_headline}</h3>
                <p class="text-sm text-gray-400 mb-8 leading-relaxed">${camp.copy_body}</p>
                
                <div class="bg-black/50 rounded-2xl p-4 mb-8 border border-white/5">
                    <div class="text-[9px] font-black text-gray-600 uppercase mb-2">Visual Prompt (Nano Banana)</div>
                    <p class="text-[11px] font-mono text-clinical-100 italic">"${camp.nano_banana_prompt}"</p>
                </div>
                
                <div class="rounded-2xl overflow-hidden mb-8 border border-white/5 relative aspect-video">
                    <img src="${camp.image_url}" class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-700"/>
                    <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end p-6">
                        <div class="text-[10px] text-white font-mono opacity-0 group-hover:opacity-100 transition-opacity">ASSET_PREVIEW_READY</div>
                    </div>
                </div>
                
                <div class="flex gap-4">
                    <button class="flex-1 bg-clinical-500 text-white text-[10px] font-black py-3 rounded-xl uppercase tracking-widest hover:bg-clinical-400 transition-all">Aprobar para Instagram</button>
                    <button class="flex-1 border border-white/10 text-gray-400 text-[10px] font-black py-3 rounded-xl uppercase tracking-widest hover:bg-white/5 transition-all">Refinar Prompt</button>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        addLog("ERROR", `Falla en el Motor de Marketing: ${e.message}`);
    }
}

function addLog(type, message) {
    const containers = [document.getElementById("watchdog-logs"), document.getElementById("fullscreen-logs")];
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
    
    const colors = {
        SYSTEM: 'text-gray-500',
        WATCHDOG: 'text-clinical-400',
        USER: 'text-white',
        WARNING: 'text-amber-500',
        ERROR: 'text-red-500'
    };

    containers.forEach(container => {
        if (!container) return;
        const line = document.createElement("div");
        line.className = `log-line mb-1 ${colors[type] || 'text-gray-400'}`;
        line.innerHTML = `<span class="opacity-30">[${time}]</span> <span class="font-bold">[${type}]</span> ${message}`;
        container.prepend(line);
        
        if (container.children.length > 50) container.lastChild.remove();
    });
}

function startWatchdogSimulation() {
    const events = [
        ["WATCHDOG", "Analizando sentimientos en hilo +52..."],
        ["SYSTEM", "Resiliency Check: 4 nodos activos."],
        ["WATCHDOG", "Generando borrador de seguimiento para Dr. García."],
        ["SYSTEM", "Sincronización de base de datos completada."],
        ["WATCHDOG", "Alerta: Intención de compra detectada en lead 0982."],
        ["SYSTEM", "Gemini-2.5-Flash respondiendo en 1.2s"]
    ];
    
    setInterval(() => {
        if (Math.random() > 0.7) {
            const ev = events[Math.floor(Math.random() * events.length)];
            addLog(ev[0], ev[1]);
        }
    }, 4000);
}

function scrollToBottom() {
    const history = document.getElementById("chat-history");
    history.scrollTop = history.scrollHeight;
}

function closeOverlay() {
    document.getElementById("overlay").classList.add("hidden");
}
