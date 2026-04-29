import pandas as pd
import os
import logging
from database import SessionLocal
from models import Message, Contact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnalyticsAgent")

def generate_weekly_report():
    """Analiza la base de datos de Supabase para detectar tendencias de leads."""
    db = SessionLocal()
    try:
        # Extracción de contactos recientes
        contacts = db.query(Contact).all()
        total_leads = len(contacts)
        
        # Identificación de Hospitales con mayor demanda
        hospitals = [c.hospital for c in contacts if c.hospital]
        top_hospitals = pd.Series(hospitals).value_counts().head(5).to_dict()
        
        report = {
            "total_leads": total_leads,
            "top_hospitals": top_hospitals,
            "region_focus": ["Puebla", "Veracruz", "Oaxaca"]
        }
        
        logger.info(f"Reporte generado: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Error en auditoría de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_weekly_report()
