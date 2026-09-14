# Free deployment: Render + Neon PostgreSQL

This project is prepared for a free Render Web Service and a free Neon PostgreSQL database.

## Why this setup

- Render Free hosts the Django site and provides HTTPS.
- Telegram uses a webhook, so the bot does not need a separate paid background worker.
- Neon Free provides PostgreSQL without the 30-day expiration of Render's Free Postgres.

## 1. Create the database

Create a project on Neon and copy its PostgreSQL connection string. It should look like:

`postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require`

Use that entire value as Render's `DATABASE_URL`.

## 2. Upload the code to GitHub

Create a new GitHub repository and upload the contents of this folder. Do NOT upload `.env`, `venv/`, `.git/`, or `__MACOSX/`.

## 3. Create the Render service

On Render, create **New -> Web Service**, connect the GitHub repository, and choose the **Free** plan.

Build command:

`pip install -r requirements.txt`

Start command:

`bash deploy/start.sh`

Health check path:

`/`

## 4. Environment variables

Set these in Render:

- `DEBUG=False`
- `SECRET_KEY` = a long random secret
- `DATABASE_URL` = Neon connection string
- `BOT_TOKEN` = Telegram bot token
- `BOT_WEBHOOK_SECRET` = random secret (letters/numbers, 20+ characters recommended)
- `ALLOWED_HOSTS` = your Render hostname, for example `online-shop-xxxx.onrender.com`
- `DJANGO_SUPERUSER_USERNAME` = your admin username
- `DJANGO_SUPERUSER_PASSWORD` = a strong admin password
- `DJANGO_SUPERUSER_EMAIL` = your email

Render also supplies `RENDER_EXTERNAL_URL` automatically. The deployment script uses it to configure the Telegram webhook.

## 5. Admin

The deployment automatically creates/updates a Django superuser from the three `DJANGO_SUPERUSER_*` environment variables. After deploy, open `/admin/` and log in with those credentials.

## 6. Important: media/images

Render Free has an ephemeral filesystem. Product images uploaded through Django Admin can disappear after a restart/redeploy. The database itself is persistent in Neon, but `/media/` is not.

For permanent product images, use an object-storage/image service such as Cloudinary or another S3-compatible service and change the Django storage configuration accordingly.

## 7. Telegram bot

The bot is converted from long polling to a webhook. Render starts the web server, `setup_webhook` automatically registers:

`https://YOUR-RENDER-HOST/telegram/webhook/`

The webhook endpoint validates `X-Telegram-Bot-Api-Secret-Token`.

## Security

Never commit `.env` or real Telegram tokens/passwords to GitHub. The old token in the original project should be revoked and replaced because it was stored in the uploaded project file.
