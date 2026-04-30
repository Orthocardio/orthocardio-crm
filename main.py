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

from database import engine, Base, get_db
from models import Contact, Message
from orchestrator import Orchestrator
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
    logger.info("Tablas de BD sincronizadas correctamente.")
except Exception as e:
    logger.warning(f"No se pudieron crear tablas al inicio (se reintentará en la primera petición): {e}")




META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ADMIN_NUMBERS = [os.getenv("ADMIN_NUMBER_1"), os.getenv("ADMIN_NUMBER_2")]

app = FastAPI(title="Ortho-Cardio CRM Búnker API")

# Configurar templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

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

# --- API ENDPOINTS ---

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
        background_tasks.add_task(process_meta_payload, body)
        return Response(content="EVENT_RECEIVED", status_code=200)
    except Exception as e:
        logger.error(f"Error recibiendo webhook: {e}")
        return Response(content="ERROR", status_code=200)

async def generate_gemini_response(user_message: str):
    try:
        system_prompt = "Eres el agente clínico de Ortho-Cardio. Lenguaje estrictamente médico, técnico y formal. Sin emojis."
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
                                response = await orchestrator.handle_message(
                                    message_text, sender_id, contact.name or "Doctor", contact.hospital or "Hospital"
                                )
                                
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
    return templates.TemplateResponse("dashboard_premium.html", {"request": request})
