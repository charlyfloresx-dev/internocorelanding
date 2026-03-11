import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, BigInteger, DateTime, UUID, func
from sqlalchemy.orm import Mapped, mapped_column
from ..infrastructure.models.base import MultiTenantBase

class FileMetadata(MultiTenantBase):
    """
    Tabla de metadatos de archivos del sistema.
    Registra cada objeto subido a S3/MinIO para auditor\u00eda y control de cuotas.
    """
    __tablename__ = "file_metadata"

    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    content_type: Mapped[Optional[str]] = mapped_column(String(100))
    original_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Traceability
    service_source: Mapped[Optional[str]] = mapped_column(String(50)) # e.g. 'WMS', 'TICKETS'
