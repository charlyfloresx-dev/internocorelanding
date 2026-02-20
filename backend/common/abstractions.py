from abc import ABC, abstractmethod
from typing import Any, List, Optional, TypeVar, Generic
from datetime import datetime
import uuid

class IDomainEvent(ABC):
    """
    Mirror of Interno.Domain.Events.IDomainEvent.
    Marker for Domain Events (MediatR style notification).
    """
    occurred_on: datetime

    def __init__(self):
        self.occurred_on = datetime.utcnow()

class Entity(ABC):
    """
    Mirror of Interno.Domain.Common.Entity.
    Base class for DDD Entities.
    Identity is based on ID, not memory reference.
    """
    def __init__(self):
        self._id: Any = None
        self._domain_events: List[IDomainEvent] = []

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def domain_events(self) -> List[IDomainEvent]:
        return self._domain_events

    def add_domain_event(self, event: IDomainEvent):
        self._domain_events.append(event)

    def clear_domain_events(self):
        self._domain_events.clear()

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        if self is other:
            return True
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self):
        if self.id is None:
            return hash(id(self))
        return hash(self.id)

class IAggregateRoot(ABC):
    """
    Mirror of Interno.Domain.Common.IAggregateRoot.
    Marker interface for Aggregate Roots (Consistency Boundary).
    """
    pass

class AuditableEntity(Entity):
    """
    Mirror of Interno.Domain.Common.AuditableEntity.
    Extension for entities that require auditing.
    """
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime]
    updated_by: Optional[str]