#!/bin/sh
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando servidor..."
exec gunicorn poketrip.wsgi:application --bind 0.0.0.0:8000 --workers 3
