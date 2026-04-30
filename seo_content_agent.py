import os
import json
import logging
import asyncio
from typing import Dict, Any, List
from model_router import router
from database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger("SEOContentAgent")


class SEOContentAgent:
    """
    Agente Especialista SEO y Copywriter.
    Genera contenido optimizado geolocalizado basado en marketing_strategy.json.
    Mantiene la estética premium de Nano Banana prompts.
    """
    def __init__(self):
        self.strategy_file = "marketing_strategy.json"

    def _load_strategy(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.strategy_file):
                with open(self.strategy_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando estrategia para SEO: {e}")
        return {
            "focus_keywords": ["traumatologia", "artroscopia"],
            "priority_locations": ["Puebla", "San Pedro Cholula", "Veracruz", "Oaxaca"],
            "strategic_direction": "Promover innovación en fijación clínica."
        }

    async def generate_seo_post(self, product_topic: str) -> Dict[str, Any]:
        """
        Genera un post optimizado para SEO local y Meta.
        """
        strategy = self._load_strategy()
        
        system_instruction = f"""
        Eres el Especialista SEO de Ortho-Cardio. 
        Debes generar contenido basado en esta estrategia: {json.dumps(strategy)}
        ESTÉTICA VISUAL: Apple Store minimalista / Arthrex Premium (fondos dark, macro texturas).
        SEO LOCAL: Prioriza keywords en {', '.join(strategy.get('priority_locations', []))}.
        RESTRICCIÓN: Cero emojis. Tono clínico formal. Prohibido ofrecer AGU/viajes.
        """
        
        prompt = f"Genera un post sobre: {product_topic}. Incluye headline, cuerpo SEO y nano_banana_prompt."
        
        try:
            response_json = await router.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True
            )
            post_data = json.loads(response_json)
            
            # Persistir en base de datos
            locations = strategy.get('priority_locations', [])
            region_str = ", ".join(locations) if isinstance(locations, list) else str(locations)
            
            with SessionLocal() as db:
                sql = text("""
                    INSERT INTO marketing_campaigns (target_region, copy_headline, copy_body, nano_banana_prompt, status)
                    VALUES (:region, :headline, :body, :prompt, 'PENDING_ASSETS')
                """)
                db.execute(sql, {
                    "region": region_str,
                    "headline": post_data.get('headline') or post_data.get('copy_headline'),
                    "body": post_data.get('body') or post_data.get('copy_body'),
                    "prompt": post_data.get('nano_banana_prompt'),
                })
                db.commit()

            
            return post_data

        except Exception as e:
            logger.error(f"Error generando contenido SEO: {e}")
            return {
                "headline": f"Innovación en {product_topic}",
                "body": "Contenido clínico en desarrollo siguiendo protocolos de excelencia.",
                "nano_banana_prompt": f"Macro render of {product_topic}, clinical dark aesthetics, premium lighting."
            }

if __name__ == "__main__":
    seo = SEOContentAgent()
    asyncio.run(seo.generate_seo_post("Anclajes para Inestabilidad de Hombro"))
