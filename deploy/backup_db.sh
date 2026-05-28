#!/usr/bin/env bash
set -euo pipefail

# backup_db.sh
# Creates a compressed pg_dump in /srv/backups with timestamp and verifies integrity.
# Optional upload to S3 if AWS_* env vars and S3_BUCKET are set.

BACKUP_DIR=${BACKUP_DIR:-/srv/backups}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-14}
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
FNAME="db-backup-${TIMESTAMP}.sql.gz"
OUTPATH="${BACKUP_DIR}/${FNAME}"

mkdir -p "${BACKUP_DIR}"
chown --recursive root:root "${BACKUP_DIR}" || true
chmod 700 "${BACKUP_DIR}"

echo "Starting DB backup to ${OUTPATH}"

# Try direct pg_dump using env vars, else try docker-compose exec db
if command -v pg_dump >/dev/null 2>&1; then
  echo "Using local pg_dump"
  PGPASSWORD=${PGPASSWORD:-${POSTGRES_PASSWORD:-}} pg_dump -h ${PGHOST:-localhost} -U ${PGUSER:-postgres} ${PGDATABASE:-postgres} | gzip > "${OUTPATH}"
elif docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1; then
  echo "Using docker compose exec to run pg_dump inside db container"
  if docker compose ps db >/dev/null 2>&1; then
    docker compose exec -T db pg_dump -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-postgres} | gzip > "${OUTPATH}"
  else
    echo "No db service found in docker-compose, trying docker-compose"
    docker-compose exec -T db pg_dump -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-postgres} | gzip > "${OUTPATH}"
  fi
else
  echo "No pg_dump or docker compose available; cannot perform backup" >&2
  exit 2
fi

echo "Backup created, verifying gzip integrity"
if gunzip -t "${OUTPATH}"; then
  echo "Gzip integrity OK"
else
  echo "Backup integrity failed" >&2
  exit 3
fi

echo "Computing checksum"
sha256sum "${OUTPATH}" > "${OUTPATH}.sha256"

# Optional upload to S3
if [ -n "${S3_BUCKET:-}" ] && command -v aws >/dev/null 2>&1; then
  echo "Uploading backup to s3://${S3_BUCKET}/backups/"
  aws s3 cp "${OUTPATH}" "s3://${S3_BUCKET}/backups/${FNAME}" --only-show-errors
  aws s3 cp "${OUTPATH}.sha256" "s3://${S3_BUCKET}/backups/${FNAME}.sha256" --only-show-errors
fi

echo "Pruning backups older than ${RETENTION_DAYS} days in ${BACKUP_DIR}"
find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -name 'db-backup-*.sql.gz' -print -delete || true

echo "Backup completed: ${OUTPATH}"
echo "${OUTPATH}.sha256 created"
