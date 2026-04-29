import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test():
    token = os.getenv("META_ACCESS_TOKEN")
    phone_id = os.getenv("PHONE_NUMBER_ID")
    
    print("--- DIAGNÓSTICO DE META API ---")
    to_number = input("Ingresa tu numero de celular personal con código de país (ej. 52XXXXXXXXXX): ")
    
    url = f"https://graph.facebook.com/v25.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": { "name": "hello_world", "language": { "code": "en_US" } }
    }
    
    print(f"\nEnviando petición a Meta para el número {phone_id}...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        print("\nCÓDIGO DE ESTADO:", response.status_code)
        print("RESPUESTA DE META:")
        import json
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n¡ÉXITO! El mensaje de prueba salió de Meta hacia tu celular.")
            print("Si te llega a WhatsApp, respóndele 'Hola' para destrabar el Webhook.")
        else:
            print("\nERROR DE META. Revisa el mensaje de arriba para saber la causa exacta (ej. falta de método de pago, número restringido, etc).")

asyncio.run(test())
