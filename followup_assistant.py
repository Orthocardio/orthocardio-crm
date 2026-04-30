import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from database import SessionLocal

logger = logging.getLogger("FollowUpAssistant")

class FollowUpAssistant:
    def check_idle_leads(self):
        """Identifica leads sin contacto por >72h en zonas clave."""
        threshold = datetime.now() - timedelta(hours=72)
        
        with SessionLocal() as db:
            query = text("""
                SELECT name, phone_number, last_interaction, hospital
                FROM contacts
                WHERE last_interaction < :threshold
                AND (hospital ILIKE '%Puebla%' OR hospital ILIKE '%Veracruz%' OR hospital ILIKE '%Oaxaca%')
                AND is_ai_active = true
            """)
            
            results = db.execute(query, {"threshold": threshold}).fetchall()
            
            if not results:
                logger.info("No se encontraron leads inactivos en las zonas críticas.")
                return []
            
            alerts = []
            for lead in results:
                alert = {
                    "contact": lead.name,
                    "phone": lead.phone_number,
                    "last_seen": lead.last_interaction,
                    "zone": lead.hospital,
                    "suggested_message": f"Estimado {lead.name}, confirmamos la disponibilidad de insumos en {lead.hospital}. ¿Reclama actualización de catálogo?"
                }
                alerts.append(alert)
                logger.warning(f"ALERTA SEGUIMIENTO: {lead.name} ({lead.hospital}) inactivo desde {lead.last_interaction}")
                
            return alerts

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    assistant = FollowUpAssistant()
    assistant.check_idle_leads()
