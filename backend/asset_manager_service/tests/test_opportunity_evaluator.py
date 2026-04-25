"""
Test — Financial Engine (OpportunityEvaluator)

Valida la precisión matemática del cálculo de ROI bajo distintos
escenarios de inversión: adeudo alto, adeudo bajo, buffer de riesgo, datos faltantes.
"""
import pytest
from decimal import Decimal
from asset_app.application.services.opportunity_evaluator import OpportunityEvaluator, ADEUDO_THRESHOLD_PCT


@pytest.fixture
def evaluator() -> OpportunityEvaluator:
    return OpportunityEvaluator()


class TestOpportunityEvaluator:

    def test_gold_opportunity(self, evaluator):
        """Escenario Oro: adeudo > 30% del VM → should be an opportunity."""
        calc = evaluator.evaluate(
            superficie=Decimal("200"),       # 200 m²
            valor_m2_zona=Decimal("4500"),   # $4,500/m² → VM = $900,000
            adeudo_total=Decimal("280000"),  # 31% del VM
            gastos_legales=Decimal("50000"),
            risk_buffer_percentage=Decimal("0.10"),
            precio_adquisicion=Decimal("0"),
        )
        assert calc is not None
        assert calc.estimated_market_value == Decimal("900000")
        # VM - (PA + adeudo + gastos + buffer)
        # buffer = 900000 * 0.10 = 90000
        # costo_total = 280000 + 50000 + 90000 = 420000
        # ROI = 900000 - (0 + 420000) = 480000
        assert calc.projected_roi == Decimal("480000")
        assert calc.is_investment_opportunity is True

    def test_below_threshold_not_opportunity(self, evaluator):
        """Si el adeudo es < 20% del VM, no debe marcarse como oportunidad."""
        calc = evaluator.evaluate(
            superficie=Decimal("200"),
            valor_m2_zona=Decimal("4500"),   # VM = 900,000
            adeudo_total=Decimal("50000"),   # ~5.5% del VM
            gastos_legales=Decimal("50000"),
            risk_buffer_percentage=Decimal("0.10"),
        )
        assert calc is not None
        assert calc.is_investment_opportunity is False

    def test_negative_roi_not_opportunity(self, evaluator):
        """Adeudo mayor al VM → ROI negativo → no es oportunidad."""
        calc = evaluator.evaluate(
            superficie=Decimal("50"),
            valor_m2_zona=Decimal("1000"),   # VM = 50,000
            adeudo_total=Decimal("200000"),  # 4x el VM
            gastos_legales=Decimal("50000"),
            risk_buffer_percentage=Decimal("0.10"),
        )
        assert calc is not None
        assert calc.projected_roi < 0
        assert calc.is_investment_opportunity is False

    def test_risk_buffer_is_percentage_of_vm(self, evaluator):
        """Verifica que el risk_buffer se calcule correctamente sobre el VM."""
        calc = evaluator.evaluate(
            superficie=Decimal("100"),
            valor_m2_zona=Decimal("3000"),   # VM = 300,000
            adeudo_total=Decimal("90000"),   # 30% del VM
            gastos_legales=Decimal("0"),
            risk_buffer_percentage=Decimal("0.15"),  # 15%
        )
        assert calc is not None
        expected_buffer = Decimal("300000") * Decimal("0.15")  # = 45,000
        assert expected_buffer in calc.details.values() or str(expected_buffer) in calc.details.values()

    def test_missing_superficie_returns_none(self, evaluator):
        """Sin superficie, no se puede calcular → debe retornar None."""
        result = evaluator.evaluate(
            superficie=None,
            valor_m2_zona=Decimal("4500"),
            adeudo_total=Decimal("100000"),
        )
        assert result is None

    def test_missing_valor_m2_returns_none(self, evaluator):
        """Sin valor_m2, no hay VM → debe retornar None."""
        result = evaluator.evaluate(
            superficie=Decimal("200"),
            valor_m2_zona=None,
            adeudo_total=Decimal("100000"),
        )
        assert result is None

    def test_zero_adeudo_still_calculates(self, evaluator):
        """Un predio sin adeudo igual puede calcularse (oportunidad de compra directa)."""
        calc = evaluator.evaluate(
            superficie=Decimal("150"),
            valor_m2_zona=Decimal("5000"),   # VM = 750,000
            adeudo_total=Decimal("0"),
            gastos_legales=Decimal("30000"),
            risk_buffer_percentage=Decimal("0.10"),
        )
        assert calc is not None
        assert calc.estimated_market_value == Decimal("750000")
        # Oportunidad = False porque adeudo < 20% del VM (es 0%)
        assert calc.is_investment_opportunity is False

    def test_threshold_constant_is_20_percent(self):
        """Asegura que el umbral de oportunidad sea exactamente 20%."""
        assert ADEUDO_THRESHOLD_PCT == Decimal("0.20")
