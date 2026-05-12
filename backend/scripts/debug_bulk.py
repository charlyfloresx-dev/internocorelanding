import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv(override=True)
load_dotenv("backend/.env", override=True)

BASE_URL = os.getenv("CORE_API_EXTERNAL_URL", "http://localhost:8000") + "/api/v1/inventory"
INTERNAL_SECRET = os.getenv("CORE_INTERNAL_API_KEY")
COMPANY_ID = os.getenv("TEST_COMPANY_ID")
PRODUCT_ID = os.getenv("TEST_PRODUCT_ID")
WAREHOUSE_ID = os.getenv("TEST_WAREHOUSE_ID")

async def test_bulk():
    print(f"URL: {BASE_URL}")
    print(f"Secret: {INTERNAL_SECRET}")
    print(f"Company: {COMPANY_ID}")
    
    payload = {
        "movements": [
            {
                "product_id": PRODUCT_ID,
                "warehouse_id": WAREHOUSE_ID,
                "transaction_type": "IN",
                "quantity_change": 10.0,
                "previous_balance": 0.0,
                "new_balance": 10.0,
                "comments": "DEBUG TEST"
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        headers = {
            "X-Internal-Secret": INTERNAL_SECRET,
            "X-Company-ID": COMPANY_ID
        }
        try:
            resp = await client.post(f"{BASE_URL}/bulk-load", json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_bulk())
