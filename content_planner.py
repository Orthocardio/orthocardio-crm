import os
import json
import logging
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configuración estricta de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ContentPlanner")

# Carga de entorno
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.critical("Variable de entorno GEMINI_API_KEY no definida.")
    exit(1)

# Inicialización del cliente moderno de GenAI
client = genai.Client(api_key=GEMINI_API_KEY)

# Esquemas de datos para garantizar Structured Output (JSON Válido estricto)
class PostPlan(BaseModel):
    dia_publicacion: str
    pilar_estrategico: str
    copy_sugerido: str
    idea_visual_para_video: str
    hashtags_seo_local: str

class WeeklyMatrix(BaseModel):
    publicaciones: list[PostPlan]

SYSTEM_PROMPT = """Actúas como Director de Marketing Clínico de Comercializadora Ortho-Cardio.
REGLAS INQUEBRANTABLES:
- El lenguaje de todos los campos, especialmente 'copy_sugerido', debe ser puramente clínico, corporativo y de lujo tecnológico.
- Queda absolutamente prohibido el uso de emojis en cualquier campo generado.
- Queda estrictamente prohibida la utilización de frases como 'héroes de bata blanca' o cualquier otra expresión emotiva, coloquial o informal.
- Los copies y hashtags deben estar optimizados para el posicionamiento SEO local, haciendo mención sutil pero estratégica a las zonas de operación: San Pedro Cholula, Puebla, Veracruz y Oaxaca.
- Tu objetivo es diseñar una matriz de contenido estratégico enfocada exclusivamente al B2B médico, tecnología quirúrgica e insumos especializados."""

def generate_weekly_matrix():
    """Invoca el modelo gemini-1.5-pro para la planeación analítica y exportación JSON."""
    prompt = """Genera un calendario semanal de 4 publicaciones. 
Debes rotar obligatoriamente entre los siguientes 4 pilares estratégicos:
1. Innovación en tecnología quirúrgica (soluciones de osteosíntesis, artroscopia).
2. Educación médica continua y capacitación técnica en quirófano.
3. Eficiencia logística, trazabilidad y control de inventario hospitalario.
4. Disponibilidad de equipo crítico y casos de éxito logístico.

Retorna la matriz estructurada respetando milimétricamente las restricciones de formato, tono y SEO local geolocalizado."""

    logger.info("Iniciando procesamiento analítico con gemini-1.5-pro...")
    
    try:
        # Se aprovecha la capacidad de response_schema para evitar expresiones regulares o fallos de parsing
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=WeeklyMatrix,
                temperature=0.3  # Reducción de varianza para forzar rigor corporativo
            )
        )
        
        raw_json = response.text
        
        # Validación final de estructura JSON
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error(f"Falla crítica: El motor no retornó un JSON válido. Detalle: {str(e)}")
            return
            
        output_file = "matriz_semanal.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Ciclo completado con éxito. Matriz estructural guardada en disco: {output_file}")
        
    except Exception as e:
        logger.error(f"Falla de ejecución en la orquestación del modelo: {str(e)}")

if __name__ == "__main__":
    generate_weekly_matrix()
