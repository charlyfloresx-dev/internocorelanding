# Common Infrastructure - Service Log

## [2026-06-03] Phase 179A — Critical Security Audit Findings

**Three critical security vulnerabilities detected in Phase 179A audit across shared infrastructure components:**

### Finding B.1 (CRITICAL): Bypass/Admin Key Timing Attack
- File: `security/limiter.py` (line ~32-34)
- Issue: Admin/bypass key validation uses `==` comparison instead of `hmac.compare_digest()`
- Risk: Timing attack allows offline brute-force cracking of internal keys within hours
- Impact: **HIGH** — compromises X-Internal-Secret and X-Admin-Master-Key bypass mechanisms
- Mitigation: Replace `==` with `hmac.compare_digest()` for constant-time comparison
- Phase 179A P0.1: 30 minutes implementation + tests
- Timeline: 2026-06-04 (start of critical phase)

### Finding C.1 (CRITICAL): god_mode JWT Falsification
- File: `middleware.py` (line ~180-200)
- Issue: `god_mode` claim is read directly from JWT without server-side session store verification
- Risk: Client can forge `god_mode=true` in JWT to bypass authorization checks
- Impact: **CRITICAL** — elevation to admin privileges without valid session
- Mitigation: Verify `god_mode` status against Redis session store before trusting JWT
- Phase 179A P0.3: 4 hours for session store architecture + implementation
- Timeline: 2026-06-04 (priority 2)

### Finding C.3 (CRITICAL): Scope Elevation Risk
- File: `middleware.py` (line ~120-140)
- Issue: User scopes embedded in JWT are trusted without server-side database validation
- Risk: Client can inject elevated scopes to gain unauthorized access to resources
- Impact: **CRITICAL** — privilege escalation without legitimate authorization
- Mitigation: Validate scopes against database SSOT before accepting JWT claims
- Phase 179A P0.4: 6 hours for service layer refactor + tests
- Timeline: 2026-06-04-05

**Compliance Status:** 70% (3 errors, 96 files audited)

**Blockers:** All three findings block Phase 179A completion
- **P0.1 (B.1):** 30 min
- **P0.3 (C.1):** 4 hours
- **P0.4 (C.3):** 6 hours
- **Subtotal:** 10.5 hours (can parallelize into 2 days with 3 developers)

**Cloud Deployment:** BLOCKED until all findings remediated. Target: 2026-06-06.

---

## Architecture Notes

**Multi-tenancy Enforcement (Muro de Hierro):**
- All security-critical infrastructure lives in `backend/common/`
- `database.py`: RLS with Postgres row-level security
- `middleware.py`: Request authentication and JWT validation
- `security/limiter.py`: Rate limiting with Redis backend
- `security/cors_setup.py`: CORS configuration for multi-tenant isolation

**Auth Flow:**
1. `T1 Login` => refresh_token issued with RTR family
2. `T2 Select-Company` => select company => new access token + refresh_token
3. `Request` => JWT validated, scopes checked, tenant isolation enforced
4. `Refresh` => RTR family rotated, breach detection triggers alerts

**Security Layers:**
- Layer 1: JWT signature verification (hmac.compare_digest required)
- Layer 2: Admin bypass key validation (hmac.compare_digest required)
- Layer 3: Session store verification (god_mode, permission status)
- Layer 4: Database SSOT validation (scopes, roles, permissions)
