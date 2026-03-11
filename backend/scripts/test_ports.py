import httpx
import asyncio

async def test_ports():
    urls = [
        "http://localhost:8001/api/v1/auth/health", # Assuming health exists
        "http://localhost:8006/api/v1/health",
        "http://localhost:8007/api/v1/health"
    ]
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                r = await client.get(url)
                print(f"{url}: {r.status_code}")
            except Exception as e:
                print(f"{url}: FAILED - {e}")

if __name__ == "__main__":
    asyncio.run(test_ports())
