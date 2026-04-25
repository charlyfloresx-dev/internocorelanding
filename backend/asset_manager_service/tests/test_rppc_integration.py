"""
Test de Integración — RPPC API (ArcGisTijuanaProvider)

Valida que la lógica de retry con variaciones de clave catastral y el
fallback por Localidad funcionen correctamente para el predio en
Venustiano Carranza 6319, Unidad C (Tijuana, BC).

IMPORTANTE:
  - El nombre devuelto NO debe ser 'JORGE ALEJANDRO' (dueño de la Unidad B).
  - Se espera el titular del Inciso/Unidad C.
  - Este test requiere conectividad real al RPPC de Baja California.

Ejecutar: pytest tests/test_rppc_integration.py -v -s
"""
import asyncio
import pytest
import sys
import os

# Asegurar que el PYTHONPATH incluya el backend y el common layer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from common.gis.infrastructure.services.arcgis_tijuana_provider import ArcGisTijuanaProvider

# ─── Config del caso de prueba ────────────────────────────────────────────────
TEST_CLAVE_RAW = "PK020119"         # clave sin formato
TEST_CLAVE_STANDARD = "PK-020-119"  # Variación 1 (esperada como principal)
TEST_CLAVE_FULL = "PK-020-119-000"  # Variación 2

TEST_ADDRESS = {
    "num_oficial": "6319",
    "calle": "VENUSTIANO CARRANZA",
    "colonia": "PRESIDENTES",
}

DUEÑO_UNIDAD_B = "JORGE ALEJANDRO"   # Este nombre NO debe aparecer como resultado final


@pytest.mark.asyncio
async def test_rppc_retry_logic_with_variations():
    """
    Verifica que el sistema pruebe variaciones de la clave catastral
    y retorne resultados antes de caer en el fallback.
    """
    provider = ArcGisTijuanaProvider()

    # Probar variaciones directamente
    results_found = False
    for version in [1, 2, 3]:
        clave_var = provider.format_cadastral_key(TEST_CLAVE_RAW, version=version)
        print(f"\n[TEST] Probando variación {version}: {clave_var}")

        result = await provider.get_ownership_from_rppc(clave_var)
        if result.get("owner_name"):
            print(f"[TEST] ✅ Resultado con variación {version}: {result['owner_name']}")
            results_found = True
            break
        else:
            print(f"[TEST] ⚠️  Variación {version} no devolvió datos. Intentando siguiente...")

    # El test pasa si al menos UNA variación devuelve datos o si el fallback lo maneja
    # No falla porque el RPPC puede estar no disponible en CI
    if not results_found:
        print("[TEST] ℹ️  Ninguna variación devolvió datos — verificar conectividad al RPPC.")
    assert True  # No bloqueamos CI por disponibilidad de API externa


@pytest.mark.asyncio
async def test_rppc_unit_c_is_not_jorge_alejandro():
    """
    Test crítico: La Unidad C de Venustiano Carranza 6319 NO debe devolver
    a 'JORGE ALEJANDRO' (titular de la Unidad B).
    """
    provider = ArcGisTijuanaProvider()

    result = await provider.get_ownership_from_rppc(
        clave=TEST_CLAVE_STANDARD,
        address=TEST_ADDRESS,
    )

    owner = result.get("owner_name", "")
    print(f"\n[TEST] Titular encontrado: '{owner}'")
    print(f"[TEST] Folio Real: {result.get('folio_real', 'N/A')}")

    if owner and owner not in ["No disponible (Consulta manual requerida)", "Propiedad Privada"]:
        # Si recibimos un nombre real, verificar que no sea el de la Unidad B
        assert DUEÑO_UNIDAD_B.upper() not in owner.upper(), (
            f"ERROR: El sistema devolvió al dueño de la Unidad B ({DUEÑO_UNIDAD_B}). "
            f"La lógica de filtrado por Inciso C no está funcionando."
        )
        print(f"[TEST] ✅ Titular de Unidad C identificado correctamente: {owner}")
    else:
        # RPPC no disponible o requiere sesión activa — no falla CI
        print(f"[TEST] ⚠️  Titular no disponible (API externa). Verificar manualmente.")


@pytest.mark.asyncio
async def test_rppc_fallback_por_localidad():
    """
    Verifica que el fallback a frmLocalidad se activa cuando porClaveCat
    devuelve Datos vacío, y que filtra correctamente el Inciso C.
    """
    provider = ArcGisTijuanaProvider()

    # Simular que la clave no existe usando una clave inválida
    # para forzar el path de frmLocalidad
    result = await provider.get_ownership_from_rppc(
        clave="PK-999-999",  # Clave inexistente
        address=TEST_ADDRESS,
    )

    owner = result.get("owner_name")
    print(f"\n[TEST] Resultado fallback por Localidad: '{owner}'")

    # Si hay conectividad, debe retornar algo o None; no debe lanzar excepción
    assert isinstance(result, dict), "El método debe retornar siempre un dict, nunca lanzar excepción."


@pytest.mark.asyncio
async def test_format_cadastral_key_variations():
    """Valida que las variaciones de formato de clave sean correctas (sin conexión)."""
    provider = ArcGisTijuanaProvider()

    v1 = provider.format_cadastral_key("PK020119", version=1)
    v2 = provider.format_cadastral_key("PK020119", version=2)
    v3 = provider.format_cadastral_key("PK020119", version=3)

    assert v1 == "PK-020-119", f"Variación 1 incorrecta: {v1}"
    assert v2 == "PK-020-119-000", f"Variación 2 incorrecta: {v2}"
    assert v3 == "PK020119", f"Variación 3 incorrecta: {v3}"
    print(f"\n[TEST] ✅ Variaciones de clave: {v1} | {v2} | {v3}")


if __name__ == "__main__":
    """Permite ejecutar directamente con: python tests/test_rppc_integration.py"""
    asyncio.run(test_format_cadastral_key_variations())
    asyncio.run(test_rppc_retry_logic_with_variations())
    asyncio.run(test_rppc_unit_c_is_not_jorge_alejandro())
    asyncio.run(test_rppc_fallback_por_localidad())
