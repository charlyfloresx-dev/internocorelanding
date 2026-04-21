import asyncio
import logging
import sys
import os

# Agregar el directorio padre al path para poder importar 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from auth_app.core.database import AsyncSessionLocal
from auth_app.models import User, Company, UserCompanyRole, Role

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_relations():
    logger.info("Iniciando reparación de relaciones User-Company...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Buscar Usuario
            email = "charly@internocore.app"
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"Usuario {email} no encontrado. Ejecuta seed.py primero.")
                return

            # 2. Buscar o Crear Rol Admin (Necesario para la relación)
            role_name = "Admin"
            result = await db.execute(select(Role).where(Role.name == role_name))
            role = result.scalar_one_or_none()
            
            if not role:
                logger.info(f"Rol {role_name} no encontrado. Creándolo...")
                role = Role(name=role_name)
                db.add(role)
                await db.flush() # Para obtener ID
                await db.refresh(role)

            # 3. Buscar Empresas y Vincular
            companies_to_fix = [
                {"name": "Interno Planta Norte", "is_new": True},
                {"name": "Interno Planta Sur", "is_new": False}
            ]

            for item in companies_to_fix:
                c_name = item["name"]
                should_be_new = item["is_new"]
                
                # Buscar empresa
                result = await db.execute(select(Company).where(Company.name == c_name))
                company = result.scalar_one_or_none()
                
                if not company:
                    logger.warning(f"Empresa {c_name} no encontrada.")
                    continue

                # Verificar si ya existe la relación
                result = await db.execute(select(UserCompanyRole).where(
                    UserCompanyRole.user_id == user.id,
                    UserCompanyRole.company_id == company.id,
                    UserCompanyRole.role_id == role.id
                ))
                ucr = result.scalar_one_or_none()

                if not ucr:
                    # Crear relación
                    ucr = UserCompanyRole(
                        user_id=user.id,
                        company_id=company.id,
                        role_id=role.id,
                        is_new=should_be_new
                    )
                    db.add(ucr)
                    logger.info(f"Vinculado: {user.email} -> {c_name} (is_new={should_be_new})")
                else:
                    # Actualizar is_new si es necesario
                    if ucr.is_new != should_be_new:
                        ucr.is_new = should_be_new
                        db.add(ucr)
                        logger.info(f"Actualizado: {c_name} is_new -> {should_be_new}")
                    else:
                        logger.info(f"Relación correcta ya existe: {c_name}")

            await db.commit()
            logger.info("Reparación completada exitosamente.")

        except Exception as e:
            logger.error(f"Error en fix_relations: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(fix_relations())
