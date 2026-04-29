import os
import json
import logging
from pydantic import BaseModel
from google import genai
from google.genai import types

logger = logging.getLogger("Orchestrator")

class IntentResponse(BaseModel):
    intent: str  # PERFILAMIENTO, COTIZACION, SOPORTE_HUMANO
    confidence: float
    reasoning: str
    actionable_data: dict

class Orchestrator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.system_instruction = """Eres el Nodo Orquestador de Ortho-Cardio. 
        Tu única función es clasificar el mensaje del cliente en un JSON estricto.
        INTENCIONES:
        - PERFILAMIENTO: Dudas técnicas, saludos o consultas sobre tecnología quirúrgica.
        - COTIZACION: Solicitud explícita de precios, stocks o presupuestos.
        - SOPORTE_HUMANO: Quejas, solicitudes de hablar con un humano o mensajes fuera de contexto médico.
        
        REGLA DE ORO: Si el cliente pide precios, clasifica como COTIZACION.
        NUNCA devuelvas texto plano, solo el esquema JSON definido.
        TONO: Clínico, formal, sin emojis."""

    async def classify_intent(self, message_text: str) -> IntentResponse:
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=message_text,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    response_mime_type="application/json",
                    response_schema=IntentResponse
                )
            )
            return IntentResponse.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Falla en clasificación de intención: {str(e)}")
            return IntentResponse(intent="SOPORTE_HUMANO", confidence=0.0, reasoning="Error de sistema", actionable_data={})
