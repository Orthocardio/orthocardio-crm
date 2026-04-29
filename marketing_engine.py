import os
import time
import logging
import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types
import schedule

# Configuración estricta de logging para trazabilidad de errores
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("MarketingEngine")

load_dotenv()

# Extracción de credenciales desde el entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# Cliente Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """Eres un Especialista Técnico de SEO y Redactor Clínico de nivel empresarial para Comercializadora Ortho-Cardio.
REGLAS INQUEBRANTABLES:
- El tono debe ser puramente clínico, técnico y de alta gama.
- Queda estrictamente prohibido el uso de emojis en todo el texto generado.
- Queda estrictamente prohibido el uso de lenguaje informal o frases trilladas de marketing médico (bajo ninguna circunstancia utilices frases como 'héroes de bata blanca' ni similares).
- El contenido debe rotar temáticamente sobre tecnología quirúrgica cardiovascular, soluciones de osteosíntesis y educación médica continua (ej. tecnología Arthrex).
- SEO Local: Debes incluir metadatos estructurados y palabras clave mencionando estratégicamente las zonas de operación: San Pedro Cholula, zona metropolitana de Puebla, Veracruz y Oaxaca."""

def generate_clinical_post() -> str:
    """Invoca a Gemini para redactar el post técnico optimizado."""
    prompt = "Redacta un artículo o post clínico de actualización sobre tecnología de osteosíntesis. Aplica las directrices de SEO local para nuestras zonas operativas."
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Falla de conexión o procesamiento en Gemini Graph: {str(e)}")
        return ""

def publish_to_facebook(text_content: str, media_url: str = None):
    """Envía el payload a Meta Graph API para publicación en Facebook Page."""
    if not PAGE_ACCESS_TOKEN or not PAGE_ID:
        logger.error("Variables PAGE_ACCESS_TOKEN o PAGE_ID no definidas en entorno.")
        return
    
    endpoint = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos" if media_url else f"https://graph.facebook.com/v19.0/{PAGE_ID}/feed"
    
    payload = {
        "access_token": PAGE_ACCESS_TOKEN,
        "message": text_content
    }
    if media_url:
        payload["url"] = media_url
        
    try:
        response = httpx.post(endpoint, data=payload, timeout=20.0)
        response.raise_for_status()
        logger.info(f"Deploy FB exitoso. ID: {response.json().get('id')}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP API Facebook: {e.response.text}")
    except Exception as e:
        logger.error(f"Excepción de Red FB: {str(e)}")

def publish_to_instagram(text_content: str, media_url: str):
    """Ejecuta el protocolo dual de IG (Contenedor -> Publicación)."""
    if not PAGE_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        logger.error("Variables PAGE_ACCESS_TOKEN o INSTAGRAM_ACCOUNT_ID no definidas en entorno.")
        return
        
    if not media_url:
        logger.warning("Bloqueo de ejecución: Instagram for Business requiere de un asset multimedia (media_url).")
        return
        
    try:
        # Fase 1: Creación del Contenedor de Medios
        container_endpoint = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
        container_payload = {
            "access_token": PAGE_ACCESS_TOKEN,
            "image_url": media_url,
            "caption": text_content
        }
        res_container = httpx.post(container_endpoint, data=container_payload, timeout=30.0)
        res_container.raise_for_status()
        creation_id = res_container.json().get("id")
        
        # Fase 2: Ejecución de Publicación
        publish_endpoint = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        publish_payload = {
            "access_token": PAGE_ACCESS_TOKEN,
            "creation_id": creation_id
        }
        res_publish = httpx.post(publish_endpoint, data=publish_payload, timeout=20.0)
        res_publish.raise_for_status()
        logger.info(f"Deploy IG exitoso. ID: {res_publish.json().get('id')}")
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP API Instagram: {e.response.text}")
    except Exception as e:
        logger.error(f"Excepción de Red IG: {str(e)}")

def run_marketing_cycle(media_url: str = None):
    """Orquestador del pipeline de SEO y Redes."""
    logger.info("Iniciando pipeline de Marketing Engine...")
    content = generate_clinical_post()
    if content:
        logger.info("Asset de texto clínico generado de forma exitosa.")
        publish_to_facebook(content, media_url)
        if media_url:
            publish_to_instagram(content, media_url)
    else:
        logger.error("Pipeline abortado. Motor de IA no retornó contenido válido.")

# Definición del Cron Job en memoria
schedule.every().day.at("09:00").do(run_marketing_cycle)

if __name__ == "__main__":
    logger.info("Marketing Engine Online. Ejecutando ciclo de validación en tiempo de arranque...")
    # Ejecución de prueba sin media_url (solo publicará en FB)
    run_marketing_cycle() 
    
    logger.info("Inicializando demonio de Calendarización de Tareas (Schedule/Cron)...")
    while True:
        schedule.run_pending()
        time.sleep(60)
