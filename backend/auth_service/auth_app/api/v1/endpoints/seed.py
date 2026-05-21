import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from auth_app.dependencies import get_db
from common.config import settings
import traceback

router = APIRouter()


async def verify_admin_master_key(x_admin_key: str = Header(..., alias="X-Admin-Master-Key")):
    if not settings or not settings.int_admin_master_key or x_admin_key != settings.int_admin_master_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso Denegado: Admin Master Key inválida o no configurada."
        )


@router.post("/run", dependencies=[Depends(verify_admin_master_key)])
async def seed_database(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    from scripts.seed import run_seed
    try:
        # Import the script dynamically just for execution
        import asyncio
        import os
        import sys
        
        # Ejecutamos asincrónicamente
        await run_seed()
        return {"status": "success", "message": "Seeding script execution triggered."}
    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}
