"""
Phase 50: Collaborator Schemas
Pydantic models for validation, creation, update, and API responses.

Regex patterns inherited from legacy .NET (Interno.Domain/InternoExtensions.cs):
  - RFC: Handles personas físicas (13 chars: 4 letters + 6 date + 3 homonimia)
  - CURP: Full 18-char string including gender and state code
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


from hcm_app.schemas.department import DepartmentRead


# ── Nested/Embedded Schemas ────────────────────────────────────────────────────

class EmergencyContact(BaseModel):
    """
    Standardized JSONB structure for emergency_contact field.
    Having a typed schema here prevents the Angular frontend from guessing the contract.
    """
    name: str = Field(..., description="Full name of the emergency contact.")
    relationship: str = Field(..., description="E.g., Cónyuge, Madre, Padre.")
    phone: str = Field(..., description="Primary phone number.")
    alternative_phone: Optional[str] = Field(None, description="Secondary/backup number.")


class EligibilityDetail(BaseModel):
    """Breakdown of a single failing document for the eligibility response."""
    document: str = Field(..., description="Name of the expired/expiring document.")
    expiry_date: Optional[date] = Field(None, description="Expiry date of the document.")
    days_remaining: Optional[int] = Field(None, description="Days until expiry. Negative means already expired.")


class EligibilityResponse(BaseModel):
    """
    Full eligibility response for the /eligibility and /validate-scan endpoints.
    Designed for the Shipping handheld to show the operator WHY a driver was rejected,
    not just that they were rejected.
    """
    eligible: bool
    reason: str = Field(..., description="Short reason code or human message.")
    collaborator_id: Optional[uuid.UUID] = None
    full_name: Optional[str] = None
    details: Optional[EligibilityDetail] = Field(
        None,
        description="Present only when eligible=False. Contains the first failing document details."
    )


# ── Core Read Schemas ──────────────────────────────────────────────────────────

class CollaboratorRead(BaseModel):
    """Public read schema. Sensitive fiscal fields (RFC, CURP, NSS) are excluded."""
    id: uuid.UUID
    internal_id: str
    first_name: str
    last_name_paternal: str
    last_name_maternal: Optional[str] = None
    full_name: str
    department_id: Optional[uuid.UUID] = None
    department: Optional[DepartmentRead] = None
    job_title: Optional[str] = None
    assigned_plant: Optional[str] = None
    shift: Optional[str] = None
    translation_key: Optional[str] = None
    is_active: bool = True
    is_direct: bool = True
    home_warehouse_id: Optional[uuid.UUID] = None
    m3_operator_id: Optional[str] = None
    hazardous_material_certified: bool = False
    blood_type: Optional[str] = None
    emergency_contact: Optional[EmergencyContact] = None
    photo_path: Optional[str] = None
    profile_url: Optional[str] = None # Virtual field for frontend
    company_id: uuid.UUID

    class Config:
        from_attributes = True


class CollaboratorSensitiveRead(CollaboratorRead):
    """Extended read schema for HR managers. Includes fiscal + credential data."""
    rfc: Optional[str] = None
    curp: Optional[str] = None
    nss: Optional[str] = None
    visa_number: Optional[str] = None
    visa_expiry: Optional[date] = None
    sentry_id: Optional[str] = None
    global_entry_id: Optional[str] = None
    driver_license_number: Optional[str] = None
    driver_license_expiry: Optional[date] = None
    medical_certificate_expiry: Optional[date] = None
    last_drug_test_date: Optional[date] = None


# ── Create Schema ──────────────────────────────────────────────────────────────

# RFC Persona Física: 4 letters + 6 date + 3 homonimia (total 13 chars)
# Derived from legacy .NET: Interno.Domain/InternoExtensions.cs
_RFC_PATTERN = r"^([A-ZÑ&]{3,4})(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([A-Z\d]{3})$"

# CURP: 18 chars including gender code (H/M) and state code
_CURP_PATTERN = (
    r"^[A-Z]{1}[AEIOU]{1}[A-Z]{2}"
    r"\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"
    r"[HM]{1}"
    r"(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)"
    r"[B-DF-HJ-NP-TV-Z]{3}[0-9A-Z]{1}\d{1}$"
)


class CollaboratorCreate(BaseModel):
    # Required core fields
    internal_id: str = Field(..., max_length=50, description="Alphanumeric badge/employee number.")
    first_name: str = Field(..., max_length=100)
    last_name_paternal: str = Field(..., max_length=50)
    last_name_maternal: Optional[str] = Field(None, max_length=50)

    # Classification
    department_id: Optional[uuid.UUID] = None
    job_title: Optional[str] = Field(None, max_length=100)
    assigned_plant: Optional[str] = Field(None, max_length=100)
    shift: Optional[str] = Field(None, max_length=50)
    is_direct: bool = True
    home_warehouse_id: Optional[uuid.UUID] = None
    supervisor_id: Optional[uuid.UUID] = None

    # ERP
    m3_operator_id: Optional[str] = Field(None, max_length=30)

    # Fiscal Identity — validated with legacy .NET regex
    rfc: Optional[str] = Field(
        None, pattern=_RFC_PATTERN,
        description="RFC Persona Física (13 chars). Pattern from legacy .NET."
    )
    curp: Optional[str] = Field(
        None, pattern=_CURP_PATTERN,
        description="CURP (18 chars). Pattern from legacy .NET."
    )
    nss: Optional[str] = Field(None, max_length=11, pattern=r"^\d{11}$")

    # Cross-border credentials
    visa_number: Optional[str] = Field(None, max_length=20)
    visa_expiry: Optional[date] = None
    sentry_id: Optional[str] = Field(None, max_length=30)
    global_entry_id: Optional[str] = Field(None, max_length=30)
    driver_license_number: Optional[str] = Field(None, max_length=30)
    driver_license_expiry: Optional[date] = None

    # Compliance
    hazardous_material_certified: bool = False
    medical_certificate_expiry: Optional[date] = None
    last_drug_test_date: Optional[date] = None

    # Industrial Safety
    blood_type: Optional[str] = Field(None, max_length=5)
    emergency_contact: Optional[EmergencyContact] = None

    # Hardware
    rfid_tag: Optional[str] = Field(None, max_length=64, description="Plain RFID string; will be hashed before storage.")
    pin_code: Optional[str] = Field(None, min_length=4, max_length=20, description="Plain PIN; will be bcrypt-hashed.")


# ── Update Schema ──────────────────────────────────────────────────────────────

class CollaboratorUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name_paternal: Optional[str] = Field(None, max_length=50)
    last_name_maternal: Optional[str] = Field(None, max_length=50)
    department_id: Optional[uuid.UUID] = None
    job_title: Optional[str] = None
    assigned_plant: Optional[str] = None
    shift: Optional[str] = None
    translation_key: Optional[str] = None
    is_direct: Optional[bool] = None
    is_active: Optional[bool] = None
    supervisor_id: Optional[uuid.UUID] = None
    home_warehouse_id: Optional[uuid.UUID] = None
    m3_operator_id: Optional[str] = None

    # Fiscal
    rfc: Optional[str] = Field(None, pattern=_RFC_PATTERN)
    curp: Optional[str] = Field(None, pattern=_CURP_PATTERN)
    nss: Optional[str] = Field(None, pattern=r"^\d{11}$")

    # Cross-border
    visa_number: Optional[str] = None
    visa_expiry: Optional[date] = None
    sentry_id: Optional[str] = None
    global_entry_id: Optional[str] = None
    driver_license_number: Optional[str] = None
    driver_license_expiry: Optional[date] = None

    # Compliance
    hazardous_material_certified: Optional[bool] = None
    medical_certificate_expiry: Optional[date] = None
    last_drug_test_date: Optional[date] = None

    # Industrial safety
    blood_type: Optional[str] = None
    emergency_contact: Optional[EmergencyContact] = None

    # Hardware
    rfid_tag: Optional[str] = None
    pin_code: Optional[str] = None


# ── Verification Schemas (for auth_service internal calls) ────────────────────

class CollaboratorVerifyRequest(BaseModel):
    """Request body for the internal verification endpoint (from auth_service)."""
    rfid_tag: Optional[str] = Field(None, description="Raw RFID string from scanner hardware.")
    internal_id: Optional[str] = Field(None, description="Alphanumeric employee number.")
    pin_code: Optional[str] = Field(None, description="Plain PIN entered by the operator.")
    company_id: Optional[uuid.UUID] = Field(None, description="Company scope for multi-tenant isolation.")
    collaborator_id: Optional[uuid.UUID] = Field(None, description="Direct GUID lookup.")


class CollaboratorVerifyResponse(BaseModel):
    """Response returned to auth_service after successful verification."""
    collaborator_id: uuid.UUID
    internal_id: str
    full_name: str
    home_warehouse_id: Optional[uuid.UUID]
    is_supervisor: bool = False
    company_id: uuid.UUID
    tenant_id: uuid.UUID
    department: Optional[str] = None


class CollaboratorMultiVerifyResponse(BaseModel):
    """Container for multiple collaborator identities discovered for a single RFID."""
    matches: list[CollaboratorVerifyResponse]
    count: int
