import uuid
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
    from inventory_app.domain.entities.transfer_entities import InitiateTransferCommand

logger = logging.getLogger(__name__)

@dataclass
class AuditIssue:
    code: str
    msg: str
    severity: str  # "REJECT" | "WARNING" | "INFO"

@dataclass
class AuditResult:
    is_binational: bool
    applied_fx_rate: Optional[Decimal]
    suggested_customs_key: Optional[str]
    pending_financial_valuation: bool
    warnings: List[AuditIssue]
    rejections: List[AuditIssue]

    def is_rejected(self) -> bool:
        return len(self.rejections) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_binational": self.is_binational,
            "applied_fx_rate": str(self.applied_fx_rate) if self.applied_fx_rate else None,
            "suggested_customs_key": self.suggested_customs_key,
            "pending_financial_valuation": self.pending_financial_valuation,
            "warnings": [{"code": w.code, "msg": w.msg} for w in self.warnings],
            "rejections": [{"code": r.code, "msg": r.msg} for r in self.rejections]
        }

class TransferAuditService:
    """
    Domain Expert for Binational Compliance & Transfer Auditing.
    Decoupled from SQLAlchemy. Uses IInventoryRepository for queries.
    """

    def __init__(self, repo: "IInventoryRepository"):
        self.repo = repo

    async def execute_preflight_audit(
        self, 
        cmd: "InitiateTransferCommand",
        origin_wh_entity: Any,
        dest_wh_entity: Any
    ) -> AuditResult:
        """
        Analyzes the transfer command against compliance rules (Phase 40/41).
        """
        warnings: List[AuditIssue] = []
        rejections: List[AuditIssue] = []
        
        # 1. Country Detection (Normalization Engine)
        def _get_country(entity: Any) -> str:
            if not entity:
                return "MX" # Default to Local if warehouse is pending/virtual
            code = "MX"
            if hasattr(entity, "country_code"):
                code = getattr(entity, "country_code", "MX")
            elif isinstance(entity, dict):
                code = entity.get("country_code", "MX")
            return (code or "MX").upper().strip()

        origin_country = _get_country(origin_wh_entity)
        dest_country = _get_country(dest_wh_entity)
        
        is_binational = origin_country != dest_country
        
        logger.info(
            f"[AUDIT] Preflight Diagnosis: "
            f"Origin={origin_country} | Dest={dest_country} | "
            f"is_binational={is_binational} | currency={cmd.currency}"
        )
        
        # 2. FX Rate Logic (DOF Fallback)
        applied_fx = getattr(cmd, "exchange_rate_dof", None)
        if is_binational and not applied_fx:
            applied_fx = Decimal("20.00") # TODO: Integrated DOF API Fallback
            warnings.append(AuditIssue(
                code="FX_FALLBACK",
                msg="No exchange rate provided for binational transfer. Using default 20.00 MXN/USD.",
                severity="WARNING"
            ))

        # 3. Compliance Documentation (Anexo 24)
        suggested_key = None
        pending_fin = False
        
        if is_binational:
            suggested_key = "V1" if origin_country == "MX" else "A1"
            if not cmd.customs_pedimento:
                warnings.append(AuditIssue(
                    code="MISSING_PEDIMENTO",
                    msg=f"Binational transfer requires customs documentation. Suggested key: {suggested_key}",
                    severity="WARNING"
                ))

        # 4. Financial Audit (Phase 40: Admin Debt)
        explicit_price = getattr(cmd, "transfer_price", None)
        if not explicit_price or explicit_price <= 0:
            pending_fin = True
            warnings.append(AuditIssue(
                code="MISSING_PRICE",
                msg="No transfer price defined. Document marked as PENDING_FINANCIAL_VALUATION.",
                severity="WARNING"
            ))

        return AuditResult(
            is_binational=is_binational,
            applied_fx_rate=applied_fx,
            suggested_customs_key=suggested_key,
            pending_financial_valuation=pending_fin,
            warnings=warnings,
            rejections=rejections
        )

    @staticmethod
    def compute_usd_amount(amount_mxn: Decimal, currency: str, fx_rate: Decimal) -> Decimal:
        """Helper for cross-border valuation."""
        if currency.upper() == "USD":
            return amount_mxn
        if not fx_rate or fx_rate <= 0:
            return amount_mxn / Decimal("20.0")
        return (amount_mxn / fx_rate).quantize(Decimal("0.0001"))
