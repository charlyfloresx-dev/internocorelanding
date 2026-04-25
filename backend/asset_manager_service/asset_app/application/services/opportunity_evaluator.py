"""
Financial Engine — OpportunityEvaluator

Calcula el ROI proyectado y determina si un predio califica como
"Oportunidad de Inversión" basándose en la deuda, el valor de mercado
y el buffer de riesgo configurado.

Fórmula:
    Costo Total  = adeudo + gastos_legales + (VM * risk_buffer)
    ROI Bruto    = VM - (precio_adquisicion + Costo Total)
    is_opportunity = ROI > 0  AND  adeudo > umbral mínimo
"""
from decimal import Decimal
from typing import Optional
from common.logger import get_logger

logger = get_logger(__name__)

# Umbral: si el adeudo representa al menos este % del VM, es candidato a oportunidad
ADEUDO_THRESHOLD_PCT = Decimal("0.20")  # 20%

# Umbral de años de morosidad para activar flag de urgencia
YEARS_DELINQUENT_THRESHOLD = 5


class FinancialCalculation:
    """Resultado del cálculo financiero para un predio."""
    def __init__(
        self,
        estimated_market_value: Decimal,
        costo_total: Decimal,
        projected_roi: Decimal,
        is_investment_opportunity: bool,
        details: dict,
    ):
        self.estimated_market_value = estimated_market_value
        self.costo_total = costo_total
        self.projected_roi = projected_roi
        self.is_investment_opportunity = is_investment_opportunity
        self.details = details


class OpportunityEvaluator:
    """
    Motor Financiero del Asset Manager.

    No tiene estado propio — recibe parámetros y retorna métricas calculadas.
    Puede ser instanciado como singleton o creado por request.
    """

    def evaluate(
        self,
        superficie: Optional[Decimal],
        valor_m2_zona: Optional[Decimal],
        adeudo_total: Optional[Decimal],
        gastos_legales: Optional[Decimal] = Decimal("50000"),
        risk_buffer_percentage: Optional[Decimal] = Decimal("0.10"),
        precio_adquisicion: Optional[Decimal] = None,
    ) -> Optional[FinancialCalculation]:
        """
        Calcula las métricas de inversión para un predio.

        Returns:
            FinancialCalculation con todos los campos calculados,
            o None si no hay datos suficientes para el cálculo.
        """
        if not superficie or not valor_m2_zona:
            logger.warning("OpportunityEvaluator: Datos insuficientes (superficie o valor_m2). Retornando None.")
            return None

        # Defaults seguros
        adeudo = adeudo_total or Decimal("0")
        gastos = gastos_legales or Decimal("50000")
        buffer_pct = risk_buffer_percentage or Decimal("0.10")

        # ── Cálculos Core ──────────────────────────────────────────────────
        vm = Decimal(str(superficie)) * valor_m2_zona
        risk_buffer_amount = vm * buffer_pct
        costo_total = adeudo + gastos + risk_buffer_amount

        # PA = precio de adquisición (negociado). Si no se conoce aún, usamos el adeudo
        # como proxy conservador del costo de entrada más la deuda.
        pa = precio_adquisicion or Decimal("0")
        projected_roi = vm - (pa + costo_total)

        # ── Reglas de Oportunidad ──────────────────────────────────────────
        adeudo_pct_of_vm = (adeudo / vm) if vm > 0 else Decimal("0")
        is_opportunity = (
            projected_roi > 0
            and adeudo_pct_of_vm >= ADEUDO_THRESHOLD_PCT
        )

        details = {
            "vm": str(vm),
            "adeudo": str(adeudo),
            "gastos_legales": str(gastos),
            "risk_buffer_amount": str(risk_buffer_amount),
            "costo_total": str(costo_total),
            "pa": str(pa),
            "adeudo_pct_of_vm": f"{float(adeudo_pct_of_vm) * 100:.1f}%",
            "umbral_oportunidad": f"{float(ADEUDO_THRESHOLD_PCT) * 100:.0f}%",
        }

        logger.info(
            f"Evaluación financiera: VM={vm:,.0f} | ROI={projected_roi:,.0f} | "
            f"Adeudo%={adeudo_pct_of_vm * 100:.1f}% | Oportunidad={is_opportunity}"
        )

        return FinancialCalculation(
            estimated_market_value=vm,
            costo_total=costo_total,
            projected_roi=projected_roi,
            is_investment_opportunity=is_opportunity,
            details=details,
        )
