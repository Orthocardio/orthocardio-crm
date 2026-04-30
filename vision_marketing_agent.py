import os
import logging
from google import genai
from google.genai import types
from marketing_engine import run_marketing_cycle

logger = logging.getLogger("VisionMarketingAgent")

class VisionMarketingAgent:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def process_video_asset(self, video_path: str):
        """Analiza el video y dispara el ciclo de marketing."""
        if not os.path.exists(video_path):
            logger.error(f"Video no encontrado: {video_path}")
            return

        logger.info(f"Procesando video clínico: {video_path}")
        
        # Subir video a Gemini (File API)
        video_file = self.client.files.upload(path=video_path)
        
        prompt = """
        Analiza este video de tecnología médica/quirúrgica de Ortho-Cardio.
        Genera tres variantes de copy estructurado para redes sociales (FB/IG):
        1. VARIANTE CLÍNICA: Enfoque en precisión quirúrgica y resultados para el paciente.
        2. VARIANTE LOGÍSTICA: Enfoque en disponibilidad inmediata y eficiencia en quirófano.
        3. VARIANTE EDUCATIVA: Enfoque en actualización tecnológica para cirujanos.
        
        REGLAS:
        - Sin emojis.
        - Sin lenguaje informal.
        - Tono de alta gama.
        - SEO local sutil (Puebla, Veracruz, Oaxaca).
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-pro',
                contents=[prompt, video_file]
            )
            
            generated_copies = response.text
            logger.info("Copies generados exitosamente a partir del video.")
            
            # Aquí se podría automatizar la publicación de una de las variantes
            # Por ahora, simularemos el disparo del marketing engine con la primera variante
            # run_marketing_cycle(media_url=video_path) # Necesitaría una URL pública para Meta
            
            return generated_copies
        except Exception as e:
            logger.error(f"Error en Vision Analysis: {e}")
            return None
