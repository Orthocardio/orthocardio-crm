import os
import logging
from typing import List, Dict, Any
from sqlalchemy import text
from database import SessionLocal
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KnowledgeIngestor")

class KnowledgeIngestor:
    def __init__(self, api_key: str):
        # La configuración se hace a nivel global
        pass

    def generate_embeddings(self, text: str) -> List[float]:
        """Genera embeddings vectoriales usando models/gemini-embedding-001."""
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']

        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return []

    def save_clinical_data(self, product_code: str, content: str, metadata: Dict[str, Any]):
        """Guarda el fragmento de conocimiento y su embedding en Supabase."""
        embedding = self.generate_embeddings(content)
        if not embedding:
            return False

        try:
            with SessionLocal() as db:
                sql = text("""
                    INSERT INTO clinical_knowledge (product_code, content, embedding, metadata_json)
                    VALUES (:product_code, :content, :embedding, :metadata_json)
                """)
                # En Supabase/Postgres con pgvector el formato es [1,2,3]
                # En SQLite local lo guardamos como string si no hay extensión vector
                db.execute(sql, {
                    "product_code": product_code,
                    "content": content,
                    "embedding": str(embedding), # SQLAlchemy + pgvector manejará esto
                    "metadata_json": metadata
                })
                db.commit()
            return True
        except Exception as e:
            logger.error(f"Error guardando conocimiento clínico: {e}")
            db.rollback()
            return False
