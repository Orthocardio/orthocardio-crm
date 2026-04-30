import os
import json
import logging
from typing import List, Dict, Any
from model_router import router

logger = logging.getLogger("ContentPlanner")

class ContentPlanner:
    """
    Director Creativo IA de Ortho-Cardio.
    Estructura campañas de marketing clínico con prompts de renderizado de ultra-alta gama.
    """
    def __init__(self):
        self.visual_standard_instruction = """
        Los prompts generados para imágenes deben seguir estrictamente el estándar visual de Arthrex fusionado con el minimalismo de una Apple Store. 
        Iluminación de estudio dramática, contrastes premium, fondos oscuros (Carbon) o neutros absolutos. 
        Enfoque macro en texturas de grado médico (titanio, acero, fibra). 
        La imagen debe transmitir seguridad clínica extrema, tecnología de punta y lujo B2B. 
        Queda absolutamente prohibido sugerir gráficos caricaturescos, colores pastel o renders de baja calidad.
        NUNCA uses emojis en ninguna parte de la respuesta.
        """

    async def generate_campaign_structure(self, product_name: str, clinical_advantage: str) -> Dict[Any, Any]:
        """
        Genera la estructura de una campaña incluyendo el prompt para Nano Banana.
        """
        system_prompt = f"""
        Eres el Director Creativo de Ortho-Cardio. Tu tarea es estructurar un post de marketing clínico.
        Debes devolver un JSON con la siguiente estructura:
        {{
            "campaign_title": "...",
            "copy_headline": "Texto principal (máximo 10 palabras)",
            "copy_body": "Cuerpo tcnico (máximo 40 palabras, tono corporativo)",
            "nano_banana_prompt": "Prompt detallado de renderizado basado en las reglas visuales",
            "target_specialty": "Especialidad médica destino"
        }}
        {self.visual_standard_instruction}
        """
        
        user_prompt = f"Producto: {product_name}. Ventaja Clínica: {clinical_advantage}."
        
        try:
            response_text = await router.generate_content(
                prompt=user_prompt,
                system_instruction=system_prompt,
                json_mode=True
            )
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Error en planeación de contenido: {e}")
            return {
                "campaign_title": f"Lanzamiento {product_name}",
                "nano_banana_prompt": f"Macro medical photography of {product_name}, surgical titanium texture, dramatic studio lighting, carbon background, 8k resolution, photorealistic.",
                "error": "Respuesta simplificada por falla en cascada."
            }
