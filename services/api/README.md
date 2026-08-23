# Control-Plane API

FastAPI-based service responsible for identity integration, workspaces, authorization, assets, findings, reports, subscriptions, audit events and job scheduling.

## Development

```bash
cd services/api
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn kingaweb_api.main:app --reload --port 8000
```

The health endpoint is available at `http://127.0.0.1:8000/health` and development API documentation at `http://127.0.0.1:8000/docs`.

Run database migrations after configuring `KINGAWEB_DATABASE_URL`:

```bash
alembic upgrade head
```

Protected endpoints require an OIDC bearer token with the configured issuer, audience and JWKS endpoint. Domain assets begin in `pending_verification`; scanning must not be scheduled until a separate verification worker confirms the DNS or HTTP challenge.

The API may request bounded scans only after policy and target-verification checks. It does not perform outbound scanning in the API process.
