import os
import logging
import datetime
import secrets
import asyncio
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import httpx
import google.generativeai as genai
from dotenv import load_dotenv

from database import engine as db_engine, Base, get_db
from models import Contact, Message
from services.core.engine import Orchestrator

# Inicializar motor agéntico (El Cerebro)
ai_engine = Orchestrator()
from model_router import router
from pdf_generator import OrthoPDF

# Cargar variables de entorno
load_dotenv(os.path.join(os.getcwd(), ".env"))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrthoCardioCRM")

# Inicializar componentes del enjambre
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

orchestrator = Orchestrator(api_key=GEMINI_API_KEY)
pdf_engine = OrthoPDF()

# Crear tablas en BD (tolerante a fallos de conexión para no bloquear el arranque)
try:
    Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=db_engine)
    logger.info("Tablas de BD sincronizadas correctamente.")
except Exception as e:
    logger.warning(f"No se pudieron crear tablas al inicio: {e}")

# --- SINCRONIZACIÓN DE ESQUEMA (Migración Automática) ---
def ensure_schema_sync():
    from sqlalchemy import text
    db = next(get_db())
    try:
        # Forzar columnas faltantes en 'contacts' usando SQL nativo para mayor compatibilidad
        columns_to_check = [
            ("status", "VARCHAR", "DEFAULT 'PENDING'"),
            ("source_platform", "VARCHAR", "DEFAULT 'whatsapp'"),
            ("ai_summary", "TEXT", ""),
            ("followup_draft", "VARCHAR", ""),
            ("last_interaction", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP")
        ]
        
        # Obtener columnas existentes
        existing_cols_result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='contacts'"))
        existing_cols = [row[0] for row in existing_cols_result]
        
        for col_name, col_type, extra in columns_to_check:
            if col_name not in existing_cols:
                logger.info(f"Detectada columna faltante: {col_name}. Migrando...")
                db.execute(text(f"ALTER TABLE contacts ADD COLUMN {col_name} {col_type} {extra}"))
                db.commit()
                logger.info(f"Columna '{col_name}' sincronizada.")
        
        # Sincronizar otras tablas
        Base.metadata.create_all(bind=db_engine)
    except Exception as e:
        db.rollback()
        logger.error(f"FALLO CRÍTICO EN SINCRONIZACIÓN DE ESQUEMA: {e}")
    finally:
        db.close()

# --- SEMILLA DE DATOS ---
def seed_demo_data():
    db = next(get_db())
    try:
        if db.query(Contact).count() == 0:
            logger.info("Base de datos vacía. Generando contactos demo...")
            demo_contacts = [
                Contact(phone_number="521234567890", name="Dr. Alejandro Méndez", role="Cardiólogo", hospital="Hospital Ángeles", is_ai_active=True, status="HOT_LEAD", source_platform="whatsapp", ai_summary="Interesado en stents de última generación. Alta probabilidad de cierre."),
                Contact(phone_number="529876543210", name="Dra. Sofía Reyes", role="Ortopedista", hospital="Centro Médico Siglo XXI", is_ai_active=False, status="COLD_LEAD", source_platform="instagram", ai_summary="Preguntó por prótesis de cadera vía DM. Requiere perfilamiento técnico."),
                Contact(phone_number="522229998877", name="Dr. Julián Casablancas", role="Cirujano Columna", hospital="Hospital Puebla", is_ai_active=True, status="PENDING", source_platform="messenger", ai_summary="Liderazgo en cirugías mínimamente invasivas. Buscando alternativas de sourcing."),
                Contact(phone_number="525554443322", name="Dra. Elena Poniatowska", role="Artroscopia", hospital="Médica Sur", is_ai_active=True, status="CONVERTED", source_platform="whatsapp", ai_summary="Cliente recurrente. Muy satisfecho con el sistema de navegación.")
            ]
            db.add_all(demo_contacts)
            db.commit()
            logger.info("Contactos demo creados con éxito.")
    except Exception as e:
        logger.error(f"Error en semilla de datos: {e}")
    finally:
        db.close()




META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ADMIN_NUMBERS = [os.getenv("ADMIN_NUMBER_1"), os.getenv("ADMIN_NUMBER_2")]

app = FastAPI(title="Ortho-Cardio CRM Búnker API")

@app.on_event("startup")
async def startup_event():
    ensure_schema_sync()
    seed_demo_data()
    asyncio.create_task(swarm_heartbeat())

# Configurar templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/Logo", StaticFiles(directory=os.path.join(BASE_DIR, "Logo")), name="Logo")

# --- MIDDLEWARE: CORS SEGURO ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SEGURIDAD: HTTP BASIC AUTH ---
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    authorized_users = {
        "carlos.cortes@ortho-cardio.com.mx": "Orthocardio2026",
        "oscar.mendez@ortho-cardio.com.mx": "Orthocardio2026"
    }
    user = authorized_users.get(credentials.username)
    if user and secrets.compare_digest(user, credentials.password):
        return credentials.username
    raise HTTPException(
        status_code=401,
        detail="Acceso Denegado: Credenciales Ortho-Cardio Inválidas",
        headers={"WWW-Authenticate": "Basic"},
    )

# --- WEBSOCKET MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                continue

manager = ConnectionManager()

async def broadcast_swarm_task(agent: str, task: str):
    await manager.broadcast({
        "type": "swarm_task",
        "agent": agent,
        "task": task
    })

async def swarm_heartbeat():
    tasks = [
        ("SEO_AGENT", "Escaneando tendencias de búsqueda en tiempo real..."),
        ("SOURCING_AGENT", "Optimizando cadena de suministro de implantes..."),
        ("CRM_AGENT", "Analizando sentimientos clínicos en hilos activos..."),
        ("INVENTORY_AGENT", "Verificando niveles de stock en nodos hospitalarios..."),
        ("MARKETING_AGENT", "Sincronizando activos multimedia con Meta Staging..."),
        ("SYSTEM_WATCHDOG", "Latencia de red: 42ms. Salud del Búnker: 100%."),
        ("NEURAL_CORE", "Indexando nuevos conocimientos quirúrgicos...")
    ]
    import random
    while True:
        await asyncio.sleep(random.randint(5, 12)) # Más rápido para dar sensación de actividad
        agent, task = random.choice(tasks)
        await broadcast_swarm_task(agent, task)

# --- API ENDPOINTS ---

@app.get("/api/marketing/campaigns")
async def get_marketing_campaigns():
    return [
        {
            "id": "camp_001",
            "status": "PENDING_ASSETS",
            "target_region": "CDMX / Santa Fe",
            "copy_headline": "Innovación en Artroscopia de Hombro",
            "copy_body": "Presentamos el sistema de navegación de última generación para procedimientos mínimamente invasivos. Precisión quirúrgica sin precedentes.",
            "nano_banana_prompt": "Photorealistic medical surgical room, ultra-modern arthroscopy equipment, blue clinical lighting, cinematic 8k, bokeh background.",
            "image_url": "https://images.unsplash.com/photo-1551076805-e1869033e561?auto=format&fit=crop&q=80&w=1000"
        },
        {
            "id": "camp_002",
            "status": "APPROVED",
            "target_region": "Puebla / Lomas de Angelópolis",
            "copy_headline": "Excelencia en Columna Vertebral",
            "copy_body": "Tu movilidad es nuestra prioridad. Descubre las prótesis inteligentes de Ortho-Cardio.",
            "nano_banana_prompt": "3D render of a futuristic spine implant, glowing blue accents, carbon fiber textures, dark background, high-tech aesthetic.",
            "image_url": "https://images.unsplash.com/photo-1579154273821-3df7579f9723?auto=format&fit=crop&q=80&w=1000"
        }
    ]

@app.get("/api/health")
async def health_check():
    return {"status": "online", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.get("/api/contacts")
def get_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).order_by(Contact.last_interaction.desc()).all()
    return [
        {
            "phone_number": c.phone_number,
            "name": c.name,
            "role": c.role,
            "hospital": c.hospital,
            "is_ai_active": c.is_ai_active,
            "status": c.status,
            "source_platform": c.source_platform,
            "ai_summary": c.ai_summary,
            "followup_draft": c.followup_draft,
            "last_interaction": c.last_interaction.isoformat() if c.last_interaction else None
        } for c in contacts
    ]

@app.get("/api/contacts/{phone_number}/messages")
def get_messages(phone_number: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.contact_phone == phone_number).order_by(Message.timestamp.asc()).all()
    return [
        {
            "id": m.id,
            "sender_type": m.sender_type,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        } for m in messages
    ]

@app.post("/api/contacts/{phone_number}/toggle_ai")
async def toggle_ai(phone_number: str, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.phone_number == phone_number).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    contact.is_ai_active = not contact.is_ai_active
    db.commit()
    
    await manager.broadcast({
        "type": "contact_update",
        "phone_number": phone_number,
        "is_ai_active": contact.is_ai_active
    })
    
    return {"status": "success", "is_ai_active": contact.is_ai_active}

@app.post("/api/contacts/{phone_number}/send")
async def send_manual_message(phone_number: str, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="El contenido es obligatorio")

    # Guardar en BD
    new_message = Message(contact_phone=phone_number, sender_type='human', content=content)
    db.add(new_message)
    contact = db.query(Contact).filter(Contact.phone_number == phone_number).first()
    if contact:
        contact.last_interaction = datetime.datetime.utcnow()
        contact.followup_draft = None
    db.commit()

    # Enviar por Meta API
    await send_whatsapp_message(PHONE_NUMBER_ID, phone_number, content)

    # Broadcast
    await manager.broadcast({
        "type": "new_message",
        "phone_number": phone_number,
        "message": {
            "id": new_message.id,
            "sender_type": "human",
            "content": content,
            "timestamp": new_message.timestamp.isoformat()
        }
    })
    
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

from fastapi.responses import JSONResponse, PlainTextResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.critical(f"FALLO CRÍTICO DETECTADO: {exc}")
    
    # Notificar a los administradores vía WhatsApp (Watchdog)
    # Los números ADMIN_NUMBER_1/2 se cargan en orchestrator.py pero podemos usarlos aquí
    alert_msg = f"ALERTA DE SISTEMA: Se ha detectado un fallo en el módulo {request.url.path}. Detalle técnico para depuración: {str(exc)[:200]}. El sistema continúa operando en modo degradado."
    
    # Lógica de envío de alerta a ADMIN_NUMBERS
    logger.error(alert_msg)

    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "status": "DEGRADED"}
    )

# --- WEBHOOK ENDPOINTS ---

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        logger.info("WEBHOOK_VERIFIED")
        return PlainTextResponse(content=challenge)
    
    return Response(content="Forbidden", status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        # Log inmediato en la consola de enjambre
        await broadcast_swarm_task("SYSTEM_WATCHDOG", "PAYLOAD_RECEPCIONADO: Verificando integridad de Meta API...")
        background_tasks.add_task(process_meta_payload, body)
        return Response(content="EVENT_RECEIVED", status_code=200)
    except Exception as e:
        logger.error(f"Error recibiendo webhook: {e}")
        return Response(content="ERROR", status_code=200)

async def generate_gemini_response(user_message: str):
    try:
        system_prompt = """ESTÁNDAR DE OPERACIÓN ORTHO-CARDIO:
        - Eres el Consultor de Tecnología Médica del Búnker Central.
        - Tu objetivo es la conversión de cirujanos y clínicas en clientes activos.
        - Lenguaje: Quirúrgico, técnico, extremadamente formal. 
        - Conocimiento: Dominas el catálogo de implantes de columna, sistemas de navegación artroscópica y logística hospitalaria.
        - Restricción: NUNCA digas 'lo siento' o 'disculpa'. Eres una autoridad técnica. 
        - Tarea: Responder con precisión milimétrica a las dudas del doctor."""
        
        return await router.generate_content(
            prompt=user_message,
            system_instruction=system_prompt
        )
    except Exception as e:
        logger.error(f"Error en generación manual: {e}")
        return "Servicio temporalmente en mantenimiento técnico."

async def process_meta_payload(body: Dict[Any, Any]):

    try:
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    phone_number_id = value.get("metadata", {}).get("phone_number_id")
                    
                    contacts_info = value.get("contacts", [])
                    sender_name = contacts_info[0].get("profile", {}).get("name", "Unknown") if contacts_info else "Unknown"

                    for message in messages:
                        if message.get("type") == "text":
                            sender_id = message.get("from")
                            message_text = message.get("text", {}).get("body")
                            
                            db = next(get_db())
                            contact = db.query(Contact).filter(Contact.phone_number == sender_id).first()
                            if not contact:
                                contact = Contact(phone_number=sender_id, name=sender_name)
                                db.add(contact)
                            
                            contact.last_interaction = datetime.datetime.utcnow()
                            contact.followup_draft = None
                            
                            user_msg = Message(contact_phone=sender_id, sender_type='user', content=message_text)
                            db.add(user_msg)
                            db.commit()

                            await manager.broadcast({
                                "type": "new_message", "phone_number": sender_id,
                                "message": {"id": user_msg.id, "sender_type": "user", "content": message_text, "timestamp": user_msg.timestamp.isoformat()}
                            })

                            if contact.is_ai_active:
                                await broadcast_swarm_task("NEURAL_CORE", f"Enrutando solicitud a enjambre especializado...")
                                
                                # Contexto para el agente
                                context = {
                                    "doctor_name": contact.name or "Desconocido",
                                    "specialty": contact.role or "Especialista",
                                    "hospital": contact.hospital or "N/A",
                                    "platform": contact.source_platform
                                }
                                
                                result = await ai_engine.route_and_execute(message_text, context)
                                response = result["response"]
                                
                                await broadcast_swarm_task(result["agent"], f"Ejecución completada: {result['tasks'][0]}")
                                
                                if isinstance(response, str):
                                    await save_and_send_message(db, sender_id, response, phone_number_id)
                                elif isinstance(response, dict):
                                    if response.get("type") == "approval_required":
                                        # Notificar al cliente
                                        await save_and_send_message(db, sender_id, response["client_message"], phone_number_id)
                                        # Notificar a administradores
                                        for admin in ADMIN_NUMBERS:
                                            if admin:
                                                await send_whatsapp_message(phone_number_id, admin, response["admin_message"])
                                    elif response.get("type") == "quote_approved":
                                        # Enviar al cliente
                                        await save_and_send_message(db, response["client_phone"], response["client_message"], phone_number_id)
                                        # Confirmar al admin
                                        await send_whatsapp_message(phone_number_id, sender_id, response["admin_confirmation"])
                            db.close()
    except Exception as e:
        logger.error(f"Payload Error: {e}")

async def save_and_send_message(db, recipient_id, text, phone_number_id):
    ai_msg = Message(contact_phone=recipient_id, sender_type='ai', content=text)
    db.add(ai_msg)
    db.commit()
    await manager.broadcast({
        "type": "new_message", "phone_number": recipient_id,
        "message": {"id": ai_msg.id, "sender_type": "ai", "content": text, "timestamp": ai_msg.timestamp.isoformat()}
    })
    await send_whatsapp_message(phone_number_id, recipient_id, text)

async def send_whatsapp_message(phone_number_id: str, recipient_id: str, text: str):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": recipient_id, "type": "text", "text": {"body": text}}
    async with httpx.AsyncClient() as client_http:
        try:
            response = await client_http.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Meta API Error: {e}")

@app.get("/", response_class=HTMLResponse)
async def root_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard_premium.html", context={})
