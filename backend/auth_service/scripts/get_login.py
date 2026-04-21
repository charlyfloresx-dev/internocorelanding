import requests
import json
import os

# Configuración
URL = "http://localhost:8001/api/v1/auth/login" 
PAYLOAD = {"email": "admin@interno.com", "password": "admin123456"}
OUTPUT_FILE = "last_login_response.json"

print("\n🔍 INSPECCIÓN Y GUARDADO DE RESPUESTA AUTH-SERVICE")
print("-" * 50)

try:
    response = requests.post(URL, json=PAYLOAD)
    print(f"Status Code: {response.status_code}")
    
    # Obtener el diccionario del JSON
    response_data = response.json()
    
    # 1. Imprimir en consola para análisis rápido
    print("\n[RAW JSON RESPONSE]:")
    print(json.dumps(response_data, indent=4, ensure_ascii=False))
    
    # 2. Guardar el JSON en un archivo para el Frontend
    if response.status_code == 200:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Archivo '{OUTPUT_FILE}' guardado exitosamente.")
        
        # Extraer token para confirmar que está presente
        token = response_data.get("data", {}).get("selection_token")
        if token:
            print(f"🔑 Selection Token capturado: {token[:30]}...")
            
except Exception as e:
    print(f"❌ Error de conexión o proceso: {e}")
