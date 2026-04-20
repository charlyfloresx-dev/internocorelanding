import os
import sys
import uuid
import io
from pathlib import Path

# Setup Path
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Mock Environment Variables for the test
os.environ["CORE_STORAGE_BACKEND"] = "S3"
os.environ["CORE_S3_ENDPOINT"] = "http://127.0.0.1:4566"
os.environ["CORE_S3_ACCESS_KEY"] = "test"
os.environ["CORE_S3_SECRET_KEY"] = "test"
os.environ["CORE_S3_BUCKET"] = "momentos-assets"

try:
    from common.infrastructure.storage.provider import get_storage_provider
    from common.config import settings
except ImportError as e:
    print(f"Error importing common: {e}")
    sys.exit(1)

def run_storage_test():
    print("=" * 50)
    print("  InternoCore Storage - Multi-tenant S3 Test")
    print("=" * 50)

    provider = get_storage_provider()
    
    # IDs de prueba (Seed data)
    company_id = "9cd9986b-89da-48b7-8733-26a2a1225b01" # Interno Enterprise
    collaborator_id = str(uuid.uuid4())
    
    # Estructura jerárquica: {company_id}/{module}/{sub-path}
    object_key = f"{company_id}/hr/collaborators/{collaborator_id}.jpg"
    
    print(f"[*] Subiendo foto de prueba para colaborador: {collaborator_id}")
    print(f"[*] Tenant Folder (S3 Key): {object_key}")

    # Crear una "imagen" dummy de 1x1 pixel (básicamente datos binarios)
    dummy_data = b"DUMMY_IMAGE_DATA_12345"
    file_obj = io.BytesIO(dummy_data)
    
    try:
        # 1. Subida
        key = provider.upload_file(file_obj, object_key, content_type="image/jpeg")
        print(f"  [OK] Archivo subido exitosamente.")
        
        # 2. Obtención de URL
        url = provider.get_url(key)
        print(f"  [OK] URL Generada (Pre-signed):")
        print(f"       {url[:100]}...") # Truncado para limpieza
        
        # 3. Verificación en LocalStack (usando boto3 directamente para auditar)
        import boto3
        s3 = boto3.client('s3', endpoint_url="http://127.0.0.1:4566", 
                        aws_access_key_id='test', aws_secret_access_key='test')
        
        objs = s3.list_objects_v2(Bucket=settings.S3_BUCKET, Prefix=f"{company_id}/")
        
        if 'Contents' in objs:
            print(f"\n[+] Verificación en Bucket '{settings.S3_BUCKET}':")
            for obj in objs['Contents']:
                print(f"    - Found: {obj['Key']} ({obj['Size']} bytes)")
        else:
            print(f"\n[!] ERROR: El archivo no aparece en el listado de S3.")

    except Exception as e:
        print(f"\n[!] Error durante el test: {str(e)}")
        if "Endpoint Connection Error" in str(e):
            print("    TIP: ¿LocalStack está corriendo? (docker compose -f infrastructure/docker-compose.localstack.yml up -d)")

if __name__ == "__main__":
    run_storage_test()
