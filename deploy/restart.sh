#!/usr/bin/env bash
set -euo pipefail

# Script to run on the staging host at /srv/icm
cd /srv/icm || { echo "directory /srv/icm not found"; exit 1; }

# Login to GHCR if credentials provided
if [ -n "${GHCR_USER:-}" ] && [ -n "${GHCR_TOKEN:-}" ]; then
  echo "Logging in to ghcr.io as ${GHCR_USER}"
  echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USER}" --password-stdin || true
fi

echo "Pulling images and updating compose"
docker compose pull --ignore-pull-failures
docker compose up -d --remove-orphans

echo "Cleanup unused images"
docker image prune -f || true

echo "Deploy finished"
