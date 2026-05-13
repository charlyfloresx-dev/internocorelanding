from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from master_app.dependencies import get_db, get_current_user
from common.domain.entities.user_context import UserContext
from common.responses import ApiResponse
from sqlalchemy import Table, MetaData

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[dict]])
async def get_enumerations(
    type: Optional[str] = Query(None, description="Filtrar por tipo de enumeración"),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Security(require_scope, scopes=["master_data:read"])
):
    metadata = MetaData()
    enumerations_table = Table("enumerations", metadata, autoload_with=None) # We'll use text or defined model if possible
    
    # Better use the model if it exists
    from sqlalchemy import text
    
    query = "SELECT * FROM enumerations WHERE (company_id = :co_id OR company_id IS NULL) AND is_active = TRUE AND deleted_at IS NULL"
    params = {"co_id": current_user.company_id}
    
    if type:
        query += " AND type = :type"
        params["type"] = type
        
    query += " ORDER BY sort_order ASC"
    
    result = await db.execute(text(query), params)
    enums = [dict(row._mapping) for row in result]
    
    return ApiResponse(status="success", data=enums, message="Enumerations retrieved successfully")
