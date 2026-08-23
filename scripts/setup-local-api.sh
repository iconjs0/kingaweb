#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIRECTORY="${REPOSITORY_ROOT}/services/api"
VIRTUAL_ENVIRONMENT="${API_DIRECTORY}/.venv"
DATABASE_FILE="${API_DIRECTORY}/kingaweb-development.db"

cd "${API_DIRECTORY}"

if [[ ! -x "${VIRTUAL_ENVIRONMENT}/bin/python" ]]; then
  python3 -m venv "${VIRTUAL_ENVIRONMENT}"
fi

"${VIRTUAL_ENVIRONMENT}/bin/pip" install -e '.[dev]'

export KINGAWEB_APP_ENVIRONMENT=development
export KINGAWEB_DATABASE_URL="sqlite+pysqlite:///${DATABASE_FILE}"

"${VIRTUAL_ENVIRONMENT}/bin/alembic" upgrade head
"${VIRTUAL_ENVIRONMENT}/bin/python" -m kingaweb_api.seed \
  --subject "development|owner" \
  --email "owner@kingaweb.local" \
  --workspace "KingaWeb Development"

echo "Local API setup complete. Run: ./scripts/start-local-api.sh"
