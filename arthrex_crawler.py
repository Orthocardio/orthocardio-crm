import asyncio
import os
import random
import logging
import json
from playwright.async_api import async_playwright
import google.generativeai as genai
from database import SessionLocal
from sqlalchemy import text
from knowledge_ingestor import KnowledgeIngestor
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv(os.path.join(os.getcwd(), ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ArthrexCrawler")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class ArthrexCrawler:
    def __init__(self, api_key: str):
        self.ingestor = KnowledgeIngestor(api_key=api_key)
        self.base_url = "https://www.arthrex.com/search?q="

    async def get_pending_codes(self):
        """Obtiene códigos 'AR-' de PriceList que no están en clinical_knowledge."""
        with SessionLocal() as session:
            sql = text("""
                SELECT p.code 
                FROM price_list p
                LEFT JOIN clinical_knowledge k ON p.code = k.product_code
                WHERE p.code LIKE 'AR-%' AND k.id IS NULL
                LIMIT 20
            """)
            try:
                results = session.execute(sql).fetchall()
                return [r.code for r in results]
            except Exception:
                return []

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Reintentando estructuración Gemini (Intento {retry_state.attempt_number})...")
    )
    async def structure_raw_text(self, raw_text: str, product_code: str):
        """Usa Gemini 2.5 Flash para extraer JSON estructurado con reintentos."""
        prompt = f"""
        Extrae y resume la Técnica Quirúrgica, Indicaciones y Ventajas Clínicas de este texto crudo obtenido de la web de Arthrex para el producto {product_code}.
        
        REGLAS:
        - Tono clínico, formal, sin emojis.
        - Si no encuentras un campo, deja el string vacío.
        - Devuelve EXCLUSIVAMENTE un objeto JSON con las claves: product_code, name, surgical_technique, clinical_advantage, video_url.
        
        TEXTO CRUDO:
        {raw_text[:8000]}
        """

        try:
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            return json.loads(response.text)
        except Exception as e:
            if "429" in str(e):
                logger.error("Límite de cuota en Crawler.")
                raise e
            logger.error(f"Error estructurando texto con Gemini para {product_code}: {e}")
            return None

    async def crawl_and_process(self):
        codes = await self.get_pending_codes()
        if not codes:
            logger.info("No hay códigos pendientes para rastrear.")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            page = await context.new_page()

            for code in codes:
                try:
                    logger.info(f"Rastreando producto: {code}")
                    search_url = f"{self.base_url}{code}"
                    
                    await page.goto(search_url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    raw_text = await page.evaluate("document.body.innerText")
                    
                    try:
                        structured_data = await self.structure_raw_text(raw_text, code)
                    except Exception:
                        structured_data = None
                    
                    if structured_data:
                        content_for_rag = f"TÉCNICA QUIRÚRGICA: {structured_data.get('surgical_technique')}\n\nVENTAJAS CLÍNICAS: {structured_data.get('clinical_advantage')}"
                        
                        metadata = {
                            "name": structured_data.get("name"),
                            "video_url": structured_data.get("video_url"),
                            "source": page.url
                        }
                        
                        success = self.ingestor.save_clinical_data(code, content_for_rag, metadata)
                        if success:
                            logger.info(f"Ingestión exitosa para {code}")
                        else:
                            logger.error(f"Falla en ingestión para {code}")
                    
                except Exception as e:
                    logger.error(f"Error procesando {code}: {e}")
                
                await asyncio.sleep(random.uniform(5, 10))

            await browser.close()

if __name__ == "__main__":
    crawler = ArthrexCrawler(GEMINI_API_KEY)
    asyncio.run(crawler.crawl_and_process())
