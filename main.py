import os
import logging
from typing import Dict, Any, Optional, List
import datetime

from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import httpx
from google import genai
from google.genai import types
from dotenv import load_dotenv

from database import engine, Base, get_db
from models import Contact, Message
from orchestrator import Orchestrator
from pdf_generator import OrthoPDF

# Inicializar componentes del enjambre
orchestrator = Orchestrator(api_key=os.getenv("GEMINI_API_KEY"))
pdf_engine = OrthoPDF()

# Crear tablas en BD
Base.metadata.create_all(bind=engine)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validación básica de credenciales
if not all([META_VERIFY_TOKEN, META_ACCESS_TOKEN, GEMINI_API_KEY]):
    logger.warning("Faltan variables de entorno críticas (META_VERIFY_TOKEN, META_ACCESS_TOKEN, GEMINI_API_KEY).")

# Configurar Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """Eres el agente clínico de Comercializadora Ortho-Cardio. Tu lenguaje es estrictamente médico, técnico y formal. Queda absolutamente prohibido el uso de emojis y frases coloquiales. Nunca des precios. Si solicitan cotización, pide Nombre completo, Especialidad y Hospital."""


from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

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

app = FastAPI(title="Ortho-Cardio CRM Búnker Edition")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: str = Depends(authenticate)):
    return """
    <div style='background:#131313;color:#e5e2e1;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;font-family:sans-serif;'>
        <h1>ORTHO-CARDIO BÚNKER</h1>
        <p>Bienvenido, """ + user + """</p>
        <p>Sistema de Gestión Omnicanal Online</p>
        <div style='border:1px solid #acc7ff;padding:20px;border-radius:8px;'>
            Dashboard Live - Sincronizado con Supabase
        </div>
    </div>
    """

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
            except Exception as e:
                logger.error(f"Error broadcasting to a websocket: {e}")

manager = ConnectionManager()


# --- DASHBOARD ENDPOINTS ---
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/contacts")
def get_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).order_by(Contact.last_interaction.desc()).all()
    return [{"phone_number": c.phone_number, "name": c.name, "is_ai_active": c.is_ai_active, "last_interaction": c.last_interaction} for c in contacts]

@app.get("/api/contacts/{phone_number}/messages")
def get_messages(phone_number: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.contact_phone == phone_number).order_by(Message.timestamp.asc()).all()
    return [{"sender": m.sender_type, "content": m.content, "timestamp": m.timestamp} for m in messages]

@app.post("/api/contacts/{phone_number}/toggle_ai")
def toggle_ai(phone_number: str, request: Request, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.phone_number == phone_number).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_ai_active = not contact.is_ai_active
    db.commit()
    return {"status": "success", "is_ai_active": contact.is_ai_active}

@app.post("/api/contacts/{phone_number}/send")
async def send_manual_message(phone_number: str, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    # Guardar en BD
    new_message = Message(contact_phone=phone_number, sender_type='human', content=content)
    db.add(new_message)
    contact = db.query(Contact).filter(Contact.phone_number == phone_number).first()
    contact.last_interaction = datetime.datetime.utcnow()
    db.commit()

    # Enviar por Meta API
    # Usamos el phone_number_id del env para enviar
    phone_id = os.getenv("PHONE_NUMBER_ID")
    await send_whatsapp_message(phone_id, phone_number, content)

    # Broadcast
    await manager.broadcast({
        "type": "new_message",
        "phone_number": phone_number,
        "message": {"sender": "human", "content": content, "timestamp": new_message.timestamp.isoformat()}
    })
    
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Mantener conexión viva
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# --- WEBHOOK ENDPOINTS ---
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == META_VERIFY_TOKEN:
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    
    raise HTTPException(status_code=400, detail="Missing parameters")

@app.get("/privacy")
async def privacy_policy():
    return PlainTextResponse("Política de Privacidad de Comercializadora Ortho-Cardio. Esta aplicación no almacena datos de manera pública.")

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        background_tasks.add_task(process_meta_payload, body)
        return Response(content="EVENT_RECEIVED", status_code=200)
    except Exception as e:
        logger.error(f"Error procesando payload: {str(e)}")
        return Response(content="ERROR", status_code=200)

async def process_meta_payload(body: Dict[Any, Any]):
    try:
        object_type = body.get("object")
        if object_type == "whatsapp_business_account":
            await handle_whatsapp_message(body)
        # TODO: Implementar Messenger/IG después en Fase 1 si aplica, nos enfocamos en WA primero.
    except Exception as e:
        logger.error(f"Excepción procesando payload: {str(e)}")

async def handle_whatsapp_message(body: Dict[Any, Any]):
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            
            # Obtener perfil (nombre del contacto) si está disponible
            contacts_info = value.get("contacts", [])
            sender_name = contacts_info[0].get("profile", {}).get("name", "Unknown") if contacts_info else "Unknown"

            for message in messages:
                if message.get("type") == "text":
                    sender_id = message.get("from")
                    message_text = message.get("text", {}).get("body")
                    
                    # Manejo de BD: Guardar mensaje del usuario
                    db = next(get_db())
                    contact = db.query(Contact).filter(Contact.phone_number == sender_id).first()
                    if not contact:
                        contact = Contact(phone_number=sender_id, name=sender_name)
                        db.add(contact)
                    
                    contact.last_interaction = datetime.datetime.utcnow()
                    user_msg = Message(contact_phone=sender_id, sender_type='user', content=message_text)
                    db.add(user_msg)
                    db.commit()

                    # Broadcast a los websockets del nuevo mensaje de usuario
                    await manager.broadcast({
                        "type": "new_message",
                        "phone_number": sender_id,
                        "message": {"sender": "user", "content": message_text, "timestamp": user_msg.timestamp.isoformat()}
                    })

                    # Procesar con IA solo si está activa
                    if contact.is_ai_active:
                        # 1. Clasificación por Enjambre (Orquestador)
                        import asyncio
                        classification = await orchestrator.classify_intent(message_text)
                        
                        if classification.intent == "SOPORTE_HUMANO":
                            contact.is_ai_active = False
                            db.commit()
                            await manager.broadcast({
                                "type": "handoff",
                                "phone_number": sender_id,
                                "reason": classification.reasoning
                            })
                            # Notificar al usuario que un humano tomará el control
                            handoff_msg = "He transferido su consulta a un ejecutivo de cuenta especializado. En breve se pondrán en contacto con usted."
                            await send_whatsapp_message(phone_number_id, sender_id, handoff_msg)
                            db.close()
                            continue

                        if classification.intent == "COTIZACION":
                            # 2. Generación automática de PDF (Draft)
                            pdf_path = pdf_engine.create_quote(contact.name, contact.hospital or "Por definir", [{"name": message_text, "qty": 1}])
                            logger.info(f"Cotización técnica generada en: {pdf_path}")

                        # 3. Generación de respuesta clínica especializada
                        gemini_response = generate_gemini_response(message_text)
                        if gemini_response:
                            # Guardar en BD la respuesta de IA
                            ai_msg = Message(contact_phone=sender_id, sender_type='ai', content=gemini_response)
                            db.add(ai_msg)
                            db.commit()

                            # Broadcast a los websockets
                            await manager.broadcast({
                                "type": "new_message",
                                "phone_number": sender_id,
                                "message": {"sender": "ai", "content": gemini_response, "timestamp": ai_msg.timestamp.isoformat()}
                            })

                            # Enviar por API de Meta
                            await send_whatsapp_message(phone_number_id, sender_id, gemini_response)
                    else:
                        logger.info(f"Mensaje de {sender_id} ignorado por IA porque está en Modo Humano.")
                    
                    db.close()

def generate_gemini_response(user_message: str) -> Optional[str]:
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Error Gemini: {str(e)}")
        return None

async def send_whatsapp_message(phone_number_id: str, recipient_id: str, text: str):
    if not phone_number_id:
        phone_number_id = os.getenv("PHONE_NUMBER_ID")
        
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client_http:
        try:
            response = await client_http.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error Meta API: {str(e)}")

# --- MARKETING AUTOMATIZADO ---
@app.post("/generate-marketing")
async def generate_marketing_content():
    try:
        prompt = "Redacta un artículo SEO clínico y técnico sobre tecnología quirúrgica cardiovascular, diseñado para atraer y prospectar doctores especialistas en Puebla, Veracruz y Oaxaca. El tono debe ser altamente profesional, de nivel congreso médico."
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        return {"status": "success", "article": response.text}
    except Exception as e:
        logger.error(f"Error generando contenido de marketing: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating marketing content")
