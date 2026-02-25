# backend/auth_service/app/models/__init__.py

# 1. Importar la Base declarativa primero.
from .base import Base

# 2. Importar modelos en orden de dependencia para el registro
from .user import User
from .role import Role
from .permission import Permission
from .role_permission import RolePermission
from .user_company_role import UserCompanyRole
from .company_stub import Company

# 4. Exponer todos los modelos para que puedan ser importados desde app.models
__all__ = ["Base", "Company", "Permission", "Role", "User", "RolePermission", "UserCompanyRole"]