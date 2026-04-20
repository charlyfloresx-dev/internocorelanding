import os
import sys
import uuid
import io
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Setup Paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
HR_SERVICE_DIR = os.path.join(BACKEND_DIR, "hr_service")

if BACKEND_DIR not in sys.path: sys.path.insert(0, BACKEND_DIR)
if HR_SERVICE_DIR not in sys.path: sys.path.insert(0, HR_SERVICE_DIR)

# Mock Environment Variables
os.environ["CORE_STORAGE_BACKEND"] = "S3"
os.environ["CORE_S3_ENDPOINT"] = "http://127.0.0.1:4566"
os.environ["CORE_S3_ACCESS_KEY"] = "test"
os.environ["CORE_S3_SECRET_KEY"] = "test"
os.environ["CORE_S3_BUCKET"] = "momentos-assets"
os.environ["CORE_HR_RFID_SALT"] = "test_salt"

async def test_hr_collaborator_with_photo():
    print("=" * 50)
    print("  HR Service - Create Collaborator with Photo Test")
    print("=" * 50)

    try:
        from hr_service.app.services.collaborator_service import CollaboratorService
        from hr_service.app.domain.entities.collaborator_entities import Collaborator
    except ImportError as e:
        print(f"Error importing HR service: {e}")
        return

    # Mock del Repositorio
    mock_repo = MagicMock()
    mock_repo.get_tenant_config = AsyncMock(return_value=None)
    mock_repo.get_by_internal_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(side_effect=lambda x: x) # Devuelve lo que recibe

    service = CollaboratorService(mock_repo)
    
    company_id = uuid.uuid4()
    data = {
        "internal_id": "TEST-123",
        "full_name": "Test Photo Operator",
        "rfid_tag": "123456789",
        "is_supervisor": False
    }

    # Crear un Mock de UploadFile
    from fastapi import UploadFile
    from starlette.datastructures import Headers
    dummy_photo = UploadFile(
        filename="profile.jpg",
        file=io.BytesIO(b"FAKE_PHOTO_CONTENT"),
        headers=Headers({"content-type": "image/jpeg"})
    )

    print(f"[*] Llamando a create_collaborator para company: {company_id}")
    
    try:
        result = await service.create_collaborator(data, company_id, photo=dummy_photo)
        
        print(f"\n[OK] Colaborador creado en dominio.")
        print(f"     ID: {result.id}")
        print(f"     Photo Path: {result.photo_path}")
        
        if result.photo_path and str(company_id) in result.photo_path:
            print(f"  [PASS] El path contiene el company_id.")
        else:
            print(f"  [FAIL] El path no tiene el formato esperado ({result.photo_path})")

        # Verificar si se subió a LocalStack (auditando el bucket)
        import boto3
        s3 = boto3.client('s3', endpoint_url="http://127.0.0.1:4566", 
                        aws_access_key_id='test', aws_secret_access_key='test')
        
        objs = s3.list_objects_v2(Bucket="momentos-assets", Prefix=f"{company_id}/")
        
        if 'Contents' in objs:
            print(f"\n[+] Verificación en LocalStack:")
            for obj in objs['Contents']:
                print(f"    - Objeto real en S3: {obj['Key']}")
        else:
            print(f"\n[!] ERROR: El archivo no se subió a LocalStack.")

    except Exception as e:
        print(f"\n[!] Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hr_collaborator_with_photo())
