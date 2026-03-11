import httpx
import asyncio
import jwt

BASE_URL_AUTH = "http://localhost:8001"
DEMO_USER = "admin@interno.com"
DEMO_PASS = "admin123456"

async def diag():
    async with httpx.AsyncClient() as client:
        r_login = await client.post(f"{BASE_URL_AUTH}/api/v1/auth/login", json={
            "email": DEMO_USER,
            "password": DEMO_PASS
        })
        login_data = r_login.json()["data"]
        token = login_data["selection_token"]
        print(f"Token: {token}")
        
        # Decode without verification
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"Decoded: {decoded}")

if __name__ == "__main__":
    asyncio.run(diag())
