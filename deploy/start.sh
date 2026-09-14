#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput
python manage.py ensure_admin
python manage.py collectstatic --noinput
python manage.py setup_webhook

exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
