import asyncio
import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app import models
from app.core.security import pwd_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_seed():
    async with AsyncSessionLocal() as db:
        try:
            # 1. Buscar o Crear Usuario (Evita error si ya existe)
            email = "charly@internocore.app"
            stmt = select(models.User).where(models.User.email == email)
            result = await db.execute(stmt)
            user_charly = result.scalar_one_or_none()

            if not user_charly:
                user_charly = models.User(
                    email=email,
                    hashed_password=pwd_context.hash("Dell2024"),
                    is_active=True
                )
                db.add(user_charly)
                await db.flush() # Para obtener el ID sin hacer commit aún
                logger.info(f"Usuario {email} creado.")
            else:
                logger.info(f"Usuario {email} ya existe.")

            # 2. Crear Empresas (Ajustado a campos reales: name, logo)
            # No enviamos company_code ni status porque no existen en el modelo
            emp_a_name = "Interno Planta Norte"
            emp_b_name = "Interno Planta Sur"
            
            for name in [emp_a_name, emp_b_name]:
                stmt = select(models.Company).where(models.Company.name == name)
                res = await db.execute(stmt)
                if not res.scalar_one_or_none():
                    company = models.Company(name=name, logo=None)
                    db.add(company)
                    logger.info(f"Empresa {name} creada.")

            await db.commit()
            logger.info("Seed completado exitosamente.")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error en seed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(run_seed())