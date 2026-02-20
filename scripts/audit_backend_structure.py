import os
import sys
from pathlib import Path

def audit_backend():
    print("🔍 INICIANDO AUDITORÍA DE ESTRUCTURA BACKEND (FASE 4)...")
    
    base_dir = Path(__file__).resolve().parent.parent
    backend_dir = base_dir / "backend"
    common_dir = backend_dir / "common"
    auth_service_dir = backend_dir / "auth_service"
    
    errors = []
    warnings = []

    # 1. Validación de Single Source of Truth (SSOT) para Common
    if not common_dir.exists():
        errors.append("❌ CRÍTICO: No se encuentra 'backend/common'.")
    else:
        print("✅ 'backend/common' existe.")
        # Verificar modelos base
        models_file = common_dir / "models.py"
        if not models_file.exists():
             errors.append("❌ CRÍTICO: 'backend/common/models.py' no encontrado.")
        
    # 2. Detección de Duplicados (Common dentro de microservicios)
    dup_common = auth_service_dir / "app" / "common"
    if dup_common.exists():
        warnings.append(f"⚠️ DUPLICADO DETECTADO: Se encontró '{dup_common}'. Marcado para eliminación.")
    else:
        print("✅ No se detectaron carpetas 'common' duplicadas en auth_service.")

    # 3. Auditoría de Modelos en Auth Service
    models_dir = auth_service_dir / "app" / "models"
    if models_dir.exists():
        for model_file in models_dir.glob("*.py"):
            if model_file.name == "__init__.py": continue
            
            try:
                content = model_file.read_text(encoding="utf-8")
                if "class " in content and "BaseEntity" in content:
                    if "MultiTenantBase" not in content and "UserCompanyRole" not in content:
                        # UserCompanyRole es especial, pero otros deberían tenerlo
                        warnings.append(f"⚠️ MODELO SIN MULTITENANCY: '{model_file.name}' parece no heredar de MultiTenantBase.")
                    elif "MultiTenantBase" in content:
                        print(f"✅ Modelo '{model_file.name}' cumple con MultiTenantBase.")
            except Exception as e:
                errors.append(f"❌ Error leyendo {model_file.name}: {str(e)}")

    # 4. Reporte Final
    print("\n--- REPORTE DE AUDITORÍA ---")
    if not errors and not warnings:
        print("✅ ESTRUCTURA LIMPIA Y SINCRONIZADA.")
    else:
        for w in warnings:
            print(w)
        for e in errors:
            print(e)
        
        if errors:
            sys.exit(1)

if __name__ == "__main__":
    audit_backend()