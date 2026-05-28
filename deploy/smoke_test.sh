#!/usr/bin/env bash
set -euo pipefail

# Simple smoke tests executed on the staging host against the local compose service
BASE_URL="${BASE_URL:-http://localhost:8000}"
paths=("/api/schema/" "/api/docs/")

for p in "${paths[@]}"; do
  url="${BASE_URL}${p}"
  echo "Checking ${url}"
  status=$(curl -s -o /dev/null -w "%{http_code}" "${url}") || status=000
  if [ "${status}" -ne 200 ]; then
    echo "Smoke test failed for ${p}: status ${status}"
    exit 2
  fi
done

echo "Smoke tests passed"
exit 0
