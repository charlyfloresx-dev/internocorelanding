import os
import boto3
from pathlib import Path
from validate_envs import parse_env_file, find_env_files

# Configuraciones Base
# Puedes sobrescribir usando variables de entorno o cambiando esto temporalmente
USE_LOCALSTACK = os.environ.get("USE_LOCALSTACK", "true").lower() == "true"
LOCALSTACK_ENDPOINT = "http://127.0.0.1:4566"
REGION_NAME = "us-east-1"
AWS_PROFILE = os.environ.get("AWS_PROFILE", "default") # Para produccion 

# Listas de deduplicación global basadas en auditoria
# Si alguna de estas llaves es detectada, se asume su prefijo: /interno-core/global/
GLOBAL_KEYS = [
    "CORE_DATABASE_URL",
    "CORE_SECRET_KEY",
    "CORE_ALGORITHM",
    "CORE_ADMIN_MASTER_KEY",
    "CORE_STRIPE_PUBLIC_KEY",
    "CORE_STRIPE_SECRET_KEY",
    "CORE_STRIPE_WEBHOOK_SECRET",
    "CORE_STRIPE_PRODUCT_ID"
]

def get_ssm_client():
    if USE_LOCALSTACK:
        print("[!] Usando AWS LocalStack SSM Parameter Store")
        return boto3.client(
            'ssm', 
            endpoint_url=LOCALSTACK_ENDPOINT,
            region_name=REGION_NAME,
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
    else:
        print(f"[!] Usando AWS Cloud SSM Parameter Store (Profile: {AWS_PROFILE})")
        session = boto3.Session(profile_name=AWS_PROFILE)
        return session.client('ssm', region_name=REGION_NAME)

def put_parameter(client, param_name, param_value):
    try:
        response = client.put_parameter(
            Name=param_name,
            Value=param_value,
            Type='String' if USE_LOCALSTACK else 'SecureString', # LOW-COST SECURE TIER (gratuito vs SecretsManager)
            Overwrite=True
        )
        print(f"  [OK] Creado/Actualizado -> {param_name}")
    except Exception as e:
        print(f"  [ERR] No se pudo crear {param_name}: {str(e)}")

def migrate_env_vars():
    print("=" * 50)
    print(" AWS Systems Manager (SSM) - Parameter Store Migration ")
    print("=" * 50)
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_files = find_env_files(project_root)
    ssm_client = get_ssm_client()
    
    migrated_globals = set()
    
    for file_path in env_files:
        service_name = "general"
        parent_dir = os.path.basename(os.path.dirname(file_path))
        if parent_dir.endswith("_service"):
             service_name = parent_dir.split("_service")[0] # auth, hr, etc
             
        print(f"\nMigrando desde: {file_path} (Service: {service_name})")
        env_vars = parse_env_file(file_path)
        
        for key, value in env_vars.items():
            param_name = ""
            if key in GLOBAL_KEYS:
                param_name = f"/interno-core/global/{key.lower()}"
                if param_name in migrated_globals:
                    print(f"  [SKIPPED] {param_name} ya fue migrado globalmente.")
                    continue
                migrated_globals.add(param_name)
            elif key.startswith("CORE_"):
                 param_name = f"/interno-core/global/{key.lower().replace('core_', '')}"
            else:
                 param_name = f"/interno-core/{service_name}/{key.lower()}"
                 
            put_parameter(ssm_client, param_name, value)
            
    print("\n[CONCLUSION] Migración completada. Puedes validar en la consola de SSM.")

if __name__ == "__main__":
    migrate_env_vars()
