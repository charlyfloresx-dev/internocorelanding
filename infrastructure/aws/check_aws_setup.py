
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def check_s3_bucket_status():
    """
    Intenta listar los buckets de S3 y confirma si 'internocore-static-files-3709' es público.
    """
    print("1. Verificando estado del bucket S3 'internocore-static-files-3709'...")
    bucket_name = "internocore-static-files-3709"
    
    try:
        s3_client = boto3.client('s3')
        
        # Primero, validar que podemos listar buckets para confirmar conectividad básica.
        s3_client.list_buckets()

        # Segundo, verificar el estado de la política de acceso público del bucket específico.
        try:
            policy_status = s3_client.get_bucket_policy_status(Bucket=bucket_name)
            is_public = policy_status.get('PolicyStatus', {}).get('IsPublic', False)
            
            if is_public:
                print(f"   [DETALLE] El bucket '{bucket_name}' es PÚBLICO según su política.")
                print("   PASSED: Se confirmó el estado del bucket S3 y es público.")
            else:
                print(f"   [DETALLE] El bucket '{bucket_name}' NO es público.")
                print("   FAILED: El bucket S3 existe pero no es público.")

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                print(f"   [ERROR] El bucket '{bucket_name}' no existe.")
                print("   FAILED: No se pudo encontrar el bucket S3.")
            elif e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                print(f"   [DETALLE] El bucket '{bucket_name}' no tiene una política de bucket, por lo tanto NO es público.")
                print("   FAILED: El bucket S3 existe pero no es público.")
            else:
                print(f"   [ERROR] Error inesperado al verificar la política del bucket: {e}")
                print("   FAILED: Error al verificar el bucket S3.")
                
    except NoCredentialsError:
        print("   [ERROR] No se encontraron credenciales de AWS. Asegúrese de configurar sus credenciales.")
        print("   FAILED: No se pudo conectar a AWS.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"   [ERROR] Error de permisos o configuración al conectar con S3: {error_code}.")
        print("   FAILED: No se pudo verificar el bucket S3.")
    except Exception as e:
        print(f"   [ERROR] Ocurrió un error inesperado: {e}")
        print("   FAILED: No se pudo verificar el bucket S3.")

def check_secrets_manager_access():
    """
    Intenta leer un secreto de AWS Secrets Manager para validar permisos de lectura.
    """
    print("\n2. Verificando acceso de lectura a AWS Secrets Manager...")
    primary_secret_id = "internocore/config-3709"
    
    try:
        secrets_client = boto3.client('secretsmanager')
        
        try:
            # Intento 1: Leer el secreto principal.
            secrets_client.get_secret_value(SecretId=primary_secret_id)
            print(f"   [DETALLE] Se accedió exitosamente al secreto '{primary_secret_id}'.")
            print("   PASSED: Se validaron los permisos de lectura en Secrets Manager.")
            return

        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                # Si el error es algo distinto a "no encontrado" (ej. AccessDenied), es un fallo.
                print(f"   [ERROR] Error al intentar leer '{primary_secret_id}': {e.response['Error']['Message']}")
                print("   FAILED: No se pudo validar el permiso de lectura en Secrets Manager.")
                return

            # Si el secreto principal no se encontró, buscar un secreto de RDS.
            print(f"   [INFO] El secreto '{primary_secret_id}' no fue encontrado. Buscando un secreto de RDS como alternativa.")
            
            paginator = secrets_client.get_paginator('list_secrets')
            rds_secret_id = None
            for page in paginator.paginate():
                for secret in page['SecretList']:
                    # Heurística para encontrar un secreto de RDS
                    if 'rds' in secret['Name'].lower() or ('Tags' in secret and any('rds' for tag in secret['Tags'])):
                        rds_secret_id = secret['Name']
                        break
                if rds_secret_id:
                    break
            
            if rds_secret_id:
                print(f"   [INFO] Se encontró un secreto de tipo RDS: '{rds_secret_id}'. Intentando leerlo...")
                secrets_client.get_secret_value(SecretId=rds_secret_id)
                print(f"   [DETALLE] Se accedió exitosamente al secreto alternativo '{rds_secret_id}'.")
                print("   PASSED: Se validaron los permisos de lectura en Secrets Manager.")
            else:
                print("   [ERROR] No se encontró el secreto primario ni un secreto alternativo de RDS.")
                print("   FAILED: No se pudo validar el permiso de lectura en Secrets Manager.")

    except NoCredentialsError:
        print("   [ERROR] No se encontraron credenciales de AWS. Asegúrese de configurar sus credenciales.")
        print("   FAILED: No se pudo conectar a AWS.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"   [ERROR] Error de permisos o configuración al conectar con Secrets Manager: {error_code}.")
        print("   FAILED: No se pudo validar el permiso de lectura en Secrets Manager.")
    except Exception as e:
        print(f"   [ERROR] Ocurrió un error inesperado: {e}")
        print("   FAILED: No se pudo validar el permiso de lectura en Secrets Manager.")


if __name__ == "__main__":
    print("="*60)
    print("Iniciando Verificación de Conectividad y Permisos AWS")
    print("="*60)
    
    check_s3_bucket_status()
    check_secrets_manager_access()
    
    print("\n" + "="*60)
    print("Verificación completada.")
    print("="*60)
    print("\nEste reporte puede ser usado como evidencia técnica de conectividad.")
