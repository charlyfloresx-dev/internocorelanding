# backend/auth_service/app/models/__init__.py

# 1. Importar la Base declarativa compartida
from common.models import Base

# 2. Importar modelos en orden de dependencia para el registro
from common.models import Company, AuditLog, BusinessGroup, SecurityAuditLog
from .user import User
from .user_credential import UserCredential
from .role import Role
from .permission import Permission
from .role_permission import RolePermission
from .user_company_role import UserCompanyRole
from .invitation import Invitation
from .refresh_token import RefreshToken
from .refresh_token_family import RefreshTokenFamily, RefreshTokenRotationAudit

# 4. Exponer todos los modelos para que puedan ser importados desde app.models
__all__ = [
    "Base", "Company", "BusinessGroup", "Permission", "Role",
    "User", "UserCredential",
    "RolePermission", "UserCompanyRole", "Invitation", "RefreshToken",
    "RefreshTokenFamily", "RefreshTokenRotationAudit",
    "SecurityAuditLog"
]
