import os
import json
import logging
import asyncio
from pydantic import BaseModel
import google.generativeai as genai
from quote_agent import QuoteAgent
from database import SessionLocal
from models import QuoteApproval, Contact, Message
from sqlalchemy import text
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv(os.path.join(os.getcwd(), ".env"))
from model_router import router

logger = logging.getLogger("Orchestrator")

ADMIN_NUMBERS = [

    os.getenv("ADMIN_NUMBER_1", "522211853060"), 
    os.getenv("ADMIN_NUMBER_2", "522221143252")
]

class IntentResponse(BaseModel):
    intent: str = "PERFILAMIENTO"
    confidence: float = 1.0
    reasoning: str = ""
    actionable_data: dict = {}



class Orchestrator:
    def __init__(self, api_key: str):
        self.quote_agent = QuoteAgent(api_key=api_key)
        self.system_instruction = """Clasifica el mensaje en JSON:
        {"intent": "COTIZACION" | "PERFILAMIENTO" | "SOPORTE_HUMANO" | "APROBACION_ADMIN" | "MODIFICACION_ADMIN"}
        
        - COTIZACION: Piden productos/precios.
        - APROBACION_ADMIN: Admin dice 'APROBADO'.
        - MODIFICACION_ADMIN: Admin pide cambios.
        - PERFILAMIENTO: Saludos/Dudas.
        - SOPORTE_HUMANO: Otros.
        NUNCA uses emojis. Tono clínico formal."""


    async def classify_intent(self, message_text: str, is_admin: bool) -> IntentResponse:
        admin_context = "El mensaje proviene de un ADMINISTRADOR." if is_admin else "El mensaje proviene de un CLIENTE."
        prompt = f"{admin_context}\nMensaje: {message_text}"
        
        try:
            clean_text = await router.generate_content(
                prompt=prompt, 
                system_instruction=self.system_instruction, 
                json_mode=True
            )
            
            data = json.loads(clean_text)
            # Mapeo flexible de llaves
            mapping = {
                "INTENCION": "intent", "INTENT": "intent", "INTENCION_ADMIN": "intent",
                "CONFIANZA": "confidence", "CONFIDENCE": "confidence",
                "RAZONAMIENTO": "reasoning", "REASONING": "reasoning",
                "ACTIONABLE_DATA": "actionable_data"
            }
            final_data = {}
            for k, v in data.items():
                final_key = mapping.get(k.upper(), k.lower())
                final_data[final_key] = v
            
            return IntentResponse.model_validate(final_data)
        except Exception as e:
            logger.error(f"Error crítico en orquestador: {e}")
            return IntentResponse(intent="SOPORTE_HUMANO")



    async def handle_message(self, message_text: str, phone_number: str, contact_name: str, hospital: str):
        is_admin = phone_number in ADMIN_NUMBERS
        intent_data = await self.classify_intent(message_text, is_admin)

        # FLUJO ADMINISTRADOR
        if is_admin:
            if intent_data.intent == "APROBACION_ADMIN":
                return await self.process_approval(phone_number)
            elif intent_data.intent == "MODIFICACION_ADMIN":
                return await self.process_modification(message_text, phone_number)

        # FLUJO CLIENTE (O Admin pidiendo cotización para alguien)
        if intent_data.intent == "COTIZACION":
            products = await self.quote_agent.find_products(message_text)
            if products:
                approval_id, pdf_path = await self.quote_agent.create_quote_for_approval(phone_number, contact_name, hospital, products)
                # Alerta obligatoria para administradores
                alert_msg = f"Cotización generada para {contact_name}/{hospital}. Requiere autorización. Responda APROBADO para transmitir al cliente, o indique las modificaciones necesarias. Documento: {pdf_path}"
                # En un entorno real, aquí enviaríamos activamente a ADMIN_NUMBERS. 
                # Por ahora, devolvemos la instrucción para que main.py la encamine.
                return {"type": "approval_required", "admin_message": alert_msg, "client_message": "He recibido su solicitud. El departamento técnico está validando los términos de su cotización. Le informaré en breve."}
            else:
                return "He recibido su requerimiento. Procedo a verificar la disponibilidad de este sistema a través de nuestra red de proveeduría para prepararle una cotización detallada a la brevedad."

        if intent_data.intent == "SOPORTE_HUMANO":
            return "He notificado a un consultor especializado para atender su solicitud de forma personalizada."

        return "Gracias por su consulta técnica. ¿Desea profundizar en algún sistema en particular?"

    async def process_approval(self, admin_phone: str):
        with SessionLocal() as db:
            # Buscar la última cotización pendiente
            approval = db.query(QuoteApproval).filter(QuoteApproval.status == "PENDING_APPROVAL").order_by(QuoteApproval.created_at.desc()).first()
            if not approval:
                return "No hay cotizaciones pendientes de aprobación."
            
            approval.status = "APPROVED"
            db.commit()
            
            return {
                "type": "quote_approved",
                "client_phone": approval.contact_phone,
                "pdf_path": approval.pdf_path,
                "admin_confirmation": "Cotización transmitida con éxito.",
                "client_message": f"Su cotización ha sido autorizada. Adjunto el documento técnico-comercial solicitado. Documento: {approval.pdf_path}"
            }

    async def process_modification(self, instruction: str, admin_phone: str):
        with SessionLocal() as db:
            approval = db.query(QuoteApproval).filter(QuoteApproval.status == "PENDING_APPROVAL").order_by(QuoteApproval.created_at.desc()).first()
            if not approval:
                return "No hay cotizaciones activas para modificar."

            # Usar Gemini para interpretar la modificación y regenerar
            prompt = f"El administrador pide: '{instruction}'. Aplica este cambio a los items actuales: {json.dumps(approval.items_json)}. Devuelve el nuevo JSON de items."
            model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
            response = await asyncio.to_thread(model.generate_content, prompt)
            new_items = json.loads(response.text)
            
            # Regenerar PDF
            contact = db.query(Contact).filter(Contact.phone_number == approval.contact_phone).first()
            new_pdf = await self.quote_agent.generate_quote_pdf(contact.name, contact.hospital, new_items)
            
            approval.pdf_path = new_pdf
            approval.items_json = new_items
            approval.status = "PENDING_APPROVAL"
            db.commit()
            
            return f"Cotización actualizada con las modificaciones solicitadas. ¿Desea aprobar ahora? Documento: {new_pdf}"
