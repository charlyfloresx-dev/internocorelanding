import requests
import subprocess
import json

BASE_URL = "http://localhost:8000/api/v1"
TRACE_ID_HEADER = "X-Trace-ID"

def check_db_tables():
    print("🔍 [1/4] Verificando tablas en PostgreSQL...")
    cmd = "docker exec interno-postgres-db-1 psql -U user_admin -d internocore -c '\\dt'"
    result = subprocess.check_output(cmd, shell=True).decode()
    tables = ["users", "companies"]
    for table in tables:
        if table in result:
            print(f"  ✅ Tabla '{table}' detectada.")
        else:
            print(f"  ❌ Tabla '{table}' NO ENCONTRADA.")

def check_health_and_format():
    print("\n🔍 [2/4] Verificando Formato de Respuesta Homologado...")
    try:
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        
        # Validar estructura StandardResponse
        keys = ["status", "data", "message", "meta"]
        if all(k in data for k in keys):
            print("  ✅ Estructura StandardResponse: CORRECTA")
        else:
            print("  ❌ Estructura StandardResponse: INVÁLIDA")
            
        if TRACE_ID_HEADER in response.headers:
            print(f"  ✅ Middleware de Trazabilidad: ACTIVO ({response.headers[TRACE_ID_HEADER]})")
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")

def check_security_hash():
    print("\n🔍 [3/4] Verificando Integridad de Hash (Bcrypt)...")
    cmd = "docker exec interno-postgres-db-1 psql -U user_admin -d internocore -c \"SELECT hashed_password FROM users LIMIT 1;\""
    hash_val = subprocess.check_output(cmd, shell=True).decode()
    if "$2b$12$" in hash_val or "$2y$12$" in hash_val:
        print("  ✅ Algoritmo Bcrypt (Cost 12): DETECTADO")
    else:
        print("  ❌ Hash corrupto o algoritmo incorrecto.")

if __name__ == "__main__":
    print("=== AUDITORÍA DE ESTADO: INTERNO-CORE AUTH-SERVICE ===\n")
    check_db_tables()
    check_health_and_format()
    check_security_hash()
    print("\n=== FIN DE LA AUDITORÍA ===")
