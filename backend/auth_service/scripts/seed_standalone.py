# Standalone Seed Script - Python-Level Conflict Handling
import os
import asyncio
import logging
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext
import sqlalchemy.exc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def run_standalone_seed():
    logger.info(f"🚀 Iniciando SEED STANDALONE (Final Charly) en {DB_URL}...")
    engine = create_async_engine(DB_URL, pool_pre_ping=True, echo=False)
    
    # 0. Permanent Schema Adjustments
    async with engine.connect() as conn:
        logger.info("Verificando column identity_token...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS identity_token VARCHAR(255);"))
            await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_identity_token ON users (identity_token) WHERE identity_token IS NOT NULL;"))
            await conn.commit()
        except Exception as e:
            logger.warning(f"Schema adjustment warning: {e}")

    async with engine.connect() as conn:
        # 1. Business Group
        group_id = "eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e"
        try:
            await conn.execute(text("""
                INSERT INTO business_groups (id, name, description, is_active, version_id, created_at, updated_at)
                VALUES (:id, :name, :desc, True, 1, NOW(), NOW())
            """), {"id": group_id, "name": "InternoCorp Group", "desc": "Cluster de manufactura principal"})
            await conn.commit()
        except sqlalchemy.exc.IntegrityError:
            await conn.rollback()

        # 2. Companies
        companies = [
            {"id": "9cd9986b-89da-48b7-8733-26a2a1225b01", "name": "InternoCorp Enterprise", "gid": group_id},
            {"id": "ad6cc8a6-34f9-42df-8f29-28254e0ad242", "name": "Planta MX", "gid": group_id},
            {"id": "777cc8a6-34f9-42df-8f29-28254e0ad277", "name": "Planta US", "gid": group_id},
            {"id": "203e03c9-5d65-43ff-9e83-864ef605426c", "name": "Nueva Planta Demo", "gid": group_id}
        ]
        for c in companies:
            try:
                await conn.execute(text("""
                    INSERT INTO companies (id, name, parent_group_id, status, is_active, version_id, created_at, updated_at)
                    VALUES (:id, :name, :gid, 'ACTIVE', True, 1, NOW(), NOW())
                """), {"id": c["id"], "name": c["name"], "gid": c["gid"]})
                await conn.commit()
            except sqlalchemy.exc.IntegrityError:
                await conn.rollback()

        # 3. Roles
        roles_names = ["admin", "owner", "supervisor", "member", "operator"]
        for c in companies:
            for rname in roles_names:
                try:
                    await conn.execute(text("""
                        INSERT INTO roles (id, name, company_id, is_active, is_system_role, version_id, created_at, updated_at)
                        VALUES (:id, :name, :cid, True, False, 1, NOW(), NOW())
                    """), {"id": str(uuid.uuid4()), "name": rname, "cid": c["id"]})
                    await conn.commit()
                except sqlalchemy.exc.IntegrityError:
                    await conn.rollback()

        # 4. Users
        u_charly_id = "69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38"
        u_op_id = "d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a"
        
        users_in = [
            {"id": u_charly_id, "email": "charly@interno.com", "pwd": hash_password("charly123"), "token": None, "cid": companies[0]["id"]},
            {"id": u_op_id, "email": "op01@interno.com", "pwd": hash_password("operator123"), "token": "RFID123456", "cid": companies[1]["id"]}
        ]
        for u in users_in:
            try:
                await conn.execute(text("""
                    INSERT INTO users (id, email, hashed_password, identity_token, company_id, is_active, version_id, created_at, updated_at)
                    VALUES (:id, :email, :pwd, :token, :cid, True, 1, NOW(), NOW())
                """), u)
                await conn.commit()
            except sqlalchemy.exc.IntegrityError:
                await conn.rollback()
                await conn.execute(text("""
                    UPDATE users SET hashed_password = :pwd, identity_token = :token, email = :email WHERE id = :id
                """), u)
                await conn.commit()

        # 5. UserCompanyRole (Linking)
        # Charly -> Enterprise
        res = await conn.execute(text("SELECT id FROM roles WHERE name='admin' AND company_id='9cd9986b-89da-48b7-8733-26a2a1225b01'"))
        rid = res.scalar()
        if rid:
            try:
                await conn.execute(text("""
                    INSERT INTO user_company_roles (user_id, company_id, role_id, is_new, version_id, created_at, updated_at, scopes)
                    VALUES (:uid, '9cd9986b-89da-48b7-8733-26a2a1225b01', :rid, False, 1, NOW(), NOW(), '[]'::jsonb)
                """), {"uid": u_charly_id, "rid": rid})
                await conn.commit()
            except sqlalchemy.exc.IntegrityError:
                await conn.rollback()

        # Charly -> Planta MX
        res = await conn.execute(text("SELECT id FROM roles WHERE name='admin' AND company_id='ad6cc8a6-34f9-42df-8f29-28254e0ad242'"))
        rid = res.scalar()
        if rid:
            try:
                await conn.execute(text("""
                    INSERT INTO user_company_roles (user_id, company_id, role_id, is_new, version_id, created_at, updated_at, scopes)
                    VALUES (:uid, 'ad6cc8a6-34f9-42df-8f29-28254e0ad242', :rid, False, 1, NOW(), NOW(), '[]'::jsonb)
                """), {"uid": u_charly_id, "rid": rid})
                await conn.commit()
            except sqlalchemy.exc.IntegrityError:
                await conn.rollback()

        # Charly -> Planta US
        res = await conn.execute(text("SELECT id FROM roles WHERE name='admin' AND company_id='777cc8a6-34f9-42df-8f29-28254e0ad277'"))
        rid = res.scalar()
        if rid:
            try:
                await conn.execute(text("""
                    INSERT INTO user_company_roles (user_id, company_id, role_id, is_new, version_id, created_at, updated_at, scopes)
                    VALUES (:uid, '777cc8a6-34f9-42df-8f29-28254e0ad277', :rid, False, 1, NOW(), NOW(), '[]'::jsonb)
                """), {"uid": u_charly_id, "rid": rid})
                await conn.commit()
            except sqlalchemy.exc.IntegrityError:
                await conn.rollback()

        # Operator -> Tijuana
        res = await conn.execute(text("SELECT id FROM roles WHERE name='operator' AND company_id='ad6cc8a6-34f9-42df-8f29-28254e0ad242'"))
        rid_op = res.scalar()
        if rid_op:
            try:
                await conn.execute(text("""
                    INSERT INTO user_company_roles (user_id, company_id, role_id, is_new, version_id, created_at, updated_at, scopes)
                    VALUES (:uid, 'ad6cc8a6-34f9-42df-8f29-28254e0ad242', :rid, False, 1, NOW(), NOW(), '[]'::jsonb)
                """), {"uid": u_op_id, "rid": rid_op})
                await conn.commit()
            except sqlalchemy.exc.IntegrityError:
                await conn.rollback()

    logger.info("✅ SEED STANDALONE COMPLETADO.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_standalone_seed())
