
import requests
import os
import json

# Configuración de pruebas
URL = "http://localhost:8003/api/v1/prices/import"
CSV_PATH = "backend/master_data_service/scripts/test_pricing_matrix.csv"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzYyNjQwMDAsInN1YiI6IjY5YWE1ZGRjLWJiYWEtNDZlNi1hN2YwLWFlYjRiOTJiNmQzOCIsInR5cCI6ImFjY2VzcyIsImNvbXBhbnlfaWQiOiI5Y2Q5OTg2Yi04OWRhLTQ4YjctODczMy0yNmEyYTEyMjViMDEiLCJncm91cF9pZCI6bnVsbCwicm9sZV9uYW1lcyI6WyJhZG1pbiJdLCJzY29wZXMiOlsiKiJdLCJtb2R1bGVzIjpbImF1dGhfY29yZSIsImludmVudG9yeV9jb3JlIl0sInN0YXR1cyI6IlRSSUFMIiwicmVhZG9ubHkiOmZhbHNlLCJjb3JyZWxhdGlvbl9pZCI6IjAzYjdiN2JkLWJhYjYtNDg0ZC1iMTVhLWIwNzE5NGJjMWM2ZiJ9.MAK1GMGR0qUAw_gNEKRwRudXP_4R4AL9sDoeRG2wGyY"

def test_import():
    print(f"--- Iniciando Validación de Importación ---")
    print(f"Archivo: {CSV_PATH}")
    
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: No se encuentra el archivo CSV en {CSV_PATH}")
        return

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    try:
        with open(CSV_PATH, "rb") as f:
            files = {"file": ("test_pricing_matrix.csv", f, "text/csv")}
            response = requests.post(URL, headers=headers, files=files)
            
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Respuesta:\n{json.dumps(result, indent=4, ensure_ascii=False)}")
        
        if result.get("status") == "success":
            print("\n[OK] VALIDACION EXITOSA: Los precios han sido importados con exito.")
        else:
            print("\n[ERROR] FALLO EN VALIDACION: Revisa el error arriba.")
            
    except Exception as e:
        print(f"ERROR DE CONEXIÓN: {e}")

if __name__ == "__main__":
    test_import()
