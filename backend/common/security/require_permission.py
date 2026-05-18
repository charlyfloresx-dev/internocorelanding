from fastapi import Request, HTTPException, status
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

# Maps slug prefix → module_code for auto-resolution
_SLUG_MODULE_MAP: dict[str, str] = {
    "inventory":   "INVENTORY_CORE",
    "pos":         "INVENTORY_CORE",
    "master_data": "MASTER_DATA_CORE",
    "hcm":         "HCM_CORE",
    "admin":       "AUTH_CORE",
}


def _resolve_module(slug: str) -> str:
    prefix = slug.split(".")[0]
    return _SLUG_MODULE_MAP.get(prefix, "AUTH_CORE")


class RequirePermission:
    """
    FastAPI callable dependency that enforces a specific Permission slug.

    Composes over SubscriptionGuard — validates JWT, module entitlement and
    readonly mode first, then checks the granular slug against token.scopes.

    Wildcard bypass: scopes=["*"] (admin/owner) skips the slug check.

    Usage:
        @router.post("/documents/approve")
        async def approve(token = Depends(RequirePermission("inventory.document.approve"))):
            ...
    """

    def __init__(self, slug: str, module_code: str = "auto"):
        self.slug = slug
        resolved = _resolve_module(slug) if module_code == "auto" else module_code
        # Guard instance is created once per RequirePermission instantiation,
        # not per request — safe because SubscriptionGuard is stateless.
        self._guard = SubscriptionGuard(module_code=resolved)

    async def __call__(self, request: Request) -> TokenPayload:
        # 1. JWT auth + module entitlement + readonly enforcement
        token: TokenPayload = await self._guard(request)

        # 2. Wildcard bypass — admin/owner get scopes=["*"]
        if token.scopes and "*" in token.scopes:
            return token

        # 3. Slug enforcement
        if not token.scopes or self.slug not in token.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR_PERMISSION_DENIED",
                    "message": f"Acceso denegado. Se requiere el permiso: {self.slug}",
                },
            )
        return token
