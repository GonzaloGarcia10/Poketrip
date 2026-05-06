#!/bin/sh
set -e

PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-3}"

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando servidor..."
exec gunicorn poketrip.wsgi:application --bind "0.0.0.0:${PORT}" --workers "${WEB_CONCURRENCY}" --log-file -
