#!/usr/bin/env bash
set -euo pipefail

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Creating/updating admin..."
python manage.py ensure_admin

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn..."
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 1 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
