#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRET_FILE="${REPOSITORY_ROOT}/.kingaweb-development-secret"

if [[ ! -s "${SECRET_FILE}" ]]; then
  echo "Development secret is missing. Run ./scripts/setup-local-api.sh first." >&2
  exit 1
fi

export KINGAWEB_API_URL="http://127.0.0.1:8000"
export KINGAWEB_DEV_AUTH_SECRET="$(<"${SECRET_FILE}")"

cd "${REPOSITORY_ROOT}"
exec pnpm --filter @kingaweb/web dev
