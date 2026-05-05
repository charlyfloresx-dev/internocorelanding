import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get('http://localhost:8000/api/v1/audit/')
            print(f'Status: {r.status_code}')
            print(f'Body: {r.text[:200]}')
        except Exception as e:
            print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(test())
