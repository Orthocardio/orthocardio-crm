import os
import logging
import asyncio
import json
from typing import Any, List, Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelRouter")

class ModelRouter:
    """
    Motor de Resiliencia para el Ortho-Cardio CRM.
    Implementa una Cascada de Modelos (Waterfall) para garantizar disponibilidad 24/7.
    """
    def __init__(self):
        load_dotenv(os.path.join(os.getcwd(), ".env"))
        # Cargar Política de Compliance (IA Constitucional)
        try:
            with open(os.path.join(os.getcwd(), "compliance_policy.json"), "r", encoding="utf-8") as f:
                self.compliance_data = json.load(f)
                rules = [r["directive"] for r in self.compliance_data["compliance_rules"]]
                self.compliance_instruction = "\nPOLÍTICA DE CUMPLIMIENTO OBLIGATORIA:\n" + "\n".join(rules)
        except Exception as e:
            logger.error(f"Error cargando política de compliance: {e}")
            self.compliance_instruction = ""

        # Jerarquía de Modelos (Cascada)


        self.model_hierarchy = [
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-1.5-flash",
            "gemma-3-27b-it"
        ]
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.error("No se encontró API_KEY en el entorno.")

    async def generate_content(self, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> str:
        last_exception = None
        
        for model_name in self.model_hierarchy:
            try:
                logger.info(f"Intentando generación con modelo: {model_name}")
                
                # Para modelos que no soportan system_instruction o para asegurar compatibilidad
                full_prompt = f"{self.compliance_instruction}\n\nINSTRUCCIÓN ADICIONAL: {system_instruction}\n\nMENSAJE: {prompt}" if system_instruction else f"{self.compliance_instruction}\n\nMENSAJE: {prompt}"

                
                generation_config = {}
                if json_mode:
                    generation_config["response_mime_type"] = "application/json"
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config
                )
                
                try:
                    response = await asyncio.to_thread(model.generate_content, full_prompt)
                except Exception as e:
                    if "JSON mode" in str(e) and json_mode:
                        logger.warning(f"Modelo {model_name} no soporta JSON mode. Reintentando sin JSON mode.")
                        model = genai.GenerativeModel(model_name=model_name)
                        response = await asyncio.to_thread(model.generate_content, full_prompt)
                    else:
                        raise e
                
                if response and response.text:
                    return response.text.strip()


                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Falla en modelo {model_name}: {error_msg}")
                last_exception = e
                
                # Si el error es 404 (Modelo no existe en este endpoint) o 429 (Cuota), continuamos a la cascada
                if "404" in error_msg or "429" in error_msg or "503" in error_msg:
                    continue
                else:
                    # Otros errores críticos detienen la cascada si es necesario, 
                    # pero para máxima resiliencia, intentamos el siguiente de todos modos.
                    continue
        
        logger.error("Cascada de modelos agotada. No se pudo obtener respuesta.")
        if last_exception:
            raise last_exception
        raise Exception("Error crítico: Jerarquía de modelos falló por completo.")

# Instancia global para ser compartida (Shared Memory Optimization pattern)
router = ModelRouter()
