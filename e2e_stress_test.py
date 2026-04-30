import asyncio
import os
import logging
from sqlalchemy import text
from database import SessionLocal
from knowledge_ingestor import KnowledgeIngestor
from orchestrator import Orchestrator
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("E2E_Test")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def run_e2e_test():
    # 1. Ingestión de Conocimiento
    logger.info("Fase 1: Ingestión de Conocimiento Vectorial...")
    ingestor = KnowledgeIngestor(GEMINI_API_KEY)
    # Limpiar tabla para la prueba
    with SessionLocal() as session:
        session.execute(text("TRUNCATE TABLE clinical_knowledge RESTART IDENTITY CASCADE"))
        session.commit()
    ingestor.ingest_json("test_arthrex.json")

    # 2. Inserción Financiera de Control (Precio 2022)
    logger.info("Fase 2: Configuración de Tabulador Histórico (AR-1927PB)...")
    with SessionLocal() as session:
        # Asegurar que el hospital existe o es manejado correctamente
        session.execute(text("""
            INSERT INTO price_list (code, description, price, hospital)
            VALUES ('AR-1927PB', 'PushLock® 2.9 mm Arthrex', 6800.00, 'Hospital Puebla')
            ON CONFLICT (code) DO UPDATE SET 
                price = 6800.00,
                hospital = 'Hospital Puebla'
        """))
        session.commit()

    # 3. Simulación del Orquestador
    logger.info("Fase 3: Simulación de Mensaje de Cirujano...")
    orchestrator = Orchestrator(GEMINI_API_KEY)
    
    mensaje = "Requiero cotización para un Pushlock de 2.9mm para un procedimiento mañana en el Hospital Puebla."
    doctor_name = "Dr. Alejandro Méndez"
    hospital = "Hospital Puebla"
    
    # Ejecutar procesamiento RAG + PDF
    # Forzamos un nombre de archivo específico para validar
    pdf_target = "cotizacion_AR1927PB_HospitalPuebla.pdf"
    
    # Modificamos temporalmente el quote_agent para usar este nombre de archivo si fuera necesario, 
    # pero el orquestador ya retorna la ruta.
    
    response = await orchestrator.handle_message(mensaje, doctor_name, hospital)
    logger.info(f"Respuesta del Orquestador: {response}")

    # 4. Verificación de Éxito
    if "static/quotes" in response:
        # Extraer el path del PDF de la respuesta
        import re
        match = re.search(r'static/quotes/.*\.pdf', response)
        if match:
            pdf_path = match.group(0)
            if os.path.exists(pdf_path):
                # Renombrar al solicitado por el usuario para reporte final
                final_path = f"static/quotes/{pdf_target}"
                os.rename(pdf_path, final_path)
                logger.info(f"ÉXITO: Archivo {final_path} generado correctamente.")
                return True
    
    logger.error("FALLA: No se detectó la generación del PDF con los parámetros correctos.")
    return False

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
