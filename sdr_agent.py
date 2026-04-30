import os
import json
import logging
import httpx
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models import Contact
from model_router import router

logger = logging.getLogger("SDRAgent")

class SDRAgent:
    """
    Agente de Prospección Clínica (SDR).
    Busca especialistas en zonas geográficas específicas e ingresa prospectos calificados en el CRM.
    """
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.target_locations = [
            "San Pedro Cholula, Puebla",
            "Puebla Capital, Puebla",
            "Veracruz, Veracruz",
            "Oaxaca de Juarez, Oaxaca"
        ]
        self.search_queries = [
            "Traumatologo",
            "Ortopedista",
            "Clinica de Ortopedia",
            "Hospital con quirofano"
        ]

    async def search_prospects(self) -> List[Dict[str, Any]]:
        """
        Simula o ejecuta la búsqueda vía Google Places (requiere API KEY).
        Por ahora, implementamos la estructura de ingesta y filtrado.
        """
        all_leads = []
        async with httpx.AsyncClient() as client:
            for location in self.target_locations:
                for query in self.search_queries:
                    logger.info(f"Buscando {query} en {location}...")
                    # Nota: En producción esto llamaría a Google Places API
                    # mock_results = await self._call_google_places(client, query, location)
                    # all_leads.extend(mock_results)
                    pass
        
        # Simulación de un lead encontrado para validación de flujo
        mock_lead = {
            "name": "Dr. Ramirez - Traumatologia Especializada",
            "phone_number": "522220000001",
            "hospital": "Hospital Angeles Puebla",
            "role": "Traumatologo",
            "location": "Puebla Capital"
        }
        return [mock_lead]

    async def ingest_leads(self, leads: List[Dict[str, Any]]):
        """
        Ingesta masiva de leads en la tabla contacts con estado COLD_LEAD.
        """
        with SessionLocal() as db:
            for lead in leads:
                # Evitar duplicados por número de teléfono
                existing = db.query(Contact).filter(Contact.phone_number == lead["phone_number"]).first()
                if not existing:
                    new_contact = Contact(
                        phone_number=lead["phone_number"],
                        name=lead["name"],
                        hospital=lead["hospital"],
                        role=lead["role"],
                        status="COLD_LEAD",
                        is_ai_active=True # Marketing autónomo activado por defecto para leads fríos
                    )
                    db.add(new_contact)
            db.commit()
            logger.info(f"Ingesta de {len(leads)} leads completada.")

    async def generate_initial_approach(self, lead_name: str, specialty: str) -> str:
        """
        Genera el primer contacto corporativo basado en la plantilla de cumplimiento.
        """
        # Extraer apellido si es posible para personalización formal
        last_name = lead_name.split()[-1] if " " in lead_name else lead_name
        
        mandatory_copy = f"Dr. {last_name}, en Comercializadora Ortho-Cardio conocemos su enfoque en la excelencia quirúrgica. Nos gustaría presentarle las recientes innovaciones de Arthrex en sistemas de fijación y artroscopia que están optimizando los tiempos de quirófano en su especialidad. ¿Tendría espacio para una breve presentación técnica?"
        
        return mandatory_copy


async def run_prospecting_cycle():
    sdr = SDRAgent()
    leads = await sdr.search_prospects()
    await sdr.ingest_leads(leads)

if __name__ == "__main__":
    asyncio.run(run_prospecting_cycle())
