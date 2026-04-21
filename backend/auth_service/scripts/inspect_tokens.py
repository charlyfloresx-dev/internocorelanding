import sys
import os
import asyncio
import json
from datetime import datetime, timezone

# Add the parent directory to sys.path to allow imports from 'app'
# This assumes the script is run from backend/auth_service/ or backend/auth_service/scripts/
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from jose import jwt, JWTError
    from sqlalchemy import select
    from auth_app.core.config import settings
    from auth_app.db.session import AsyncSessionLocal
    # Attempt to import models. Adjust if your project structure uses specific submodules without __init__ exports.
    from auth_app.models import User, UserCompanyRole
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import auth_application modules.\nDetails: {e}")
    print(f"PYTHONPATH: {sys.path}")
    print("Ensure you are running this script with the backend/auth_service environment active.")
    sys.exit(1)

def inspect_token(token: str):
    print("\n" + "="*60)
    print("🕵️  TOKEN INSPECTION TOOL")
    print("="*60)
    
    if not token:
        print("❌ No token provided.")
        return

    # 1. Decode without verification to get headers
    try:
        header = jwt.get_unverified_header(token)
        print(f"[*] Algorithm: {header.get('alg')}")
        print(f"[*] Type:      {header.get('typ')}")
    except Exception as e:
        print(f"[!] Error reading header: {e}")
        return

    # 2. Verify Signature
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        print("[*] Signature: ✅ VALID (Matches server SECRET_KEY)")
    except JWTError as e:
        print(f"[!] Signature: ❌ INVALID - {e}")
        print("    (The token might be from a different environment or the SECRET_KEY is mismatched)")
        # Continue with unverified payload for debugging
        try:
            payload = jwt.get_unverified_claims(token)
        except:
            return

    # 3. Print Claims
    print("\n--- 📋 CLAIMS ---")
    print(f"User ID (sub): {payload.get('sub')}")
    print(f"Company ID:    {payload.get('company_id', 'N/A')}")
    
    scopes = payload.get('scopes')
    print(f"Scopes:        {scopes} (Type: {type(scopes).__name__})")
    
    roles = payload.get('roles')
    print(f"Roles:         {roles}")

    # 4. Expiration
    exp = payload.get('exp')
    if exp:
        exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        remaining = (exp_dt - now).total_seconds() / 60
        print(f"Expires:       {exp_dt} UTC")
        if remaining > 0:
            print(f"Status:        ✅ Active ({remaining:.2f} min remaining)")
        else:
            print(f"Status:        ❌ Expired ({abs(remaining):.2f} min ago)")
    else:
        print("Expires:       Never")

async def inspect_database():
    print("\n" + "="*60)
    print("🗄️  DATABASE DIAGNOSTIC (User: admin@interno.com)")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get User
            result = await db.execute(select(User).where(User.email == "admin@interno.com"))
            user = result.scalars().first()
            
            if not user:
                print("[!] User 'admin@interno.com' NOT FOUND in database.")
                return

            print(f"[*] User Found: {user.id} ({user.email})")

            # Get Roles
            result = await db.execute(
                select(UserCompanyRole)
                .where(UserCompanyRole.user_id == user.id)
                .limit(3)
            )
            roles = result.scalars().all()

            if not roles:
                print("[!] No UserCompanyRole records found for this user.")
            
            for i, role in enumerate(roles, 1):
                print(f"\n--- Record #{i} ---")
                print(f"Company ID: {role.company_id}")
                print(f"Role ID:    {role.role_id}")
                
                # Check Scopes format
                scopes = role.scopes
                print(f"Scopes DB:  {scopes}")
                print(f"Type:       {type(scopes)}")
                
                if isinstance(scopes, str):
                    try:
                        parsed = json.loads(scopes)
                        print(f"JSON Parse: ✅ Valid List -> {parsed}")
                    except:
                        print(f"JSON Parse: ❌ Invalid JSON string")
                elif isinstance(scopes, list):
                     print(f"Format:     ✅ Native List (PostgreSQL JSONB?)")

        except Exception as e:
            print(f"[!] Database Error: {e}")

async def main():
    print(f"Configuration Loaded:")
    print(f"- SECRET_KEY: {settings.SECRET_KEY[:5]}...{settings.SECRET_KEY[-5:] if settings.SECRET_KEY else 'None'}")
    print(f"- ALGORITHM:  {settings.ALGORITHM}")
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("\n👇 Paste the token below and press Enter:")
        token = input().strip()

    inspect_token(token)
    await inspect_database()

if __name__ == "__main__":
    # Fix for Windows Asyncio Loop
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
