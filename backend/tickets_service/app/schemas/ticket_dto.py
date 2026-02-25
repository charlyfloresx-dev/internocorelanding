from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.core.constants import TicketStatus, TicketPriority, TicketType

class TicketBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=10)
    ticket_type: TicketType = TicketType.SUPPORT
    priority: TicketPriority = TicketPriority.MEDIUM

class TicketCreate(TicketBase):
    company_id: UUID

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to_id: Optional[UUID] = None

class TicketCommentBase(BaseModel):
    content: str

class TicketCommentCreate(TicketCommentBase):
    ticket_id: UUID
    company_id: UUID

class TicketCommentRead(TicketCommentBase):
    id: UUID
    author_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TicketHistoryRead(BaseModel):
    id: UUID
    change_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TicketRead(TicketBase):
    id: UUID
    reference_code: str
    status: TicketStatus
    assigned_to_id: Optional[UUID] = None
    company_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments: List[TicketCommentRead] = []
    
    class Config:
        from_attributes = True

class ApiResponse(BaseModel):
    status: str = "success"
    data: Optional[any] = None
    message: str = ""
    meta: dict = {}
