import os
import sys
from pathlib import Path

# Add the necessary paths for imports to work inside the container
sys.path.append("/app")
sys.path.append("/app/auth_service")

try:
    from auth_app.core.config import settings
    
    print("\n" + "="*50)
    print("INTERNOCORE IP VALIDATION TOOL")
    print("="*50)
    
    env_ip = os.environ.get("INT_API_EXTERNAL_URL")
    setting_ip = settings.INT_API_EXTERNAL_URL
    
    print(f"1. Variable de Entorno (OS): {env_ip if env_ip else '❌ NO DETECTADA'}")
    print(f"2. Variable en Settings (Pydantic): {setting_ip if setting_ip else '❌ NO CARGADA'}")
    
    if setting_ip:
        print("\n✅ RESULTADO: El Monolito está configurado correctamente.")
        print(f"   IP Destino: {setting_ip}")
    else:
        print("\n❌ RESULTADO: El Monolito sigue sin detectar la IP manual.")
        print("   Acción sugerida: Reiniciar contenedor con 'docker compose restart'.")
    
    print("="*50 + "\n")

except Exception as e:
    print(f"\n❌ ERROR CRÍTICO AL VALIDAR: {e}")
    sys.exit(1)
