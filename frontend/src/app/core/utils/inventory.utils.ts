// temp_future/src/app/core/utils/inventory.utils.ts

/**
 * Standard mass validation logic for Interno Core.
 * Follows the "Forensic Rule": abs((Qty * Factor) - Weight) > Tolerance
 */
export const MASS_VALIDATION_TOLERANCE = 0.0001;

export function validateMovementMass(
  quantity: number,
  uomFactor: number,
  declaredWeight: number
): boolean {
  if (quantity <= 0 || uomFactor <= 0 || declaredWeight <= 0) return false;
  
  const expectedWeight = quantity * uomFactor;
  const discrepancy = Math.abs(expectedWeight - declaredWeight);
  
  return discrepancy <= MASS_VALIDATION_TOLERANCE;
}

/**
 * Calculates the total weight and item count for a set of movements.
 */
export function calculateTotals(movements: { quantity: number; weight?: number; uomFactor?: number }[]) {
  return movements.reduce(
    (acc, m) => {
      acc.totalItems += m.quantity;
      acc.totalWeight += m.weight || (m.quantity * (m.uomFactor || 1));
      return acc;
    },
    { totalItems: 0, totalWeight: 0 }
  );
}
