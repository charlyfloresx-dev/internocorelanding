import psycopg2
import sys

# Datos de conexión a AWS
DB_CONFIG = {
    "host": "nexosuite-auth-db.c920i68eetxr.us-east-2.rds.amazonaws.com",
    "database": "postgres",
    "user": "postgres",
    "password": "NexoPassword2026!",
    "port": "5432"
}

def test_connection():
    print("🚀 Iniciando prueba de fuego a AWS RDS...")
    try:
        # Intentar conectar
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Crear un cursor para ejecutar una consulta simple
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        
        print("✅ CONEXIÓN EXITOSA")
        print(f"🔹 Versión de la DB: {db_version[0]}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print("❌ ERROR DE CONEXIÓN")
        print(f"Detalle: {e}")
        return False

if __name__ == "__main__":
    if not test_connection():
        sys.exit(1)