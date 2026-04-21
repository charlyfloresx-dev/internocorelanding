from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from auth_app.dependencies import get_db
from common.models.company import Company
from auth_app.models.user import User

router = APIRouter()

@router.get("/demo")
async def get_demo_health(db: AsyncSession = Depends(get_db)):
    """
    Resumen del estado de los datos cargados en Modo Demo.
    """
    company_count = await db.execute(select(func.count(Company.id)))
    user_count = await db.execute(select(func.count(User.id)))
    
    return {
        "status": "active",
        "demo_mode": True,
        "summary": {
            "companies": company_count.scalar(),
            "users": user_count.scalar()
        }
    }
