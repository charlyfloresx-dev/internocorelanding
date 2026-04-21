import asyncio
import uuid
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock

# Setup paths
sys.path.append('/app')
sys.path.append('/app/common')

from auth_app.core.database import AsyncSessionLocal
from common.models.audit_log import AuditLog
from common.audit.logger import AuditLogger

async def debug_login_audit():
    print("Testing AuditLogger.log_action (simulating login)...")
    async with AsyncSessionLocal() as session:
        try:
            # Mock request
            request = MagicMock()
            request.client.host = "127.0.0.1"
            request.headers = {"user-agent": "diagnostic-tool", "x-trace-id": str(uuid.uuid4())}
            
            print("Calling AuditLogger.log_action...")
            await AuditLogger.log_action(
                db=session,
                action="AUTH_LOGIN_HANDSHAKE",
                table_name="users",
                record_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                request=request
            )
            print("Flushing...")
            await session.flush()
            print("Committing...")
            await session.commit()
            print("✅ DIAGNOSTIC SUCCESS")
        except Exception as e:
            print(f"❌ CAUSE OF 500 ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(debug_login_audit())
