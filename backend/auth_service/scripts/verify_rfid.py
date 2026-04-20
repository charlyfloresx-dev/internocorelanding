import asyncio
import os
import sys

# Setup path
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [BACKEND_ROOT, SERVICE_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User

async def check_rfids():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User.email, User.rfid).where(User.email.in_(['charly@interno.com', 'operador@interno.com'])))
        print('--- DB VALIDATION ---')
        for r in res.all():
            print(f'Email: {r[0]} | RFID: {r[1]}')

if __name__ == "__main__":
    asyncio.run(check_rfids())
