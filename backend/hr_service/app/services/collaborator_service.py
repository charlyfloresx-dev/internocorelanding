import csv
import io
import uuid
import logging
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException, status

import re
from app.domain.entities.collaborator_entities import Collaborator
from app.domain.ports.collaborator_repository import ICollaboratorRepository
from app.core.security import hash_rfid, hash_pin

logger = logging.getLogger(__name__)

class CollaboratorService:
    def __init__(self, repo: ICollaboratorRepository):
        self.repo = repo

    async def _validate_format(self, internal_id: str, company_id: uuid.UUID):
        """Validates internal_id against company-specific Regex pattern."""
        config = await self.repo.get_tenant_config(company_id)
        if config and config.internal_id_pattern:
            if not re.match(config.internal_id_pattern, internal_id):
                error_msg = config.pattern_error_message or f"ID {internal_id} no cumple con el formato de la empresa."
                raise ValueError(error_msg)

    @staticmethod
    async def get_csv_template() -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["internal_id", "full_name", "rfid_tag", "pin_code", "home_warehouse_id", "is_supervisor"])
        return output.getvalue()

    async def bulk_upload(
        self, 
        file: UploadFile, 
        company_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Parses CSV and creates/updates collaborators via Repository Interface.
        Orchestator pattern for domain entities.
        """
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be CSV.")

        content = await file.read()
        try:
            decoded = content.decode('utf-8-sig')
            f = io.StringIO(decoded)
            reader = csv.DictReader(f)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Parsing error: {str(e)}")

        results = {"created": 0, "updates": 0, "errors": []}
        
        for i, row in enumerate(reader):
            try:
                internal_id = row.get("internal_id")
                if not internal_id:
                    results["errors"].append(f"Row {i+1}: Missing internal_id")
                    continue

                full_name = row.get("full_name", "Unknown")
                
                # Validar Patrón de Empresa (123456A, etc.)
                await self._validate_format(internal_id, company_id)

                rfid_raw = row.get("rfid_tag")
                pin_raw = row.get("pin_code")
                wid_raw = row.get("home_warehouse_id")
                is_sup = str(row.get("is_supervisor", "false")).lower() == "true"

                rfid_hash = hash_rfid(rfid_raw) if rfid_raw else None
                pin_hash = hash_pin(pin_raw) if pin_raw else None
                
                home_warehouse_id = None
                if wid_raw:
                    try:
                        home_warehouse_id = uuid.UUID(wid_raw)
                    except ValueError:
                        results["errors"].append(f"Row {i+1}: Invalid warehouse UUID")
                        continue

                # Clean Architecture: Use Repository Interface
                existing = await self.repo.get_by_internal_id(internal_id, company_id)
                
                if existing:
                    existing.full_name = full_name
                    if rfid_hash: existing.rfid_tag = rfid_hash
                    if pin_hash: existing.pin_code = pin_hash
                    existing.home_warehouse_id = home_warehouse_id
                    existing.is_supervisor = is_sup
                    await self.repo.update(existing)
                    results["updates"] += 1
                else:
                    new_colab = Collaborator(
                        id=uuid.uuid4(),
                        company_id=company_id,
                        tenant_id=company_id,
                        internal_id=internal_id,
                        full_name=full_name,
                        rfid_tag=rfid_hash,
                        pin_code=pin_hash,
                        home_warehouse_id=home_warehouse_id,
                        is_supervisor=is_sup
                    )
                    await self.repo.create(new_colab)
                    results["created"] += 1

            except Exception as e:
                results["errors"].append(f"Row {i+1}: {str(e)}")

        # Note: commit should happen at middleware/entry-point level
        return results

    async def create_collaborator(
        self, 
        data: Dict[str, Any], 
        company_id: uuid.UUID,
        photo: Optional[UploadFile] = None
    ) -> Collaborator:
        """Creates a single collaborator with pattern validation and optional photo upload."""
        internal_id = data.get("internal_id")
        if not internal_id:
            raise ValueError("internal_id is required")

        # Validar Patrón de Empresa
        await self._validate_format(internal_id, company_id)

        # Check existing
        existing = await self.repo.get_by_internal_id(internal_id, company_id)
        if existing:
            raise ValueError(f"Collaborator with ID {internal_id} already exists in this company.")

        photo_path = None
        colab_id = uuid.uuid4()

        if photo:
            try:
                from common import get_storage_provider
                storage = get_storage_provider()
                
                # Path: {company_id}/hr/collaborators/{uuid}.jpg
                extension = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
                object_key = f"{company_id}/hr/collaborators/{colab_id}.{extension}"
                
                # Upload
                photo_path = storage.upload_file(photo.file, object_key, content_type=photo.content_type)
                logger.info(f"Photo uploaded for collaborator {internal_id}: {photo_path}")
            except Exception as e:
                # No bloqueamos el flujo si falla el almacenamiento, pero logueamos el error
                logger.error(f"Error uploading photo for collaborator {internal_id}: {str(e)}")

        rfid_raw = data.get("rfid_tag")
        pin_raw = data.get("pin_code")
        
        new_colab = Collaborator(
            id=colab_id,
            company_id=company_id,
            tenant_id=company_id,
            internal_id=internal_id,
            full_name=data.get("full_name", "Unknown"),
            rfid_tag=hash_rfid(rfid_raw) if rfid_raw else None,
            pin_code=hash_pin(pin_raw) if pin_raw else None,
            home_warehouse_id=data.get("home_warehouse_id"),
            is_supervisor=data.get("is_supervisor", False),
            photo_path=photo_path
        )
        return await self.repo.create(new_colab)
