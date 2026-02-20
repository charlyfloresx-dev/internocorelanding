# backend/auth_service/app/models/__init__.py

# 1. IMPORTANTE: Importar Company desde common
from common.models.company import Company
from common.models.base_models import Base

# 2. Importar el resto de modelos locales
from .user import User
from .role import Role
from .permission import Permission
from .role_permission import RolePermission
from .user_company_role import UserCompanyRole

# 3. Asegurar que Company esté en __all__
__all__ = ["Base", "User", "Company", "Role", "Permission", "RolePermission", "UserCompanyRole"]