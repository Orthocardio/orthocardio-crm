from services.agents.factory import MarketingAgent, SalesAgent, SourcingAgent
from typing import Dict, Any

class Orchestrator:
    def __init__(self):
        self.marketing = MarketingAgent()
        self.sales = SalesAgent()
        self.sourcing = SourcingAgent()

    async def route_and_execute(self, input_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica de ruteo simplificada (esto puede ser una llamada a Gemini también)
        text_lower = input_text.lower()
        
        if any(word in text_lower for word in ['precio', 'costo', 'comprar', 'stent', 'protesis', 'disponible']):
            agent = self.sales
            agent_name = "SALES_SDR"
        elif any(word in text_lower for word in ['campaña', 'instagram', 'anuncio', 'foto', 'marketing']):
            agent = self.marketing
            agent_name = "MARKETING_CREATIVE"
        elif any(word in text_lower for word in ['stock', 'inventario', 'pedir', 'proveedor', 'alibaba']):
            agent = self.sourcing
            agent_name = "SOURCING_LOGISTICS"
        else:
            agent = self.sales # Default a ventas para no perder leads
            agent_name = "SALES_SDR"

        response_text = await agent.run(input_text, context)
        
        return {
            "agent": agent_name,
            "response": response_text,
            "tasks": [f"Tarea ejecutada por {agent_name} basada en intención detectada."]
        }
