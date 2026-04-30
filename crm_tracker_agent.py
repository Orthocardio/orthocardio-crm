import os
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from database import SessionLocal
import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv(os.path.join(os.getcwd(), ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CRMTrackerAgent")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class CRMTrackerAgent:
    def __init__(self, api_key: str):
        pass


    async def check_agu_eligibility(self, contact_name: str, status: str):
        """
        Lógica de IA Constitucional: Solo clientes leales califican para AGU.
        """
        if status == "LOYAL_CLIENT":
            last_name = contact_name.split()[-1] if " " in contact_name else contact_name
            alert_msg = f"El Dr. {last_name} ha alcanzado el volumen clínico requerido. ¿Autoriza iniciar el perfilamiento para alta en AGU (Educación Médica)?"

            logger.info(f"ALERTA AGU GENERADA: {alert_msg}")
            # Enrutamiento a administración se manejaría en el orquestador o vía WhatsApp API
            return alert_msg
        return None

    async def generate_followup_draft(self, contact_name: str, hospital: str):
        """Genera un borrador clínico formal para seguimiento usando ModelRouter."""
        from model_router import router
        prompt = f"Redacta un mensaje de seguimiento para el Dr. {contact_name} en {hospital} sobre tecnología Arthrex."
        system_instruction = "Eres el enlace clínico de Ortho-Cardio. Máximo dos líneas. Tono formal médico. Sin emojis."
        
        try:
            return await router.generate_content(prompt=prompt, system_instruction=system_instruction)
        except Exception as e:
            logger.error(f"Falla en seguimiento: {e}")
            return None


    async def run_cycle(self):
        """Ejecuta el ciclo de monitoreo de leads inactivos."""
        logger.info("Iniciando ciclo de monitoreo CRM...")
        threshold = datetime.now() - timedelta(hours=72)
        
        with SessionLocal() as db:
            query = text("""
                SELECT phone_number, name, hospital, status
                FROM contacts
                WHERE last_interaction < :threshold
                AND status IN ('PENDING', 'QUOTING')
                AND (LOWER(hospital) LIKE '%puebla%' OR LOWER(hospital) LIKE '%veracruz%' OR LOWER(hospital) LIKE '%oaxaca%')
            """)
            
            try:
                results = db.execute(query, {"threshold": threshold}).fetchall()
            except Exception as e:
                logger.error(f"Error en consulta de monitoreo: {e}")
                return
            
            if not results:
                logger.info("No se detectaron leads inactivos en las zonas críticas.")
                return

            for lead in results:
                logger.info(f"Procesando seguimiento para: {lead.name} ({lead.hospital})")
                
                try:
                    draft = await self.generate_followup_draft(lead.name, lead.hospital)
                except Exception:
                    draft = None
                
                if draft:
                    update_sql = text("""
                        UPDATE contacts 
                        SET followup_draft = :draft 
                        WHERE phone_number = :pn
                    """)
                    db.execute(update_sql, {"draft": draft, "pn": lead.phone_number})
                    logger.info(f"Borrador inyectado para {lead.name}")
            
            db.commit()
            logger.info("Ciclo de monitoreo completado.")

async def main():
    agent = CRMTrackerAgent(GEMINI_API_KEY)
    while True:
        await agent.run_cycle()
        await asyncio.sleep(86400)

if __name__ == "__main__":
    asyncio.run(main())
