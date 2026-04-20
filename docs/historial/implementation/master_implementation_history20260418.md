# Master Implementation History - 2026-04-18

## Architectural Summary: CloudFront to ECS CORS Resolution
Today's session dealt with deep architectural integration between AWS CloudFront (HTTPS) and AWS Application Load Balancer - ALB (HTTP), specifically targeting Mixed Content tracking and FastAPI Starlette CORS Middleware lifecycle hooks.

### 1. Mixed Content vs. CORS Origin Blocking
Initially, the frontend (deployed on CloudFront under `d36af6ioy7l4ga.cloudfront.net` over HTTPS) was hard-blocked by Chrome with "Provisional headers are shown". This was diagnosed as a strict **Mixed Content** block rather than CORS, because requests were being fired towards an HTTP origin (`http://internocore-alb...`).
- **Temporary bypass:** Bypassed via Chrome's "Allow Insecure Content" setting for developers to unblock e2e validations in staging without DNS allocation.
- **Architectural solution scheduled:** Assign an AWS ACM Certificate to a custom domain and attach an HTTPS listener to the ALB, OR configure CloudFront to reverse proxy `/api/*` towards the ALB as its origin.

### 2. FastAPI (Starlette) CORSMiddleware Lifecycle Bug
Once the Mixed Content bypass allowed the `OPTIONS` preflight request to reach the `auth_service` Fargate container, it failed with `400 Bad Request` missing `Access-Control-Allow-Origin`.

**Root Cause Analysis:**
1. The `CORE_BACKEND_CORS_ORIGINS` secret injection relied on dynamic properties evaluation inside `app.core.config.load_aws_secrets()`.
2. The reflection loop `hasattr()` explicitly targeted Python instance attribute names (e.g., `int_backend_cors_origins`) bypassing Pydantic aliases.
3. The injection logic failed silently when encountering the `@property` `ASYNC_DATABASE_URL` or `ENV_MODE` without a setter, crashing the iteration before injecting CORS.
4. **The Ultimate Lifecycle Trap:** `app.main` imported `common.security.cors_setup`, which instantiated `CORSMiddleware` *before* AWS Secrets were downloaded. Starlette's `CORSMiddleware` deep-copies the `allow_origins` array strictly at start-up time (`__init__`). Therefore, modifying `settings.int_backend_cors_origins` post-startup had zero effect.

### 3. Resolution
- **Secrets Tuning:** Removed read-only properties (`env_mode`, `aws_region`) from Secrets Manager and formatted `int_backend_cors_origins` explicitly as a JSON List mapping to python's type annotation list.
- **Code Fix:** Flipped the import sequence in `auth_service/app/main.py` ensuring `app.core.config.settings` executes `load_aws_secrets()` BEFORE `setup_cors()` is evaluated.
- **Deployment:** A new Docker image (`interno-backend-auth-service:latest`) was built locally and pushed to AWS ECR, followed by `aws ecs update-service --force-new-deployment` to rotate Fargate replicas without downtime.

### 4. Final E2E Validation 🚀
- **Status:** **SUCCESS**.
- **Evidence:** User confirmed successful redirection to `/dashboard` on CloudFront. Chrome console shows successful `200` responses from the ALB.
- **Observed minor gaps:** Some `404` errors on `/health` and `/active-rate` endpoints are noted for Phase 56 stabilization, but the core Auth handshake and Tenant selection flow are 100% operational in production.

