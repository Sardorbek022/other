# #!/usr/bin/env bash
# set -euo pipefail

# echo "==> Running database migrations..."
# python manage.py migrate --noinput

# echo "==> Creating admin if needed..."
# python manage.py shell -c "
# from django.contrib.auth import get_user_model
# import os

# User = get_user_model()
# username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
# email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
# password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

# if username and password:
#     user, created = User.objects.get_or_create(
#         username=username,
#         defaults={
#             'email': email or '',
#             'is_staff': True,
#             'is_superuser': True,
#         }
#     )

#     if created:
#         user.set_password(password)
#         user.is_staff = True
#         user.is_superuser = True
#         user.save()
#         print('==> Admin created successfully.')
#     else:
#         user.email = email or user.email
#         user.is_staff = True
#         user.is_superuser = True
#         user.set_password(password)
#         user.save()
#         print('==> Admin already exists; password updated.')
# else:
#     print('==> Admin environment variables are not configured.')
# "

# echo "==> Collecting static files..."
# python manage.py collectstatic --noinput

# echo "==> Starting Gunicorn..."
# exec gunicorn core.wsgi:application \
#   --bind 0.0.0.0:${PORT:-8000} \
#   --workers 1 \
#   --threads 4 \
#   --timeout 120 \
#   --access-logfile - \
#   --error-logfile -
#!/usr/bin/env bash

set -euo pipefail


echo "========================================"
echo "1. DATABASE MIGRATIONS"
echo "========================================"

python manage.py migrate --noinput


echo "========================================"
echo "2. CREATE / UPDATE ADMIN"
echo "========================================"

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

    user.email = email or user.email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()

    if created:
        print('==> Admin created successfully.')
    else:
        print('==> Admin already exists; password updated.')

else:

    print('==> Admin environment variables are not configured.')
"


echo "========================================"
echo "3. COLLECT STATIC"
echo "========================================"

python manage.py collectstatic --noinput


echo "========================================"
echo "4. SET TELEGRAM WEBHOOK"
echo "========================================"

python - <<'PY'

import json
import os
import urllib.request


token = os.environ.get("BOT_TOKEN")

secret = os.environ.get(
    "BOT_WEBHOOK_SECRET"
)

render_url = os.environ.get(
    "RENDER_EXTERNAL_URL",
    "https://other-1.onrender.com"
)


if not token:

    raise SystemExit(
        "ERROR: BOT_TOKEN is missing"
    )


webhook_url = (
    render_url.rstrip("/")
    + "/telegram/webhook/"
)


data = {
    "url": webhook_url,
}


if secret:

    data["secret_token"] = secret


request = urllib.request.Request(

    f"https://api.telegram.org/bot{token}/setWebhook",

    data=json.dumps(data).encode("utf-8"),

    headers={
        "Content-Type": "application/json"
    },

    method="POST",
)


try:

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

except Exception as e:

    raise SystemExit(
        f"ERROR: Telegram webhook request failed: {e}"
    )


if not result.get("ok"):

    raise SystemExit(
        f"ERROR: Telegram rejected webhook: {result}"
    )


print(
    "==> Telegram webhook successfully set:"
)

print(
    f"==> {webhook_url}"
)

PY


echo "========================================"
echo "5. START DJANGO / GUNICORN"
echo "========================================"

exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
