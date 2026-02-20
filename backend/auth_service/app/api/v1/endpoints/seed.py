import asyncio
import logging
import sys
import os

# Agregar el directorio padre al path para poder importar 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, Company, Role, Permission, RolePermission, UserCompanyRole
from app.core.security import hash_password

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed():
    logger.info("Iniciando seed de base de datos...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Crear Permiso 'all:manage'
            perm_name = "all:manage"
            result = await db.execute(select(Permission).where(Permission.name == perm_name))
            permission = result.scalar_one_or_none()
            
            if not permission:
                permission = Permission(
                    id="perm-all-manage-001", # ID manual tipo string
                    name=perm_name
                )
                db.add(permission)
                logger.info(f"Permiso creado: {perm_name}")
            else:
                logger.info(f"Permiso ya existe: {perm_name}")

            # 2. Crear Rol 'Admin'
            role_name = "Admin"
            result = await db.execute(select(Role).where(Role.name == role_name))
            role = result.scalar_one_or_none()
            
            if not role:
                role = Role(
                    id="role-admin-001", # ID manual tipo string
                    name=role_name
                )
                db.add(role)
                logger.info(f"Rol creado: {role_name}")
            else:
                logger.info(f"Rol ya existe: {role_name}")

            # 3. Vincular Rol y Permiso
            # Verificar si ya existe la relación
            result = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id
                )
            )
            role_perm = result.scalar_one_or_none()
            
            if not role_perm:
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id
                )
                db.add(role_perm)
                logger.info("Permiso 'all:manage' asignado a Rol 'Admin'")

            # 4. Crear Empresas Demo
            companies_data = [
                {
                    "id": "88888888-4444-4444-4444-121212121212",
                    "name": "Empresa Demo A",
                    "logo": "https://via.placeholder.com/150?text=DemoA"
                },
                {
                    "id": "99999999-5555-5555-5555-131313131313",
                    "name": "Empresa Demo B",
                    "logo": "https://via.placeholder.com/150?text=DemoB"
                }
            ]
            
            companies_objs = {}
            
            for c_data in companies_data:
                result = await db.execute(select(Company).where(Company.id == c_data["id"]))
                company = result.scalar_one_or_none()
                
                if not company:
                    company = Company(
                        id=c_data["id"],
                        name=c_data["name"],
                        logo=c_data["logo"]
                    )
                    db.add(company)
                    logger.info(f"Empresa creada: {c_data['name']}")
                else:
                    logger.info(f"Empresa ya existe: {c_data['name']}")
                companies_objs[c_data["name"]] = company

            # 5. Crear Usuario Admin
            email = "test@ejemplo.com"
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    id="user-test-001", # ID manual tipo string
                    email=email,
                    hashed_password=hash_password("admin123"),
                    is_active=True
                )
                db.add(user)
                logger.info(f"Usuario creado: {email}")
            else:
                logger.info(f"Usuario ya existe: {email}")

            # 6. Crear Relaciones UserCompanyRole
            # Empresa A (is_new=True)
            comp_a = companies_objs["Empresa Demo A"]
            result = await db.execute(
                select(UserCompanyRole).where(
                    UserCompanyRole.user_id == user.id,
                    UserCompanyRole.company_id == comp_a.id,
                    UserCompanyRole.role_id == role.id
                )
            )
            if not result.scalar_one_or_none():
                ucr_a = UserCompanyRole(
                    user_id=user.id,
                    company_id=comp_a.id,
                    role_id=role.id,
                    is_new=True # Flag para demo
                )
                db.add(ucr_a)
                logger.info(f"Usuario asignado a {comp_a.name} (is_new=True)")

            # Empresa B (is_new=False)
            comp_b = companies_objs["Empresa Demo B"]
            result = await db.execute(
                select(UserCompanyRole).where(
                    UserCompanyRole.user_id == user.id,
                    UserCompanyRole.company_id == comp_b.id,
                    UserCompanyRole.role_id == role.id
                )
            )
            if not result.scalar_one_or_none():
                ucr_b = UserCompanyRole(
                    user_id=user.id,
                    company_id=comp_b.id,
                    role_id=role.id,
                    is_new=False
                )
                db.add(ucr_b)
                logger.info(f"Usuario asignado a {comp_b.name} (is_new=False)")

            await db.commit()
            logger.info("Seed completado exitosamente.")
            
        except Exception as e:
            logger.error(f"Error durante el seed: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed())