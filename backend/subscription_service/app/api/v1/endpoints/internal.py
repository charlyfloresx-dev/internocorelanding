from app.services.queries import GetEntitlementsQuery

router = APIRouter()

@router.get("/entitlements/{company_id}")
async def get_company_entitlements(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    modules = await GetEntitlementsQuery.execute(db, company_id)
    return {
        "company_id": company_id,
        "modules": modules,
        "status": "ACTIVE" if modules else "INACTIVE"
    }
