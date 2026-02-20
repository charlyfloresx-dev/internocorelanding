# -*- coding: utf-8 -*-
"""
Script para Cargar Datos Iniciales (Seed Data) en la Base de Datos.

Uso:
  - Asegúrate de que el entorno virtual esté activado y las dependencias instaladas.
  - Asegúrate de que el archivo .env está presente en la raíz del proyecto.
  - Ejecuta desde la raíz del proyecto (desde la carpeta `interno`):
    python scripts/seed_data.py

Este script se conecta a la base de datos configurada en el .env y carga
datos esenciales para el funcionamiento inicial del sistema, como la primera
compañía, el usuario administrador y los roles básicos.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Cargar variables de entorno y ajustar sys.path ---
# Añadir el directorio del servicio de autenticación al path para poder importar sus módulos
# asumiendo que el script se ejecuta desde la raíz del proyecto.
# IMPORTANT: Adjust sys.path for the new location of the script
# The script is now at backend/auth_service/scripts/seed_data.py inside the container.
# Its imports (like 'app.core.database') assume 'app' is directly on the Python path.
# So, we need to add the directory containing 'app' (which is 'backend/auth_service/') to sys.path.
# os.path.dirname(__file__) will be /app/scripts/
# os.path.join(os.path.dirname(__file__), '..') will be /app
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')) # /app/
load_dotenv()


# --- Importar componentes de la aplicación ---
# Ahora estas importaciones deberían funcionar correctamente
from app.core.database import AsyncSessionLocal
from app.models import Company, User, UserCompanyRole, Role, Permission, RolePermission
from app.core.security import hash_password # Para hashear la contraseña del admin
from app.core.config import settings # Not used directly in seed logic, but good practice to keep.

# --- Lógica de Seeding ---
async def seed_data():
    """
    Función principal que orquesta el seeding de datos para Users, Companies, Roles y sus relaciones.
    """
    logger.info("🌱 Iniciando el proceso de seeding de datos...")

    async with AsyncSessionLocal() as db_session:
        try:
            # 1. Seed Roles (from User, Company, Role requirement)
            # Ensure basic roles exist
            default_roles = ["admin", "owner", "supervisor", "member"]
            seeded_roles = {}
            for role_name in default_roles:
                result = await db_session.execute(select(Role).filter_by(name=role_name))
                role = result.scalar_one_or_none()
                if not role:
                    logger.info(f"Creando rol: {role_name}...")
                    role = Role(name=role_name)
                    db_session.add(role)
                    await db_session.commit()
                    await db_session.refresh(role)
                    logger.info(f"Rol '{role_name}' creado con ID: {role.id}")
                else:
                    logger.info(f"Rol '{role_name}' ya existe con ID: {role.id}")
                seeded_roles[role_name] = role

            # 2. Seed Companies
            # InternoCore Systems (from previous seed_data.py) - Only with name
            result = await db_session.execute(
                select(Company).filter(Company.name == "InternoCore Systems")
            )
            internocore_company = result.scalar_one_or_none()

            if not internocore_company:
                logger.info("Creando compañía por defecto 'InternoCore Systems'...")
                internocore_company = Company(name="InternoCore Systems") # Only name
                db_session.add(internocore_company)
                await db_session.commit()
                await db_session.refresh(internocore_company)
                logger.info(f"Compañía 'InternoCore Systems' creada con ID: {internocore_company.id}.")
            else:
                logger.info(f"La compañía 'InternoCore Systems' ya existe con ID: {internocore_company.id}.")

            # Aperture Science (from previous seed_tenant.py and new requirement) - Only with name and logo
            result = await db_session.execute(select(Company).filter_by(name="Aperture Science"))
            aperture_company = result.scalars().first()

            if not aperture_company:
                logger.info("Creando compañía: Aperture Science...")
                aperture_company = Company(name="Aperture Science", logo="https://example.com/aperture_logo.png") # Only name and logo
                db_session.add(aperture_company)
                await db_session.commit()
                await db_session.refresh(aperture_company)
                logger.info(f"Compañía 'Aperture Science' creada con ID: {aperture_company.id}")
            else:
                logger.info(f"Compañía 'Aperture Science' ya existe con ID: {aperture_company.id}")

            # Black Mesa (New requirement) - Only with name and logo
            result = await db_session.execute(select(Company).filter_by(name="Black Mesa"))
            black_mesa_company = result.scalars().first()

            if not black_mesa_company:
                logger.info("Creando compañía: Black Mesa...")
                black_mesa_company = Company(name="Black Mesa", logo="https://example.com/blackmesa_logo.png") # Only name and logo
                db_session.add(black_mesa_company)
                await db_session.commit()
                await db_session.refresh(black_mesa_company)
                logger.info(f"Compañía 'Black Mesa' creada con ID: {black_mesa_company.id}")
            else:
                logger.info(f"Compañía 'Black Mesa' ya existe con ID: {black_mesa_company.id}.")


            # 3. Seed Users
            # Admin user
            result = await db_session.execute(
                select(User).filter(User.email == "admin@interno.core")
            )
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                logger.info("Creando usuario administrador 'admin@interno.core'...")
                admin_user = User(
                    email="admin@interno.core",
                    full_name="Admin User",
                    hashed_password=hash_password("admin"),
                    status="active"
                )
                db_session.add(admin_user)
                await db_session.commit()
                await db_session.refresh(admin_user)
                logger.info(f"Usuario administrador creado con ID: {admin_user.id}.")
            else:
                logger.info(f"El usuario administrador ya existe con ID: {admin_user.id}.")
            
            # Charly user
            result = await db_session.execute(
                select(User).filter(User.email == "charly@internocore.app")
            )
            charly_user = result.scalar_one_or_none()

            if not charly_user:
                logger.info("Creando usuario 'charly@internocore.app'...")
                charly_user = User(
                    email="charly@internocore.app",
                    full_name="Charly Admin",
                    hashed_password=hash_password("Dell2024"),
                    status="active"
                )
                db_session.add(charly_user)
                await db_session.commit()
                await db_session.refresh(charly_user)
                logger.info(f"Usuario 'charly@internocore.app' creado con ID: {charly_user.id}.")
            else:
                logger.info(f"El usuario 'charly@internocore.app' ya existe con ID: {charly_user.id}.")


            # 4. Link Users with Companies (UserCompanyRole)
            # Link admin_user with InternoCore Systems as admin
            result = await db_session.execute(
                select(UserCompanyRole)
                .filter_by(user_id=admin_user.id, company_id=internocore_company.id)
            )
            admin_ic_link = result.scalars().first()
            if not admin_ic_link:
                logger.info(f"Vinculando admin_user ({admin_user.id}) con InternoCore Systems ({internocore_company.id}) como admin.")
                admin_ic_link = UserCompanyRole(
                    user_id=admin_user.id,
                    company_id=internocore_company.id,
                    role_id=seeded_roles["admin"].id,
                    is_new=False
                )
                db_session.add(admin_ic_link)
                await db_session.commit()
                await db_session.refresh(admin_ic_link)
            else:
                logger.info(f"Vinculación admin_user con InternoCore Systems ya existe.")

            # Link charly_user with Aperture Science as admin (is_new=False)
            result = await db_session.execute(
                select(UserCompanyRole)
                .filter_by(user_id=charly_user.id, company_id=aperture_company.id)
            )
            charly_aperture_link = result.scalars().first()

            if not charly_aperture_link:
                logger.info(f"Vinculando charly_user ({charly_user.id}) con Aperture Science ({aperture_company.id}) como admin (is_new=False)...")
                charly_aperture_link = UserCompanyRole(
                    user_id=charly_user.id,
                    company_id=aperture_company.id,
                    role_id=seeded_roles["admin"].id,
                    is_new=False # Set to False as per new requirement
                )
                db_session.add(charly_aperture_link)
                await db_session.commit()
                await db_session.refresh(charly_aperture_link)
                logger.info("✅ Vinculación creada con éxito.")
            else:
                logger.info(f"Vinculación charly_user con Aperture Science ya existe. Asegurando is_new=False...")
                charly_aperture_link.is_new = False # Ensure is_new is False
                await db_session.commit()
                await db_session.refresh(charly_aperture_link)
                logger.info("✅ Vinculación actualizada con éxito.")

            # Link charly_user with Black Mesa as admin (is_new=True)
            result = await db_session.execute(
                select(UserCompanyRole)
                .filter_by(user_id=charly_user.id, company_id=black_mesa_company.id)
            )
            charly_black_mesa_link = result.scalars().first()

            if not charly_black_mesa_link:
                logger.info(f"Vinculando charly_user ({charly_user.id}) con Black Mesa ({black_mesa_company.id}) como admin (is_new=True)...")
                charly_black_mesa_link = UserCompanyRole(
                    user_id=charly_user.id,
                    company_id=black_mesa_company.id,
                    role_id=seeded_roles["admin"].id,
                    is_new=True # Set to True as per new requirement
                )
                db_session.add(charly_black_mesa_link)
                await db_session.commit()
                await db_session.refresh(charly_black_mesa_link)
                logger.info("✅ Vinculación creada con éxito.")
            else:
                logger.info(f"Vinculación charly_user con Black Mesa ya existe. Asegurando is_new=True...")
                charly_black_mesa_link.is_new = True # Ensure is_new is True
                await db_session.commit()
                await db_session.refresh(charly_black_mesa_link)
                logger.info("✅ Vinculación actualizada con éxito.")

            logger.info("✅ Proceso de seeding de datos completado con éxito.")

        except Exception as e:
            logger.error(f"❌ Error durante el proceso de seeding: {e}")
            await db_session.rollback()
            raise # Re-raise the exception after rollback for proper error handling
        finally:
            await db_session.close() # Cierra la sesión
            logger.info("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    asyncio.run(seed_data())