from typing import List, Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import inspect
from enum import Enum

import common.enums as system_enums
from common.responses import ApiResponse

router = APIRouter()

class EnumItem(BaseModel):
    id: Any
    name: str

def get_all_enums() -> Dict[str, List[Dict[str, Any]]]:
    enum_dict = {}
    for name, obj in inspect.getmembers(system_enums):
        if inspect.isclass(obj) and issubclass(obj, Enum) and obj is not Enum:
            enum_dict[name] = [{"id": item.value, "name": item.name} for item in obj]
    return enum_dict

@router.get("/all", response_model=ApiResponse[Dict[str, List[EnumItem]]], summary="Listar todos los enumeradores del sistema")
async def get_all_system_enums():
    """Devuelve un diccionario con todos los catálogos enumerados del ecosistema interno."""
    data = get_all_enums()
    return ApiResponse(status="success", data=data, message="Enumeradores recuperados exitosamente")

@router.get("/{enum_name}", response_model=ApiResponse[List[EnumItem]], summary="Obtener valores de un enumerador específico")
async def get_specific_enum(enum_name: str):
    """Devuelve los valores posibles para un enumerador por su nombre exacto de clase (ej. 'MovementType', 'WarehouseType')."""
    enums = get_all_enums()
    if enum_name not in enums:
        raise HTTPException(status_code=404, detail=f"Enum '{enum_name}' no encontrado en el ecosistema.")
    return ApiResponse(status="success", data=enums[enum_name], message=f"Valores para {enum_name} recuperados")
