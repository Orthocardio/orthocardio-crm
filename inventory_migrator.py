import os
import pandas as pd
import logging
from sqlalchemy import text
from database import engine, SessionLocal
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InventoryMigrator")

EXCEL_PATH = "c:/Users/CarlosCortes/Desktop/ORTHOCARDIO MARKETING Y CRM/Datos/Lista Precios para app.xlsx"

def migrate_inventory():
    if not os.path.exists(EXCEL_PATH):
        logger.error(f"Archivo no encontrado: {EXCEL_PATH}")
        return

    try:
        logger.info("Leyendo catálogo desde Excel...")
        df = pd.read_excel(EXCEL_PATH)
        
        # Mapeo y limpieza de columnas
        # Columnas Excel: ['Codigo', 'DESCRIPCION', 'PRECIO', 'Hospital', 'Codigo Alterno']
        df = df.rename(columns={
            'Codigo': 'code',
            'DESCRIPCION': 'description',
            'PRECIO': 'price',
            'Hospital': 'hospital',
            'Codigo Alterno': 'alternative_code'
        })
        
        # Normalización
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)
        df['description'] = df['description'].astype(str).str.strip()
        df['code'] = df['code'].astype(str).str.strip()
        
        # Eliminar duplicados de código para evitar errores de llave primaria si los hay
        df = df.drop_duplicates(subset=['code'])

        logger.info(f"Preparando carga masiva de {len(df)} productos...")
        
        # Convertir a lista de diccionarios para SQLAlchemy
        records = df.to_dict(orient='records')
        
        with SessionLocal() as session:
            # Limpiar tabla antes de la carga (opcional, pero recomendado para frescura total)
            session.execute(text("TRUNCATE TABLE price_list RESTART IDENTITY CASCADE"))
            
            # Bulk Insert usando el motor directamente para máxima velocidad
            from sqlalchemy.dialects.postgresql import insert
            from models import Base # Asumiremos que definimos PriceList en models.py si es necesario, 
                                   # o usaremos SQL crudo para evitar dependencias circulares complejas en scripts de migración.
            
            # Usando SQL crudo para el script de migración para mayor control
            sql = text("""
                INSERT INTO price_list (code, description, price, hospital, alternative_code)
                VALUES (:code, :description, :price, :hospital, :alternative_code)
                ON CONFLICT (code) DO UPDATE SET
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    hospital = EXCLUDED.hospital,
                    alternative_code = EXCLUDED.alternative_code
            """)
            
            # Dividir en lotes para no saturar la conexión
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                session.execute(sql, batch)
                logger.info(f"Cargado lote {i // batch_size + 1}...")
            
            session.commit()
            logger.info("Migración completada exitosamente.")

    except Exception as e:
        logger.error(f"Falla crítica en migración: {e}")

if __name__ == "__main__":
    migrate_inventory()
