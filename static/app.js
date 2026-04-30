let currentContactPhone = null;
let currentTab = 'crm';
let currentChannel = 'all'; // 'all', 'whatsapp', 'instagram', 'messenger'
let currentView = 'list'; // 'list' or 'pipeline'
let ws = null;
let allContacts = [];

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    loadContacts();
    setupWebSocket();
    startSwarmFeedSimulation();
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

    if (tabId === 'marketing') loadMarketingPipeline();
    
    // Close mobile menu on tab switch
    const sidebar = document.getElementById("main-sidebar");
    if (sidebar) sidebar.classList.add("-translate-x-full");
}

function toggleMobileMenu() {
    const sidebar = document.getElementById("main-sidebar");
    sidebar.classList.toggle("-translate-x-full");
}

function switchChannel(channel) {
    currentChannel = channel;
    const channels = ['all', 'whatsapp', 'instagram', 'messenger'];
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
    renderContacts();
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
        listBtn.className = 'flex-1 py-1 text-[9px] font-black uppercase rounded-md text-gray-500 transition-all';
        pipeBtn.className = 'flex-1 py-1 text-[9px] font-black uppercase rounded-md bg-clinical-500 text-white transition-all';
        chatHist.classList.add('hidden');
        pipeView.classList.remove('hidden');
        inputArea.classList.add('hidden');
        chatHeader.classList.add('hidden');
        renderPipeline();
    } else {
        pipeBtn.className = 'flex-1 py-1 text-[9px] font-black uppercase rounded-md text-gray-500 transition-all';
        listBtn.className = 'flex-1 py-1 text-[9px] font-black uppercase rounded-md bg-clinical-500 text-white transition-all';
        pipeView.classList.add('hidden');
        chatHist.classList.remove('hidden');
        if (currentContactPhone) {
            inputArea.classList.remove('hidden');
            chatHeader.classList.remove('hidden');
        }
    }
}

function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    ws.onopen = () => addLog("SYSTEM", "SECURE_CONNECTION_ESTABLISHED: Búnker Central Online.");
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "new_message") {
            loadContacts();
            if (currentContactPhone === data.phone_number) {
                appendMessage(data.message);
                scrollToBottom();
            }
            addLog("SWARM", `Interceptado mensaje en nodo +${data.phone_number}`);
        } else if (data.type === "swarm_task") {
            renderSwarmTask(data.agent, data.task);
        }
    };
    ws.onclose = () => setTimeout(setupWebSocket, 3000);
}

async function loadContacts() {
    try {
        const res = await fetch('/api/contacts');
        allContacts = await res.json();
        renderContacts();
        if (currentView === 'pipeline') renderPipeline();
    } catch (e) { addLog("ERROR", `FALLO_RED_CONTACTOS: ${e.message}`); }
}

function renderContacts() {
    const list = document.getElementById("contact-list");
    list.innerHTML = "";
    
    const filtered = allContacts.filter(c => currentChannel === 'all' || c.source_platform === currentChannel);
    
    if (filtered.length === 0) {
        list.innerHTML = '<div class="p-10 text-center text-gray-700 text-[10px] uppercase font-mono italic">No_Leads_Detected</div>';
        return;
    }

    filtered.forEach(c => {
        const isActive = currentContactPhone === c.phone_number;
        const item = document.createElement("div");
        item.className = `flex items-center gap-3 p-3 cursor-pointer border-b border-white/5 transition-all ${isActive ? 'bg-carbon-800' : 'hover:bg-carbon-800/40'}`;
        item.onclick = () => selectContact(c);
        
        let platformIcon = 'chat';
        let iconColor = 'text-whatsapp';
        if (c.source_platform === 'instagram') { platformIcon = 'photo_camera'; iconColor = 'text-instagram'; }
        if (c.source_platform === 'messenger') { platformIcon = 'send'; iconColor = 'text-messenger'; }

        const statusColor = c.status === 'HOT_LEAD' ? 'bg-red-500' : (c.status === 'COLD_LEAD' ? 'bg-amber-500' : 'bg-clinical-500');

        item.innerHTML = `
            <div class="relative flex-shrink-0">
                <div class="w-10 h-10 rounded-lg clinical-gradient border border-white/5 flex items-center justify-center text-clinical-400 font-bold uppercase text-base shadow-inner">
                    ${(c.name || "?").charAt(0)}
                </div>
                <div class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 ${statusColor} rounded-full border-2 border-carbon-900 shadow-lg"></div>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex justify-between items-baseline mb-0.5">
                    <span class="text-[11px] font-bold text-white truncate pr-2 uppercase tracking-tight">${c.name || 'ANÓNIMO'}</span>
                    <span class="text-[8px] text-gray-500 font-mono">14:02</span>
                </div>
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-1.5 overflow-hidden">
                        <span class="material-symbols-outlined text-[10px] ${iconColor}">${platformIcon}</span>
                        <span class="text-[9px] text-gray-500 truncate font-mono uppercase tracking-tighter">${c.role || 'ESPECIALISTA'}</span>
                    </div>
                    ${c.is_ai_active ? '<span class="text-[7px] bg-clinical-500/10 text-clinical-400 px-1 rounded font-black tracking-tighter">IA</span>' : ''}
                </div>
            </div>
        `;
        list.appendChild(item);
    });
}

function renderPipeline() {
    const stages = {
        'PENDING': document.getElementById('pipe-pending'),
        'COLD_LEAD': document.getElementById('pipe-followup'),
        'HOT_LEAD': document.getElementById('pipe-quote'),
        'CONVERTED': document.getElementById('pipe-won')
    };
    
    Object.keys(stages).forEach(k => {
        if(stages[k]) stages[k].innerHTML = "";
        const countEl = document.getElementById(`count-${k.toLowerCase()}`);
        if(countEl) countEl.innerText = allContacts.filter(c => (c.status || 'PENDING') === k).length;
    });
    
    allContacts.forEach(c => {
        const stage = c.status || 'PENDING';
        const container = stages[stage];
        if (!container) return;
        
        const card = document.createElement("div");
        card.className = "p-3 bg-carbon-800 border border-white/5 rounded-lg shadow-sm hover:border-clinical-500/30 cursor-pointer transition-all";
        card.onclick = () => { setListView('list'); selectContact(c); };
        
        card.innerHTML = `
            <div class="flex items-center gap-2 mb-2">
                <div class="w-2 h-2 rounded-full ${c.source_platform === 'whatsapp' ? 'bg-whatsapp' : (c.source_platform === 'instagram' ? 'bg-instagram' : 'bg-messenger')}"></div>
                <div class="text-[10px] font-bold text-white truncate">${c.name || 'Dr. X'}</div>
            </div>
            <div class="text-[9px] text-gray-500 font-mono mb-2">${c.role || 'MÉDICO'}</div>
            <div class="flex justify-between items-center opacity-40">
                <span class="text-[8px] uppercase font-black tracking-widest">${c.hospital || 'NODO'}</span>
                <span class="material-symbols-outlined text-xs">drag_indicator</span>
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
    
    document.getElementById("active-name").innerText = contact.name || "NODO_IDENTIFICADO";
    document.getElementById("active-details").innerText = `ID_NODE: ${contact.phone_number} | ROLE: ${contact.role || 'MÉDICO'}`;
    document.getElementById("active-avatar").innerText = (contact.name || "?").charAt(0);
    
    const tag = document.getElementById("active-platform-tag");
    tag.innerText = (contact.source_platform || 'whatsapp').toUpperCase();
    tag.className = `text-[8px] bg-white/5 px-1.5 py-0.5 rounded text-${contact.source_platform || 'whatsapp'} uppercase tracking-tighter`;

    const toggle = document.getElementById("ai-toggle");
    const label = document.getElementById("ai-mode-label");
    toggle.checked = contact.is_ai_active;
    label.innerText = contact.is_ai_active ? "IA_ACTIVE" : "IA_OFF";
    label.className = `text-[9px] font-black uppercase tracking-widest ${contact.is_ai_active ? 'text-clinical-400' : 'text-gray-500'}`;
    
    // AI Summary
    const summaryText = document.getElementById("ai-summary-text");
    summaryText.innerText = contact.ai_summary || "Perfilando doctor a través del historial de mensajes...";
    
    loadMessages(contact.phone_number);
    addLog("USER", `Enlazando sesión segura con Dr. ${contact.name || contact.phone_number}`);
    
    // Close mobile menu after selection
    const sidebar = document.getElementById("main-sidebar");
    if (window.innerWidth < 768) {
        sidebar.classList.add("-translate-x-full");
    }
}

function toggleAiSummary() {
    const bar = document.getElementById("ai-summary-bar");
    bar.classList.toggle("hidden");
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
    } catch (e) {}
}

function appendMessage(msg) {
    const history = document.getElementById("chat-history");
    const wrapper = document.createElement("div");
    const isUser = msg.sender_type === 'user';
    const isAi = msg.sender_type === 'ai';
    const isHuman = msg.sender_type === 'human';
    wrapper.className = `flex w-full ${isUser ? 'justify-start' : 'justify-end'} mb-3`;
    const time = new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    let bubbleClass = isUser ? 'bg-carbon-800 text-gray-300 border border-white/5' : 
                      isAi ? 'bg-carbon-900 border border-clinical-500/30 text-gray-200' : 
                      'bg-clinical-600 text-white';
    
    wrapper.innerHTML = `
        <div class="max-w-[80%] px-3 py-2 rounded-xl shadow-lg ${bubbleClass} relative">
            ${isAi ? '<div class="text-[7px] font-black text-clinical-400 mb-1 tracking-widest uppercase">NEURAL_RESPONSE</div>' : ''}
            <p class="text-[11px] leading-snug">${msg.content}</p>
            <div class="text-[8px] mt-1 text-right opacity-30 font-mono">${time}</div>
        </div>
    `;
    history.appendChild(wrapper);
}

async function loadMarketingPipeline() {
    const stages = {
        'STRATEGY': document.getElementById('marketing-strategy'),
        'PRODUCTION': document.getElementById('marketing-production'),
        'SCHEDULED': document.getElementById('marketing-scheduled')
    };
    
    Object.values(stages).forEach(el => el.innerHTML = '<div class="text-[9px] text-gray-700 animate-pulse uppercase">Syncing...</div>');
    
    // Mocking real pipeline data con regiones correctas
    const mockCampaigns = [
        { 
            id: 1, 
            title: "Artroscopia Avanzada", 
            stage: "STRATEGY", 
            region: "Puebla", 
            headline: "Precisión Quirúrgica", 
            reason: "Tendencia creciente en búsquedas de 'recuperación rápida' en Angelópolis.",
            prompt: "Generar render 3D de articulación de hombro con iluminación cinematográfica y logo Ortho-Cardio en la esquina superior derecha.",
            scope: "15,000 médicos especialistas en traumatología."
        },
        { 
            id: 2, 
            title: "Columna 2026", 
            stage: "PRODUCTION", 
            region: "Oaxaca", 
            headline: "Libertad de Movimiento", 
            reason: "Mercado saturado de prótesis rígidas. Enfocando en flexibilidad y tecnología híbrida.",
            prompt: "Video 4K de 15 segundos mostrando la flexibilidad de la prótesis de titanio grado médico.",
            scope: "8,000 leads en la región sur del país."
        },
        { 
            id: 3, 
            title: "Implantes Dentales", 
            stage: "SCHEDULED", 
            region: "Veracruz", 
            headline: "Tu Mejor Sonrisa", 
            reason: "Target de alto poder adquisitivo detectado en zonas portuarias.",
            prompt: "Carrusel de Instagram con casos de éxito y testimonios de cirujanos locales.",
            scope: "25,000 impresiones garantizadas via Meta Ads."
        }
    ];
    
    setTimeout(() => {
        Object.values(stages).forEach(el => el.innerHTML = "");
        mockCampaigns.forEach(camp => {
            const container = stages[camp.stage];
            const card = document.createElement("div");
            card.className = "p-4 bg-carbon-800 border border-white/5 rounded-xl group hover:border-clinical-500/40 transition-all";
            card.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <div class="text-[9px] text-clinical-500 font-black uppercase tracking-widest">${camp.region}</div>
                    <span class="text-[8px] bg-carbon-900 px-1.5 py-0.5 rounded text-gray-500 font-mono">ID_${camp.id}</span>
                </div>
                <h4 class="text-xs font-bold text-white mb-2 uppercase tracking-tight">${camp.title}</h4>
                
                <div class="space-y-2 mb-4">
                    <div class="bg-carbon-900 rounded-lg p-2 border border-white/5">
                        <div class="text-[7px] text-gray-500 uppercase mb-1">Estrategia / SEO</div>
                        <p class="text-[9px] text-gray-400 italic leading-tight">${camp.reason}</p>
                    </div>
                    <div class="bg-carbon-900 rounded-lg p-2 border border-white/5">
                        <div class="text-[7px] text-clinical-400 uppercase mb-1 font-bold">Multimedia Prompt</div>
                        <p class="text-[8px] text-gray-500 leading-tight truncate">${camp.prompt}</p>
                    </div>
                </div>

                ${camp.stage === 'PRODUCTION' ? '<div class="h-1 bg-clinical-500/20 rounded-full mb-4 overflow-hidden"><div class="w-2/3 h-full bg-clinical-500 shadow-[0_0_10px_#0066ff]"></div></div>' : ''}
                
                <div class="flex gap-2">
                    <button onclick="openModal('edit_camp', ${JSON.stringify(camp).replace(/"/g, '&quot;')})" class="flex-1 py-1.5 bg-carbon-900 text-[8px] font-black uppercase border border-white/5 hover:bg-clinical-500 transition-all">Editar</button>
                    <button onclick="openModal('campaign_detail', ${JSON.stringify(camp).replace(/"/g, '&quot;')})" class="flex-1 py-1.5 bg-clinical-500 text-white text-[8px] font-black uppercase hover:bg-clinical-400 transition-all shadow-md">Ver Detalle</button>
                </div>
            `;
            container.appendChild(card);
        });
    }, 500);
}

function addLog(type, message) {
    const container = document.getElementById("watchdog-logs");
    const line = document.createElement("div");
    line.className = `log-line py-0.5 border-b border-white/5 ${type === 'ERROR' ? 'text-red-500' : (type === 'SYSTEM' ? 'text-gray-500' : 'text-clinical-400')}`;
    line.innerHTML = `<span class="opacity-30 font-mono">[${new Date().toLocaleTimeString()}]</span> <span class="font-black">[${type}]</span> ${message}`;
    container.prepend(line);
}

function renderSwarmTask(agent, task) {
    const container = document.getElementById("swarm-feed");
    if (!container) return;
    
    const line = document.createElement("div");
    line.className = "text-[10px] py-1.5 border-l-2 border-clinical-500 pl-3 mb-1 bg-clinical-500/5 flex justify-between items-center group";
    line.innerHTML = `
        <span><span class="text-clinical-400 font-black uppercase">${agent}:</span> ${task}</span>
        <span class="text-[8px] opacity-0 group-hover:opacity-40 transition-opacity font-mono">${new Date().toLocaleTimeString()}</span>
    `;
    container.prepend(line);
    if (container.children.length > 50) container.lastChild.remove();
}

function openModal(type) {
    const overlay = document.getElementById("overlay");
    const content = document.getElementById("overlay-content");
    overlay.classList.remove("hidden");
    
    if (type === 'strategy') {
        content.innerHTML = `
            <h2 class="text-xl font-black text-white mb-6 uppercase">Generar Nueva Estrategia IA</h2>
            <div class="space-y-4">
                <div>
                    <label class="text-[10px] font-bold text-gray-500 uppercase block mb-2">Objetivo Clínico</label>
                    <input type="text" placeholder="Ej: Artroscopia de Hombro - Campaña Mayo" class="w-full bg-carbon-900 border border-white/5 rounded-xl p-4 text-white outline-none focus:border-clinical-500">
                </div>
                <div>
                    <label class="text-[10px] font-bold text-gray-500 uppercase block mb-2">Región de Impacto</label>
                    <select class="w-full bg-carbon-900 border border-white/5 rounded-xl p-4 text-white outline-none focus:border-clinical-500">
                        <option>Puebla - Angelópolis</option>
                        <option>Oaxaca - Zona Central</option>
                        <option>Veracruz - Puerto</option>
                    </select>
                </div>
                <button class="w-full bg-clinical-500 text-white font-black py-4 rounded-xl mt-4 hover:bg-clinical-400 transition-all">INICIAR PROCESAMIENTO NEURAL</button>
            </div>
        `;
    } else if (type === 'campaign_detail') {
        const camp = arguments[1];
        content.innerHTML = `
            <div class="flex justify-between items-center mb-8">
                <div>
                    <div class="text-[10px] text-clinical-400 font-black uppercase tracking-[0.2em] mb-1">Expediente de Campaña</div>
                    <h2 class="text-2xl font-black text-white uppercase">${camp.title}</h2>
                </div>
                <div class="text-right">
                    <div class="text-[10px] text-gray-500 uppercase font-mono">Región</div>
                    <div class="text-lg font-black text-white uppercase">${camp.region}</div>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-8">
                <div class="space-y-6">
                    <div class="bg-carbon-900 p-6 rounded-2xl border border-white/5">
                        <h3 class="text-[10px] font-black text-gray-500 uppercase mb-4 tracking-widest">Estrategia & Razonamiento</h3>
                        <p class="text-xs text-gray-300 leading-relaxed italic border-l-2 border-clinical-500 pl-4">${camp.reason}</p>
                    </div>
                    <div class="bg-carbon-900 p-6 rounded-2xl border border-white/5">
                        <h3 class="text-[10px] font-black text-gray-500 uppercase mb-4 tracking-widest">Alcance Estimado</h3>
                        <div class="text-2xl font-black text-clinical-400">${camp.scope}</div>
                        <p class="text-[10px] text-gray-500 mt-2 uppercase">Datos basados en analítica Meta Business Suite</p>
                    </div>
                </div>
                <div class="bg-carbon-900 p-6 rounded-2xl border border-clinical-500/20">
                    <h3 class="text-[10px] font-black text-clinical-400 uppercase mb-4 tracking-widest">Multimedia Neural Prompt</h3>
                    <div class="bg-black/50 p-4 rounded-xl border border-white/5 font-mono text-[11px] text-gray-400 leading-relaxed mb-6">
                        ${camp.prompt}
                    </div>
                    <div class="p-4 border-2 border-dashed border-white/10 rounded-xl text-center">
                        <span class="material-symbols-outlined text-3xl text-gray-800 mb-2">image_search</span>
                        <p class="text-[9px] text-gray-600 uppercase font-bold">IA analizando renders quirúrgicos...</p>
                    </div>
                </div>
            </div>
            
            <div class="mt-10 flex gap-4">
                <button onclick="closeOverlay()" class="flex-1 py-4 border border-white/5 text-gray-500 font-black uppercase rounded-xl hover:text-white transition-all">Cerrar</button>
                <button class="flex-1 py-4 bg-clinical-500 text-white font-black uppercase rounded-xl hover:bg-clinical-400 transition-all">Aprobar para Meta Ads</button>
            </div>
        `;
    } else if (type === 'upload') {
        content.innerHTML = `
            <h2 class="text-xl font-black text-white mb-6 uppercase">Upload Professional Assets</h2>
            <div class="border-2 border-dashed border-white/10 rounded-3xl p-12 text-center hover:border-clinical-500 transition-all cursor-pointer">
                <span class="material-symbols-outlined text-4xl text-gray-700 mb-4">cloud_upload</span>
                <p class="text-xs text-gray-500 uppercase font-black">Arrastra aquí tu render médico o video quirúrgico</p>
                <p class="text-[9px] text-gray-700 mt-2 uppercase">Soporte hasta 4K / ProRES</p>
            </div>
            <div class="mt-8 flex gap-4">
                <button onclick="closeOverlay()" class="flex-1 border border-white/5 text-gray-500 py-3 rounded-xl font-black uppercase">Cancelar</button>
                <button class="flex-1 bg-clinical-500 text-white py-3 rounded-xl font-black uppercase">Vincular a Campaña</button>
            </div>
        `;
    }
}

function startSwarmFeedSimulation() {
    // Ya no es necesaria la simulación local, ahora viene del servidor
    addLog("SYSTEM", "Canal de Enjambre Sincronizado.");
}

async function sendMessage() {
    if (!currentContactPhone) return;
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    addLog("SYSTEM", `TRANSMITTING_PAYLOAD_TO_NODE: ${currentContactPhone}`);
    try {
        await fetch(`/api/contacts/${currentContactPhone}/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
        });
    } catch (e) { addLog("ERROR", `FAILED_TRANSMISSION: ${e.message}`); }
}

function handleKeyPress(e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }
function scrollToBottom() { const h = document.getElementById("chat-history"); h.scrollTop = h.scrollHeight; }
function closeOverlay() { document.getElementById("overlay").classList.add("hidden"); }
function toggleAiMode() { /* API call for AI toggle */ }
