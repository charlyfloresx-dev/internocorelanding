"""
Integration Tests — Refresh Token Rotation (RTR) Phase C.

Cubre todos los escenarios del handler de 8 fases:
- Normal rotation (gen increment)
- Concurrent refresh (grace pattern)
- Failover idempotency (2s window)
- Reuse detection (breach → family revoked)
- Company binding validation (HMAC tampering)
- Family revocation rejection
- Multi-tenant isolation
- Audit logging
"""
import pytest
import jwt
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from sqlalchemy import select

from auth_app.domain.handlers.refresh_token_handler import (
    RefreshTokenHandler,
    RefreshTokenCommand
)
from auth_app.infrastructure.repositories.sqlalchemy_refresh_token_repo import (
    SQLAlchemyRefreshTokenRepository
)
from auth_app.domain.exceptions.refresh_token_exceptions import (
    RefreshTokenExpiredError,
    RefreshTokenRevokedError,
    RefreshTokenReuseDetectedError,
    CompanyIdMismatchError,
    RefreshTokenInvalidFamilyError,
    RefreshTokenInvalidError
)
from auth_app.models.refresh_token_family import RefreshTokenRotationAudit as AuditModel


def get_family_vo(db, test_family, test_company):
    """Obtener TokenFamily VO desde ORM model via repo."""
    return SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)


class TestRefreshTokenRotationNormal:
    """Tests para flujo normal de rotación."""

    @pytest.mark.asyncio
    async def test_refresh_successful_increments_generation(
        self, db, test_family, test_user, test_company, secret_key
    ):
        """Rotación normal: gen 0 → gen 1."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        assert family_vo.current_generation == 0

        initial_refresh_token = handler._issue_refresh_token(family_vo)

        cmd = RefreshTokenCommand(
            refresh_token=initial_refresh_token,
            ip_address="127.0.0.1",
            user_agent="test-client"
        )

        response = await handler.execute(cmd)
        await db.commit()

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.expires_in == 3600

        updated_family = await repo.get_family(test_family.id, test_company.id)
        assert updated_family.current_generation == 1

    @pytest.mark.asyncio
    async def test_multiple_rotations_increments_sequentially(
        self, db, test_family, test_user, test_company, secret_key
    ):
        """Múltiples rotaciones incrementan generación secuencialmente (0→1→2→3)."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_id = test_family.id
        company_id = test_company.id

        for expected_gen in range(3):
            current_family = await repo.get_family(family_id, company_id)
            token = handler._issue_refresh_token(current_family)
            cmd = RefreshTokenCommand(
                refresh_token=token,
                ip_address="127.0.0.1",
                user_agent="test"
            )
            await handler.execute(cmd)
            await db.commit()

            updated = await repo.get_family(family_id, company_id)
            assert updated.current_generation == expected_gen + 1


class TestRefreshTokenRotationConcurrency:
    """Tests para race conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_refresh_graceful_handling(
        self, db, test_family, test_company, secret_key
    ):
        """Dos requests con mismo token: segundo recibe tokens del ganador (grace)."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        token = handler._issue_refresh_token(family_vo)

        # Primer request
        cmd1 = RefreshTokenCommand(
            refresh_token=token, ip_address="127.0.0.1", user_agent="browser"
        )
        response1 = await handler.execute(cmd1)
        await db.commit()

        # Segundo request con mismo token (simula race: idempotency window expiró en fixture)
        cmd2 = RefreshTokenCommand(
            refresh_token=token, ip_address="192.168.1.1", user_agent="mobile"
        )
        # Gen 0 token, familia en gen 1 → gap < 1 → no es breach → rota o devuelve cached
        response2 = await handler.execute(cmd2)
        await db.commit()

        assert response1.access_token is not None
        assert response2.access_token is not None
        assert response1.refresh_token != token
        assert response2.refresh_token != token


class TestRefreshTokenRotationFailover:
    """Tests para RDS failover resilience."""

    @pytest.mark.asyncio
    async def test_idempotent_retry_within_window(
        self, db, test_family, test_company, secret_key
    ):
        """Mismo JTI dentro de 2s → retorna tokens cacheados (idempotencia failover)."""
        from datetime import timedelta
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)

        # Primer refresh (establece last_refresh_jti + ventana de 2s)
        token = handler._issue_refresh_token(family_vo)
        cmd = RefreshTokenCommand(
            refresh_token=token, ip_address="127.0.0.1", user_agent="test"
        )
        response1 = await handler.execute(cmd)
        await db.commit()

        # Extender la ventana vía ORM para que la identity map refleje el nuevo valor
        from sqlalchemy import select
        from auth_app.models.refresh_token_family import RefreshTokenFamily
        from datetime import timezone
        stmt = select(RefreshTokenFamily).where(RefreshTokenFamily.id == test_family.id)
        family_row = (await db.execute(stmt)).scalar_one()
        family_row.refresh_window_expires_at = datetime.now(timezone.utc) + timedelta(seconds=60)
        await db.flush()

        # Segundo request con mismo token original (retry dentro del window)
        response2 = await handler.execute(cmd)
        await db.flush()

        assert response2.access_token is not None
        assert response2.refresh_token is not None

        # Idempotencia: la generación NO debe incrementar (sigue en 1, no pasa a 2)
        # _return_cached_tokens emite tokens nuevos (JTI fresco) pero para la MISMA generación
        final_family = await repo.get_family(test_family.id, test_company.id)
        assert final_family.current_generation == 1


class TestRefreshTokenRotationReuse:
    """Tests para detección de reuse/breach."""

    @pytest.mark.asyncio
    async def test_reuse_detection_generation_gap(
        self, db, test_family, test_company, secret_key
    ):
        """Token gen 0 con familia en gen 2 → breach → familia revocada."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_id = test_family.id
        company_id = test_company.id

        # Guardar token gen 0
        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        token_gen_0 = handler._issue_refresh_token(family_vo)

        # Rotar 2 veces (gen 0 → 1 → 2)
        for _ in range(2):
            current_family = await repo.get_family(family_id, company_id)
            token = handler._issue_refresh_token(current_family)
            cmd = RefreshTokenCommand(
                refresh_token=token, ip_address="127.0.0.1", user_agent="test"
            )
            await handler.execute(cmd)
            await db.commit()

        # Intentar replay con token gen 0 (familia en gen 2)
        cmd_replay = RefreshTokenCommand(
            refresh_token=token_gen_0, ip_address="127.0.0.1", user_agent="attacker"
        )

        with pytest.raises(RefreshTokenReuseDetectedError):
            await handler.execute(cmd_replay)

        # Familia debe estar revocada
        revoked_family = await repo.get_family(family_id, company_id)
        assert revoked_family is None or revoked_family.revoked_at is not None


class TestRefreshTokenRotationSecurity:
    """Tests para validaciones de seguridad."""

    @pytest.mark.asyncio
    async def test_company_id_binding_tampering_detected(
        self, db, test_family, test_company, secret_key
    ):
        """Adulteración de company_id en token → detectado vía filtro compound WHERE (IDOR defense)."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        token = handler._issue_refresh_token(family_vo)

        # Decodificar y adulterar company_id (campo "co")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        payload["co"] = str(uuid4())
        tampered_token = jwt.encode(payload, secret_key, algorithm="HS256")

        cmd = RefreshTokenCommand(
            refresh_token=tampered_token, ip_address="127.0.0.1", user_agent="attacker"
        )

        # get_family() filtra por (family_id, company_id) → tampered company_id no encuentra la familia
        # Defensa: compound WHERE en FASE 2 previene IDOR antes de llegar a validación HMAC en FASE 3
        with pytest.raises(RefreshTokenInvalidFamilyError):
            await handler.execute(cmd)

    @pytest.mark.asyncio
    async def test_revoked_family_rejects_refresh(
        self, db, test_family, test_company, secret_key
    ):
        """Family revocada → RefreshTokenRevokedError."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        # Obtener VO ANTES de revocar (estado gen=0, active)
        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        token = handler._issue_refresh_token(family_vo)

        # Revocar la familia
        await repo.revoke_family(test_family.id, test_company.id, "SECURITY_ALERT")
        await db.flush()

        # Usar el token emitido antes de la revocación → FASE 4 detecta revocación
        cmd = RefreshTokenCommand(
            refresh_token=token, ip_address="127.0.0.1", user_agent="test"
        )

        with pytest.raises(RefreshTokenRevokedError):
            await handler.execute(cmd)


class TestRefreshTokenRotationMultiTenant:
    """Tests para multi-tenancy isolation."""

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(
        self, db, test_family, test_company, secret_key
    ):
        """Token con company_id de otra empresa → IDOR bloqueado."""
        from auth_app.models import Company as CompanyModel
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        company2 = CompanyModel(
            id=uuid4(),
            name="Company 2 RTR",
            status="ACTIVE",
        )
        db.add(company2)
        await db.flush()

        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        token = handler._issue_refresh_token(family_vo)

        # Adulterar: cambiar company_id al de empresa 2
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        payload["co"] = str(company2.id)
        tampered_token = jwt.encode(payload, secret_key, algorithm="HS256")

        cmd = RefreshTokenCommand(
            refresh_token=tampered_token, ip_address="127.0.0.1", user_agent="test"
        )

        # compound WHERE: token con company2.id no encuentra la familia (que pertenece a company1)
        with pytest.raises(RefreshTokenInvalidFamilyError):
            await handler.execute(cmd)


class TestRefreshTokenRotationAudit:
    """Tests para audit logging."""

    @pytest.mark.asyncio
    async def test_audit_log_captures_rotation_event(
        self, db, test_family, test_company, secret_key
    ):
        """Audit log registra ROTATED con generaciones y IP."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        token = handler._issue_refresh_token(family_vo)
        cmd = RefreshTokenCommand(
            refresh_token=token, ip_address="192.168.1.100", user_agent="Mozilla/5.0"
        )
        await handler.execute(cmd)
        await db.commit()

        stmt = select(AuditModel).where(
            (AuditModel.family_id == test_family.id) &
            (AuditModel.action == "ROTATED")
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

        assert len(events) == 1
        assert events[0].ip_address == "192.168.1.100"
        assert events[0].old_generation == 0
        assert events[0].new_generation == 1

    @pytest.mark.asyncio
    async def test_audit_log_captures_breach_detection(
        self, db, test_family, test_company, secret_key
    ):
        """Audit log registra REUSE_DETECTED cuando se detecta brecha."""
        repo = SQLAlchemyRefreshTokenRepository(db)
        handler = RefreshTokenHandler(repo, secret_key)

        family_id = test_family.id
        company_id = test_company.id

        family_vo = SQLAlchemyRefreshTokenRepository._model_to_value_object(test_family)
        token_gen_0 = handler._issue_refresh_token(family_vo)

        # Rotar 2 veces
        for _ in range(2):
            current_family = await repo.get_family(family_id, company_id)
            token = handler._issue_refresh_token(current_family)
            cmd = RefreshTokenCommand(
                refresh_token=token, ip_address="127.0.0.1", user_agent="test"
            )
            await handler.execute(cmd)
            await db.commit()

        # Replay con token gen 0
        cmd_replay = RefreshTokenCommand(
            refresh_token=token_gen_0, ip_address="127.0.0.1", user_agent="attacker"
        )
        try:
            await handler.execute(cmd_replay)
        except RefreshTokenReuseDetectedError:
            pass
        await db.commit()

        stmt = select(AuditModel).where(
            (AuditModel.family_id == family_id) &
            (AuditModel.action == "REUSE_DETECTED")
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

        assert len(events) >= 1
        assert events[0].action == "REUSE_DETECTED"
