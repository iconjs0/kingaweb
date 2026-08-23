#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIRECTORY="${REPOSITORY_ROOT}/services/api"
DATABASE_FILE="${API_DIRECTORY}/kingaweb-development.db"

export KINGAWEB_APP_ENVIRONMENT=development
export KINGAWEB_DATABASE_URL="sqlite+pysqlite:///${DATABASE_FILE}"

cd "${API_DIRECTORY}"
exec .venv/bin/uvicorn kingaweb_api.main:app --reload --host 127.0.0.1 --port 8000
