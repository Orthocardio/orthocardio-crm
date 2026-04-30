import os
import logging
import json
import asyncio
from typing import List, Dict, Any
from sqlalchemy import text
from database import SessionLocal
from models import QuoteApproval
import google.generativeai as genai
from pdf_generator import OrthoPDF
from pydantic import BaseModel
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv(os.path.join(os.getcwd(), ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logger = logging.getLogger("QuoteAgent")

ADMIN_NUMBERS = [os.getenv("ADMIN_NUMBER_1"), os.getenv("ADMIN_NUMBER_2")]

class ProductMatch(BaseModel):
    code: str
    description: str
    price: float
    reasoning: str
    technical_support: str = ""

class QuoteAgent:
    def __init__(self, api_key: str):
        self.pdf_engine = OrthoPDF()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Reintentando embedding (Intento {retry_state.attempt_number})...")
    )
    def generate_embeddings(self, text: str) -> List[float]:
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            if "429" in str(e): raise e
            logger.error(f"Error generando embedding: {e}")
            return []

    async def find_products(self, query: str) -> List[Dict[Any, Any]]:
        """Busca productos en el catálogo."""
        query_embedding = self.generate_embeddings(query)
        
        with SessionLocal() as db:
            # Extraer palabras clave para búsqueda flexible
            def normalize(w):
                return w.lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").strip("?,.")
            
            ignore_words = ["cotiza", "cotizame", "quiero", "necesito", "precio", "favor", "procedo", "verificar"]
            keywords = [w for w in query.split() if len(w) > 3 and normalize(w) not in ignore_words]
            search_term = keywords[0] if keywords else query


            
            # Consulta compatible con SQLite y PostgreSQL
            if "sqlite" in str(db.get_bind().url):
                search_query = text("""
                    SELECT code, description, price, hospital
                    FROM price_list
                    WHERE description LIKE :like_query
                    LIMIT 10
                """)
            else:
                search_query = text("""
                    SELECT code, description, price, hospital
                    FROM price_list
                    WHERE search_vector @@ to_tsquery('spanish', :query)
                    OR description ILIKE :like_query
                    LIMIT 10
                """)
            
            like_query = f"%{search_term}%"
            params = {"query": search_term, "like_query": like_query}

            print(f"DEBUG - SQL Params: {params}")
            
            try:
                results = db.execute(search_query, params).fetchall()
                print(f"DEBUG - SQL Results: {results}")
            except Exception as e:
                logger.error(f"Error en consulta SQL: {e}")
                results = []


            
            if not results:
                return []
            
            candidates = []
            for r in results:
                # Omitimos RAG temporalmente para agilizar la respuesta en este flujo
                candidates.append({
                    "code": r.code,
                    "description": r.description,
                    "price": float(r.price),
                    "hospital": r.hospital
                })
            
            return await self.refine_product_search(query, candidates)

    async def refine_product_search(self, query: str, products: List[Dict[Any, Any]]) -> Dict[Any, Any]:
        """
        Usa el ModelRouter para seleccionar el producto más adecuado.
        """
        context = "\n".join([f"- {p['description']} (Código: {p['code']})" for p in products])
        prompt = f"El médico solicita: '{query}'.\n\nProductos encontrados:\n{context}\n\nSelecciona el código que mejor coincida. Responde solo el JSON: {{\"selected_code\": \"...\", \"reasoning\": \"...\"}}"
        
        system_instruction = "Eres un experto en productos Arthrex. Responde solo en JSON. NUNCA uses emojis."
        
        try:
            response_text = await router.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True
            )
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Error en refinamiento de producto: {e}")
            return {"selected_code": products[0]["code"], "reasoning": "Fallback al primer resultado."}

    async def create_quote_for_approval(self, phone_number: str, doctor_name: str, hospital: str, items: List[Dict[Any, Any]]):
        """Genera el PDF y crea el registro de aprobación en la BD."""
        pdf_path = await self.generate_quote_pdf(doctor_name, hospital, items)
        
        with SessionLocal() as db:
            new_approval = QuoteApproval(
                contact_phone=phone_number,
                pdf_path=pdf_path,
                status="PENDING_APPROVAL",
                items_json=items
            )
            db.add(new_approval)
            db.commit()
            return new_approval.id, pdf_path

    async def generate_quote_pdf(self, doctor_name: str, hospital: str, items: List[Dict[Any, Any]]) -> str:
        formatted_items = []
        for item in items:
            if isinstance(item, dict):
                formatted_items.append({
                    "code": item.get('code', 'N/A'),
                    "name": item.get('description', 'Producto'),
                    "price": item.get('price', 0.0),
                    "qty": 1
                })
            else:
                formatted_items.append({
                    "code": "N/A",
                    "name": str(item),
                    "price": 0.0,
                    "qty": 1
                })
        return self.pdf_engine.create_quote(doctor_name, hospital, formatted_items)

