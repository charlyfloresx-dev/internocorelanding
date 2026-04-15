from fastapi import APIRouter, Depends
from typing import Any
from app.schemas.readiness import InventoryReadinessDto
from app.api.v1.handlers.readiness_handler import (
    GetCompanyInventoryReadinessHandler, 
    GetCompanyInventoryReadinessQuery
)
from app.dependencies.repositories import get_inventory_repository
from app.dependencies.clients import get_master_data_client
from common.context import request_context
from common.security.guards import requires_role

router = APIRouter()

@router.get("/readiness", response_model=InventoryReadinessDto)
@requires_role(["OWNER", "ADMIN", "TENANT_ADMIN"])
async def get_inventory_readiness(
    repo=Depends(get_inventory_repository),
    md_client=Depends(get_master_data_client)
) -> Any:
    """
    Check if the company is ready for inventory operations.
    Used during onboarding to guide the user.
    """
    try:
        context = request_context.get()
        query = GetCompanyInventoryReadinessQuery(
            company_id=context.company_id,
            user_id=context.user_id
        )
        handler = GetCompanyInventoryReadinessHandler(repo, md_client)
        return await handler.handle(query)
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Error in get_inventory_readiness: {str(e)}")
        logging.error(traceback.format_exc())
        # We don't raise here yet to see if we can return a partial success? 
        # Actually better to raise 500 but with clear log.
        raise
