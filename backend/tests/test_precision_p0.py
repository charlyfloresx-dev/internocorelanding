import unittest
from decimal import Decimal
from pydantic import BaseModel, Field

class TestFloatVsDecimal(unittest.TestCase):
    def test_precision_difference(self):
        # 1. El Pecado del Float
        float_result = 0.1 + 0.2
        self.assertNotEqual(float_result, 0.3)
        self.assertEqual(float_result, 0.30000000000000004) # Demostrando la inconsistencia

        # 2. La Verdad del Decimal
        decimal_result = Decimal("0.1") + Decimal("0.2")
        self.assertEqual(decimal_result, Decimal("0.3"))
        
        # 3. Validación de Pydantic Model
        class PriceSchema(BaseModel):
            unit_price: Decimal = Field(..., ge=Decimal("0.0"))
            
        # Pydantic parsea el string al Decimal correcto y exacto
        schema = PriceSchema(unit_price="100.50")
        self.assertEqual(schema.unit_price, Decimal("100.50"))
        self.assertIsInstance(schema.unit_price, Decimal)
        
        print("✅ [TEST PASSED] Decimal Precision verified over Float Inaccuracy.")

if __name__ == "__main__":
    unittest.main()
