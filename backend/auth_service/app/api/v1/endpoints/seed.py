import uuid
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
import traceback

router = APIRouter()

@router.post("/run")
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
