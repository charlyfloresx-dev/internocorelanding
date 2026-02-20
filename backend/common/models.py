# Proxy para mantener compatibilidad mientras se migra a common.domain
from .domain.entities import Base, BaseDomainEntity, AuditBase, MultiTenantBase

# Alias para compatibilidad con nombres antiguos si es necesario
BaseEntity = BaseDomainEntity