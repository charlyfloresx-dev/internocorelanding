import asyncio
import uuid
import sys
import os
from datetime import datetime

# Setup paths
sys.path.append('/app')
sys.path.append('/app/common')

from app.core.database import AsyncSessionLocal
from common.models.audit_log import AuditLog

async def test_audit_insert():
    print("Testing AuditLog insert...")
    async with AsyncSessionLocal() as session:
        try:
            log = AuditLog(
                id=str(uuid.uuid4()),
                action="DIAGNOSTIC_TEST",
                table_name="none",
                record_id="0",
                user_id="test_user",
                timestamp=datetime.utcnow()
            )
            session.add(log)
            await session.commit()
            print("✅ Insert and Commit SUCCESSFUL")
        except Exception as e:
            print(f"❌ ERROR during insert: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(test_audit_insert())
