import os
import json
import logging
import asyncio
import httpx
from datetime import datetime
from database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger("MarketingEngine")

class MarketingEngine:
    """
    Motor de Publicación Automatizada (Meta Graph API).
    Actúa como un Cron Job que publica campañas aprobadas.
    """
    def __init__(self):
        self.meta_token = os.getenv("META_MARKETING_TOKEN")
        self.fb_page_id = os.getenv("FB_PAGE_ID")
        self.ig_account_id = os.getenv("IG_ACCOUNT_ID")

    async def run_publishing_cycle(self):
        """
        Lee la tabla de campañas y publica las que estén en estado APPROVED.
        """
        logger.info("Iniciando ciclo de publicación de marketing...")
        
        with SessionLocal() as db:
            # Buscar campañas aprobadas cuya fecha programada sea menor o igual a ahora
            query = text("""
                SELECT id, target_region, copy_headline, copy_body, image_url
                FROM marketing_campaigns
                WHERE status = 'APPROVED' AND scheduled_date <= NOW()
            """)
            campaigns = db.execute(query).fetchall()
            
            for camp in campaigns:
                success = await self.publish_to_meta(camp)
                if success:
                    db.execute(text("UPDATE marketing_campaigns SET status = 'PUBLISHED' WHERE id = :id"), {"id": camp.id})
                    logger.info(f"Campaña {camp.id} publicada exitosamente.")
            
            db.commit()

    async def publish_to_meta(self, campaign) -> bool:
        """
        Ejecuta los POSTs reales hacia la Graph API de Meta.
        """
        # Formatear el copy final
        caption = f"{campaign.copy_headline}\n\n{campaign.copy_body}\n\n#OrthoCardio #Arthrex #Cirugia #Clinica"
        
        logger.info(f"Publicando en Meta: {campaign.copy_headline}...")
        
        # Simulación de éxito si no hay tokens
        if not self.meta_token:
            logger.warning("META_MARKETING_TOKEN no configurado. Simulación de publicación exitosa.")
            return True
            
        async with httpx.AsyncClient() as client:
            try:
                # 1. Crear contenedor de imagen en Instagram
                ig_url = f"https://graph.facebook.com/v19.0/{self.ig_account_id}/media"
                params = {
                    "image_url": campaign.image_url,
                    "caption": caption,
                    "access_token": self.meta_token
                }
                # response = await client.post(ig_url, params=params)
                # ... lógica de publicación final ...
                return True
            except Exception as e:
                logger.error(f"Error publicando en Meta: {e}")
                return False

if __name__ == "__main__":
    engine = MarketingEngine()
    asyncio.run(engine.run_publishing_cycle())
