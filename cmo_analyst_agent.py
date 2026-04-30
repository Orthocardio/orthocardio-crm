import os
import json
import logging
import asyncio
from typing import Dict, Any, List
from model_router import router

logger = logging.getLogger("CMOAnalystAgent")

class CMOAnalystAgent:
    """
    Agente Analista de Rendimiento (CMO).
    Analiza métricas de Meta Ads y Google Analytics para definir la estrategia de marketing.
    Estructura la directriz estratégica en marketing_strategy.json.
    """
    def __init__(self):
        self.strategy_file = "marketing_strategy.json"

    async def fetch_performance_data(self) -> Dict[str, Any]:
        """
        Mock de datos de rendimiento (Meta Ads / Google Analytics).
        """
        return {
            "meta_ads": {
                "cpc": 0.45,
                "cpl": 12.50,
                "top_performing_creatives": ["Macro-Titanium-Ankle", "Clinical-Articulations-Dark"],
                "best_regions": ["Puebla", "Veracruz"]
            },
            "analytics": {
                "top_keywords": ["cirugia artroscopica puebla", "anclajes de titanio arthrex"],
                "conversion_rate": 0.035
            }
        }

    async def define_strategy(self):
        """
        Analiza los datos y genera la directriz estratégica usando ModelRouter.
        """
        metrics = await self.fetch_performance_data()
        
        prompt = f"""
        Analiza las siguientes métricas de marketing para Ortho-Cardio:
        {json.dumps(metrics, indent=2)}
        
        Define la estrategia de contenido para la próxima semana.
        Criterios: Foco en ROI, especialidades de traumatología y geolocalización.
        """
        
        system_instruction = "Eres el CMO de Ortho-Cardio. Tu salida debe ser un JSON estricto con las claves: 'focus_keywords', 'priority_locations', 'strategic_direction' y 'content_pillars'."
        
        try:
            strategy_json = await router.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True
            )
            
            with open(self.strategy_file, "w", encoding="utf-8") as f:
                f.write(strategy_json)
            
            logger.info("Estrategia de marketing actualizada exitosamente.")
            return json.loads(strategy_json)
        except Exception as e:
            logger.error(f"Error definiendo estrategia CMO: {e}")
            return None

if __name__ == "__main__":
    cmo = CMOAnalystAgent()
    asyncio.run(cmo.define_strategy())
