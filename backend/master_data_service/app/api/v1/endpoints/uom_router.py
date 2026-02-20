import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.schemas.uom import UOMRead, UOMCreate, UOMUpdate
from app.services.uom_service import UOMService
from common.responses import ApiResponse
from app.dependencies import get_current_user_payload
from app.db.session import get_db

router = APIRouter()


@router.get("/", response_model=ApiResponse[List[UOMRead]], summary="Listar Unidades de Medida")
async def list_uoms(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    """
    Devuelve una lista de todas las Unidades de Medida (UM) para la compañía actual.
    """
    company_id = uuid.UUID(payload.get("company_id"))
    uoms = await UOMService.get_uoms_by_company(db, company_id=company_id)
    return ApiResponse(
        status="success",
        data=uoms,
        message="Unidades de Medida recuperadas exitosamente."
    )

@router.post("/", response_model=ApiResponse[UOMRead], summary="Crear Unidad de Medida")
async def create_uom(
    uom_in: UOMCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    company_id = uuid.UUID(payload.get("company_id"))
    try:
        uom = await UOMService.create_uom(db, uom_in=uom_in, company_id=company_id)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una unidad de medida con este código en la compañía."
        )
    
    return ApiResponse(
        status="success",
        data=uom,
        message="Unidad de Medida creada exitosamente."
    )

@router.get("/{uom_id}", response_model=ApiResponse[UOMRead], summary="Obtener Unidad de Medida")
async def get_uom(
    uom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    company_id = uuid.UUID(payload.get("company_id"))
    uom = await UOMService.get_uom_by_id(db, uom_id=uom_id, company_id=company_id)
    if not uom:
        raise HTTPException(status_code=404, detail="Unidad de Medida no encontrada")
    
    return ApiResponse(
        status="success",
        data=uom,
        message="Unidad de Medida recuperada."
    )

@router.patch("/{uom_id}", response_model=ApiResponse[UOMRead], summary="Actualizar Unidad de Medida")
async def update_uom(
    uom_id: uuid.UUID,
    uom_in: UOMUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    company_id = uuid.UUID(payload.get("company_id"))
    uom = await UOMService.get_uom_by_id(db, uom_id=uom_id, company_id=company_id)
    if not uom:
        raise HTTPException(status_code=404, detail="Unidad de Medida no encontrada")
    
    try:
        uom = await UOMService.update_uom(db, db_obj=uom, uom_in=uom_in)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una unidad de medida con este código en la compañía."
        )

    return ApiResponse(
        status="success",
        data=uom,
        message="Unidad de Medida actualizada."
    )

@router.delete("/{uom_id}", response_model=ApiResponse[None], summary="Eliminar Unidad de Medida")
async def delete_uom(
    uom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    company_id = uuid.UUID(payload.get("company_id"))
    uom = await UOMService.get_uom_by_id(db, uom_id=uom_id, company_id=company_id)
    if not uom:
        raise HTTPException(status_code=404, detail="Unidad de Medida no encontrada")
    
    await UOMService.delete_uom(db, db_obj=uom)
    
    return ApiResponse(
        status="success",
        data=None,
        message="Unidad de Medida eliminada."
    )