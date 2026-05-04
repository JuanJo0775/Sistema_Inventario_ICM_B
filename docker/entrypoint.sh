#!/bin/sh

echo "Esperando base de datos..."
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
