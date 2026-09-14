#!/usr/bin/env bash
set -euo pipefail

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Creating admin if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if username and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email or '',
            'is_staff': True,
            'is_superuser': True,
        }
    )

    if created:
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print('==> Admin created successfully.')
    else:
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        print('==> Admin already exists; password updated.')
else:
    print('==> Admin environment variables are not configured.')
"

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
