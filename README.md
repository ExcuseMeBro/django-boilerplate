# 🚀 Django Boilerplate

Production uchun tayyor, xavfsiz va kengaytiriladigan Django REST API starter. Telefon + OTP autentifikatsiya, JWT, WebSocket-ready Channels, PostgreSQL, Redis, MinIO va zamonaviy Unfold admin paneli bir joyda.

## ✨ Imkoniyatlar

- 🐍 **Django 6.1** + Django REST Framework 3.18
- 🔐 Telefon raqami + OTP, JWT rotation va token blacklist
- 🛡️ Secure-by-default production sozlamalari, CORS, CSRF va throttling
- 📘 OpenAPI schema, Swagger UI va ReDoc
- 🔎 API filter, search va ordering uchun tayyor infratuzilma
- ⚡ Redis cache va Django Channels
- 💬 Conversation va HTTP messaging API bazasi
- 🐘 PostgreSQL va connection health check
- 🪣 Private MinIO/S3 media, vaqtinchalik signed URL'lar
- 🎨 Django Unfold admin va dashboard
- 🔔 Notification, device token va ixtiyoriy Firebase push
- 📈 Ixtiyoriy Sentry error/performance monitoring
- 🌍 O‘zbek, ingliz va rus tillari
- 🐳 Docker Compose health check'lari bilan
- 📦 uv orqali yagona dependency workflow va Git’da saqlanadigan `uv.lock`
- 🧪 Pytest, Coverage va Ruff uchun tayyor konfiguratsiya

## 🧱 Texnologiyalar

| Yo‘nalish | Texnologiya |
|---|---|
| Backend | Django, DRF, Daphne |
| Auth | SimpleJWT, OTP |
| Database | PostgreSQL |
| Cache / WebSocket-ready | Redis, Channels |
| Storage | MinIO / Amazon S3 |
| API docs | drf-spectacular |
| Admin | Django Unfold |
| Monitoring | Sentry SDK |
| Dependencies | uv, pyproject.toml, uv.lock |
| Quality | Pytest, Coverage, Ruff |

## ⚡ Tez boshlash — Docker

### 1. Repozitoriyni tayyorlang

```bash
git clone https://github.com/ExcuseMeBro/django-boilerplate.git
cd django-boilerplate
cp .env.example .env
```

### 2. Majburiy secretlarni kiriting

`.env` ichida kamida quyidagilarni almashtiring:

```env
SECRET_KEY=uzun-tasodifiy-secret
DB_PASSWORD=mustahkam-database-parol
MINIO_ROOT_USER=minio-access-key
MINIO_ROOT_PASSWORD=mustahkam-minio-secret
# Faqat lokal Swagger/ReDoc uchun yoqing:
API_DOCS_ENABLED=True
```

Secret yaratish:

```bash
docker run --rm python:3.14-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 3. Servislarni ishga tushiring

```bash
docker compose up --build
```

### 4. Superuser yarating

```bash
docker compose exec backend python manage.py createsuperuser
```

## 🌐 Lokal manzillar

| Xizmat | URL |
|---|---|
| Landing page | http://localhost:8000 |
| Health check | http://localhost:8000/api/health/ |
| Admin panel | http://localhost:8000/admin/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| OpenAPI schema | http://localhost:8000/api/schema/ |
| MinIO API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 |

> 📌 API dokumentatsiyasi `API_DOCS_ENABLED=True` bo‘lganda ochiladi. Production'da uni `False` qoldiring yoki autentifikatsiya ortida taqdim eting.

## 🛠️ Lokal ishlash — uv

[uv o‘rnating](https://docs.astral.sh/uv/getting-started/installation/). Docker build va CI’da uv **0.12.5** ishlatiladi. PostgreSQL va Redis kerak; MinIO ixtiyoriy. Python **3.14** `.python-version` orqali tanlanadi; uv kerak bo‘lsa uni yuklab oladi.

```bash
uv sync --locked
cp .env.example .env
```

`uv sync --locked` `.venv` yaratadi va lockfile’dagi runtime hamda dev paketlarini o‘rnatadi. Virtual environment’ni qo‘lda aktivlashtirish yoki `pip install` ishlatish kerak emas. `--locked` dependency ta’rifi bilan lockfile mos kelmasa xato beradi.

Docker'dan tashqarida ishlaganda `.env` ichidagi hostlarni migratsiyadan oldin moslang:

```env
DB_HOST=127.0.0.1
REDIS_URL=redis://127.0.0.1:6379/0
CACHE_URL=redis://127.0.0.1:6379/1
USE_MINIO=False
```

Keyin migration va serverni ishga tushiring:

```bash
uv run --locked python manage.py migrate
uv run --locked python manage.py runserver
```

Yoki `.env` tayyor bo‘lgach `./start_dev.sh` ishlating: u locked sync, migration va `0.0.0.0:8000` da dev serverni ketma-ket bajaradi.

### 📦 Dependency boshqaruvi

Paketlar uchun yagona manba — `pyproject.toml`; yechilgan versiyalar va artifact hash’lari — `uv.lock`. Ikkalasini ham Git’ga kiriting.

```bash
uv add django-filter             # Runtime paket qo‘shish
uv add --dev pytest              # Dev paket qo‘shish
uv remove paket-nomi             # Paketni olib tashlash
uv lock --upgrade-package Django # Bitta paketni ruxsat etilgan diapazonda yangilash
uv sync --locked                # Yangilangan lockfile’ni o‘rnatish
```

Yangilashdan keyin test va lintni qayta ishlating. Oddiy install/deploy vaqtida `uv lock --upgrade` ishlatmang.

Docker build `uv sync --locked --no-dev` bilan faqat runtime paketlarini o‘rnatadi. Container startida paket yuklanmaydi: `entrypoint.sh` tayyor `.venv` ichidagi Python va Daphne’dan foydalanadi. Docker foydalanuvchisiga host’da uv o‘rnatish shart emas.

`requirements.txt` va `requirements-dev.txt` parallel yuritilmaydi. Faqat tashqi platforma talab qilsa lockfile’dan eksport qiling; eksport faylini qo‘lda tahrirlamang:

```bash
uv export --locked --no-dev --format requirements-txt --output-file /tmp/requirements.txt
```

Dependency yangilanishini ortga qaytarishda oldingi `pyproject.toml` va `uv.lock`ni birga tiklang, `uv sync --locked` bajaring va Docker image’ni qayta build qiling. uv migratsiyasidan oldingi deploy’ga qaytish uchun oldingi image’dan foydalaning.

## 🔌 API endpointlar

Asosiy prefix: `/api/v1/`

### 🔐 Auth va profil

| Method | Endpoint | Vazifa |
|---|---|---|
| `POST` | `/auth/otp/send/` | OTP yuborish |
| `POST` | `/auth/otp/verify/` | OTP tekshirish va JWT olish |
| `POST` | `/auth/token/refresh/` | Access tokenni yangilash |
| `POST` | `/auth/logout/` | Refresh tokenni bekor qilish |
| `GET` / `PATCH` | `/auth/me/` | Joriy foydalanuvchi profili |

### 🔔 Ilova

| Method | Endpoint | Vazifa |
|---|---|---|
| `POST` | `/devices/token/` | Push device tokenini saqlash |
| `GET` | `/notifications/` | Bildirishnomalarni olish |
| `POST` | `/notifications/read/` | Barchasini o‘qilgan qilish |
| `POST` | `/notifications/{id}/read/` | Bittasini o‘qilgan qilish |
| `GET` | `/config/` | Public app konfiguratsiyasi |

### 💬 Messaging

| Method | Endpoint | Vazifa |
|---|---|---|
| `GET` / `POST` | `/conversations/` | Suhbatlar ro‘yxati va yangi suhbat |
| `GET` / `PATCH` / `DELETE` | `/conversations/{id}/` | Suhbatni boshqarish |
| `POST` | `/conversations/{id}/participants/` | Ishtirokchi qo‘shish |
| `DELETE` | `/conversations/{id}/participants/{user_id}/` | Ishtirokchini olib tashlash |
| `GET` / `POST` | `/messages/` | Xabarlar ro‘yxati va yangi xabar |
| `GET` / `PATCH` / `DELETE` | `/messages/{id}/` | Xabarni boshqarish |

## ⚙️ Muhim environment sozlamalari

| O‘zgaruvchi | Vazifa | Default |
|---|---|---|
| `DEBUG` | Debug rejimi | `False` |
| `ALLOWED_HOSTS` | Ruxsat etilgan hostlar | local hostlar |
| `DB_*` | PostgreSQL ulanishi | — |
| `REDIS_URL` | Channels Redis bazasi | bo‘sh |
| `CACHE_URL` | Django cache Redis bazasi | bo‘sh, LocMem fallback |
| `API_DOCS_ENABLED` | Swagger/ReDoc/schema | `DEBUG` qiymati |
| `OTP_STATIC_CODE` | Faqat local OTP kodi | bo‘sh |
| `USE_MINIO` | S3-compatible storage | `False` |
| `MINIO_PUBLIC_READ` | Public media bucket | `False` |
| `SENTRY_DSN` | Sentry integratsiyasi | bo‘sh/o‘chiq |
| `SENTRY_TRACES_SAMPLE_RATE` | Performance sample ulushi | `0.0` |

Barcha sozlamalar va izohlar: [`.env.example`](.env.example).

## 🪣 MinIO va media fayllar

Media bucket default holatda **private**. Fayllar expiring signed URL orqali beriladi.

Docker'da brauzer `minio:9000` manzilini ochishi uchun lokal hosts fayliga qo‘shing:

```text
127.0.0.1 minio
```

> ⚠️ `MINIO_PUBLIC_READ=True` faqat ommaviy media uchun ishlatilsin. Shaxsiy avatarlar, hujjatlar yoki tibbiy fayllar uchun bucket private qolishi kerak.

## 🌍 Tarjimalar

Qo‘llab-quvvatlanadigan tillar:

- 🇺🇿 `uz` — default
- 🇬🇧 `en`
- 🇷🇺 `ru`

API tilini `Accept-Language` orqali tanlang:

```bash
curl -H 'Accept-Language: ru' http://localhost:8000/api/health/
curl -H 'Accept-Language: en' http://localhost:8000/api/v1/config/
```

Tarjima matnlari o‘zgargandan keyin:

```bash
uv run --locked python manage.py makemessages -l uz -l en -l ru
uv run --locked python manage.py compilemessages
```

## 🧪 Test va code quality

Development paketlarini o‘rnating:

```bash
uv sync --locked
```

Tekshiruvlar:

```bash
uv run --locked pytest
uv run --locked coverage run -m pytest
uv run --locked coverage report
uv run --locked ruff check .
uv run --locked python manage.py check
uv run --locked python manage.py check --deploy
```

GitHub Actions (`.github/workflows/ci.yml`) Python 3.14 / uv 0.12.5 bilan locked sync, Ruff, launcher regression testlari va Django system check’ni bajaradi. Launcher testlari tashqi servislarni ishga tushirmaydi; to‘liq API/database testlari hali qo‘shilmagan.

## 📁 Tuzilma

```text
.
├── config/              # Settings, URL, ASGI va WSGI
├── core/                # User, OTP, notification va app config
├── messaging/           # Conversation va message API
├── templates/           # Landing page
├── docker-compose.yaml  # PostgreSQL, Redis, MinIO va backend
├── .python-version      # Python 3.14
├── .github/workflows/ci.yml # Locked install, lint va smoke checks
├── tests/               # uv launcher regression testlari
├── uv.lock              # Aniq dependency versiyalari va hash’lar
└── pyproject.toml        # Runtime/dev paketlar, Pytest, Coverage va Ruff
```

## 🚢 Production checklist

- [ ] `DEBUG=False`
- [ ] Kuchli `SECRET_KEY`, DB va MinIO secretlari o‘rnatilgan
- [ ] `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS` aniq ko‘rsatilgan
- [ ] `ENABLE_HTTPS_REDIRECT=True` va proxy HTTPS headerlari tekshirilgan
- [ ] `API_DOCS_ENABLED=False` yoki docs autentifikatsiya bilan himoyalangan
- [ ] `OTP_STATIC_CODE` bo‘sh va real SMS provider ulangan
- [ ] PostgreSQL hamda MinIO backup va restore jarayoni sinovdan o‘tgan
- [ ] Sentry/monitoring va alertlar sozlangan
- [ ] Docker image taglari production uchun pin qilingan
- [ ] `pyproject.toml` va `uv.lock` Git’da, build `uv sync --locked --no-dev` orqali
- [ ] `uv run --locked python manage.py check --deploy` xatosiz tugagan
- [ ] Test, lint va migration tekshiruvlari CI'dan o‘tgan

## 🔒 Xavfsizlik eslatmalari

- Production wildcard `ALLOWED_HOSTS` bilan ishga tushmaydi.
- Secure/HttpOnly cookie, HSTS, HTTPS redirect va proxy sozlamalari mavjud.
- OTP cooldown, kunlik limit, urinish limiti va secure random kod ishlatiladi.
- JWT refresh tokenlar rotate qilinadi va eski token blacklist'ga tushadi.
- DRF default holatda autentifikatsiyani talab qiladi; public view'lar alohida `AllowAny` beradi.
- Sentry'da default user PII va request body yig‘ish o‘chirilgan (`send_default_pii=False`, `max_request_body_size='never'`).

## 🤝 Template sifatida foydalanish

GitHub'da **Use this template** tugmasini bosing, yangi repository yarating va loyiha nomlariga mos ravishda quyidagilarni almashtiring:

- `unfold_boilerplate_db`, `unfold_user`
- `unfold-boilerplate` MinIO bucket nomi
- Admin panel title/header
- `core.AppConfig` default qiymatlari
- SMS va push provider konfiguratsiyasi

---

<p align="center">Django loyihalarini xavfsiz va tez boshlash uchun yaratilgan. 🐍⚡</p>
