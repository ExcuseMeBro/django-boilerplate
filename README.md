# django-boilerplate

Production-ready Django starter based on BabyTime and DoctorAI patterns.

## Stack

- Django 6 + DRF + SimpleJWT
- Django Unfold admin
- PostgreSQL by default
- Redis + Channels
- MinIO S3-compatible media storage
- Uzbek, English, Russian i18n
- Single-file Docker Compose
- Phone + OTP auth skeleton

## Use as template

Click **Use this template** on GitHub, then:

```bash
cp .env.example .env
# Change SECRET_KEY, DB_PASSWORD, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD.

docker compose up --build
```

Admin user:

```bash
docker compose exec backend python manage.py createsuperuser
```

URLs:

- API health: `http://localhost:8000/api/health/`
- Admin: `http://localhost:8000/admin/`
- MinIO S3: `http://localhost:9000`
- MinIO console: `http://localhost:9001`

## i18n

Supported languages:

- `uz` — Uzbek default
- `en` — English
- `ru` — Russian

API language selection uses `Accept-Language`:

```bash
curl -H 'Accept-Language: ru' http://localhost:8000/api/health/
curl -H 'Accept-Language: en' http://localhost:8000/api/v1/config/
```

Admin language also follows Django locale middleware. Custom admin labels, Unfold sidebar, model verbose names, API responses, and common DRF errors are translated.

After changing text:

```bash
python manage.py makemessages -l uz -l en -l ru
# edit locale/*/LC_MESSAGES/django.po
python manage.py compilemessages
```

## Production notes

`.env` da shularni majburiy almashtiring:

```env
SECRET_KEY=long-random-secret
DEBUG=False
ALLOWED_HOSTS=api.example.com
ENABLE_HTTPS_REDIRECT=True
CSRF_TRUSTED_ORIGINS=https://api.example.com
CORS_ALLOWED_ORIGINS=https://example.com
DB_PASSWORD=long-random-db-password
MINIO_ROOT_USER=long-access-key
MINIO_ROOT_PASSWORD=long-random-secret-key
MINIO_ENDPOINT=media.example.com
MINIO_USE_HTTPS=True
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | Health check |
| POST | `/api/v1/auth/otp/send/` | Send OTP |
| POST | `/api/v1/auth/otp/verify/` | Verify OTP, return JWT |
| GET/PATCH | `/api/v1/auth/me/` | Current user |
| POST | `/api/v1/devices/token/` | Register push token |
| GET | `/api/v1/notifications/` | List notifications |
| POST | `/api/v1/notifications/read/` | Mark all read |
| GET | `/api/v1/config/` | Public app config |

## Security audit summary

Applied:

- No hardcoded production secrets in Compose.
- Production rejects wildcard `ALLOWED_HOSTS`.
- HTTPS/HSTS/proxy cookie settings ready for Coolify/Traefik.
- `X_FRAME_OPTIONS=DENY`, `SECURE_CONTENT_TYPE_NOSNIFF=True`, `Referrer-Policy=same-origin`.
- DRF anon/user/OTP throttling enabled.
- OTP cooldown, daily limit, max attempts, secure random production code.
- PostgreSQL connection health checks enabled.
- MinIO credentials loaded from env.
- Entrypoint runs migrations and collectstatic, not `makemigrations`.
- Upload memory limits configured.

Review before launch:

- Decide if MinIO bucket must be public. Compose currently creates public media bucket.
- Add real SMS provider implementation; console backend only logs OTP.
- Add backup policy for PostgreSQL and MinIO volumes.
- Pin Docker image tags for regulated production.
