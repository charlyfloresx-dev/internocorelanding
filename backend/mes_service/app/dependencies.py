from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db

# Aquí se añadirán dependencias de Auth (get_current_user, etc)
# por ahora solo DB
