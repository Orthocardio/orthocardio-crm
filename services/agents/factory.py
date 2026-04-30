from typing import List, Dict, Any
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, role: str, instruction: str):
        self.name = name
        self.role = role
        self.instruction = instruction
        self.model = genai.GenerativeModel('gemini-2.0-flash') # Usamos el modelo más rápido y capaz

    async def run(self, input_text: str, context: Dict[str, Any] = None) -> str:
        prompt = f"ROLE: {self.role}\nCONTEXT: {context}\nUSER_INPUT: {input_text}"
        response = self.model.generate_content(
            contents=prompt,
            system_instruction=self.instruction
        )
        return response.text

class MarketingAgent(BaseAgent):
    def __init__(self):
        instruction = """ESTÁNDAR AGENTE CREATIVO ORTHO-CARDIO:
        - Objetivo: Generar activos de marketing de alto impacto (Nano Banana Prompts, Copys Quirúrgicos).
        - Estilo: Innovador, fotorrealista, basado en tendencias de cirugía robótica.
        - Salida: Siempre sugiere un 'Copy Headline', 'Copy Body' y un 'Visual Prompt'."""
        super().__init__("MarketingAgent", "Director Creativo IA", instruction)

class SalesAgent(BaseAgent):
    def __init__(self):
        instruction = """ESTÁNDAR AGENTE SDR ORTHO-CARDIO:
        - Objetivo: Perfilamiento de cirujanos y cierre de ventas de implantes.
        - Estilo: Técnico, quirúrgico, formal, orientado a beneficios logísticos.
        - Salida: Respuestas precisas sobre precios, disponibilidad y certificaciones."""
        super().__init__("SalesAgent", "Consultor Comercial Senior", instruction)

class SourcingAgent(BaseAgent):
    def __init__(self):
        instruction = """ESTÁNDAR AGENTE LOGÍSTICA ORTHO-CARDIO:
        - Objetivo: Optimización de inventario y búsqueda de materiales (Alibaba/Proveedores).
        - Estilo: Analítico, orientado a costos y tiempos de entrega.
        - Salida: Reportes de stock y alertas de reposición."""
        super().__init__("SourcingAgent", "Head of Sourcing", instruction)
