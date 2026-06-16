#!/bin/sh
# entrypoint.sh — Punto de entrada inteligente para ICM
# Soporta modos: dev, test, production según variable SKIP_DB_WAIT

set -e

# Modo test (SQLite in-memory): no requiere PostgreSQL
if [ "${SKIP_DB_WAIT}" = "1" ]; then
    echo "[ENTRYPOINT] Modo test — saltando espera de BD, migraciones y collectstatic"
    exec "$@"
fi

echo "[ENTRYPOINT] Esperando PostgreSQL en ${DB_HOST:-db}:${DB_PORT:-5432}..."
until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-icm_user}"; do
    sleep 1
done
echo "[ENTRYPOINT] PostgreSQL disponible"

echo "[ENTRYPOINT] Ejecutando migraciones..."
python manage.py migrate --noinput

echo "[ENTRYPOINT] Ejecutando collectstatic..."
python manage.py collectstatic --noinput --clear

exec "$@"
