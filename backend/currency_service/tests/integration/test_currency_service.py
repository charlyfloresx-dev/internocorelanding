import pytest
import uuid
from httpx import AsyncClient
from decimal import Decimal

# La URL del servicio dentro del contenedor
BASE_URL = "http://localhost:8000"

@pytest.mark.anyio
async def test_health_check():
    """Verifica que el servicio esté vivo."""
    async with AsyncClient(base_url=BASE_URL) as ac:
        response = await ac.get("/health")
    assert response.status_code == 200

@pytest.mark.anyio
async def test_manual_rate_update_flow():
    """Verifica el flujo completo de actualización manual vía API."""
    cid = str(uuid.uuid4())
    uid = str(uuid.uuid4())
    
    payload = {
        "base_currency": "USD",
        "target_currency": "MXN",
        "rate": 18.50
    }
    
    headers = {
        "X-Company-Id": cid,
        "X-User-Id": uid
    }
    
    async with AsyncClient(base_url=BASE_URL) as ac:
        # 1. Crear rate manual
        response = await ac.post("/api/v1/currencies/manual", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert float(data["rate"]) == 18.5
        
        # 2. Verificar que aparezca en el summary
        resp_sum = await ac.get(f"/api/v1/currencies/latest?base=USD&targets=MXN", headers=headers)
        assert resp_sum.status_code == 200
        summary_data = resp_sum.json()
        rates = summary_data["rates"]
        
        # El campo corregido es 'currency' y el valor 'current_stored_rate'
        mxn_rate = next((r for r in rates if r["currency"] == "MXN"), None)
        assert mxn_rate is not None
        assert float(mxn_rate["current_stored_rate"]) == 18.5
