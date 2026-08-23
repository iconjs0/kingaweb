# Control-Plane API

FastAPI-based service responsible for identity integration, workspaces, authorization, assets, findings, reports, subscriptions, audit events and job scheduling.

## Development

For a zero-container local environment from the repository root:

```bash
./scripts/setup-local-api.sh
./scripts/start-local-api.sh
```

This creates an ignored SQLite development database, applies the same Alembic migration used for PostgreSQL and seeds an idempotent development workspace. SQLite is a local convenience only; staging and production remain PostgreSQL.

The setup also generates an ignored, permission-restricted development signing secret. Both local start scripts read that secret so the web app can issue one-hour development sessions. This HS256 path is accepted only when the API environment is `development`; staging and production require configured RS256 OIDC.

In a second terminal, start the web application:

```bash
./scripts/start-local-web.sh
```

Manual setup:

```bash
cd services/api
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn kingaweb_api.main:app --reload --port 8000
```

The liveness endpoint is available at `http://127.0.0.1:8000/health`, database readiness at `http://127.0.0.1:8000/ready` and development API documentation at `http://127.0.0.1:8000/docs`.

Run database migrations after configuring `KINGAWEB_DATABASE_URL`:

```bash
alembic upgrade head
```

Protected endpoints require an OIDC bearer token with the configured issuer, audience and JWKS endpoint. Domain assets begin in `pending_verification`; scanning must not be scheduled until a separate verification worker confirms the DNS or HTTP challenge.

The API may request bounded scans only after policy and target-verification checks. It does not perform outbound scanning in the API process.
