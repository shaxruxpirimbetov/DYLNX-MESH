<div align="center">

# Mesh — DYLNX

**Smart QR stickers for your belongings. Anyone can reach the owner — nobody sees who the owner is.**

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/Django-REST%20Framework-092E20?logo=django&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)
![Cloudflare R2](https://img.shields.io/badge/Cloudflare-R2-F38020?logo=cloudflare&logoColor=white)

</div>

---

## Overview

Mesh is a QR-sticker service built by **DYLNX**. A sticker is attached to a car, wallet, phone, keys, a bag — anything worth getting back or worth being contacted about.

When someone scans the QR (a car blocking a driveway, a lost wallet, a found phone), they land on a web page, pick a reason or write a message, and the owner receives it instantly in **Telegram**. The conversation is fully anonymous: neither side sees the other's account or phone number, and the owner can reply, close the chat, or block the sender.

No app to install. No phone number printed on the windshield.

## Features

- **Anonymous two-way chat** via a Telegram bot. Messages are delivered with `copy_message`, so there is no "forwarded from" label and no identity leak.
- **Rich content relay:** text, photos, video, voice, documents, locations, stickers, video notes and contacts.
- **Activation flow with a printed card** (QR + secret code). A sticker is inert until the buyer activates it through the bot.
- **Three public landing pages:** active sticker, inactive/expired sticker, unknown UUID — each with RU / UZ language switch.
- **Admin panel** (single-file HTML SPA): create stickers, print cards, regenerate QR codes, view stats, browse messages, manage users.
- **Two-way sync without WebSockets:** a background poller delivers messages written outside the bot (for example by an admin from the panel) and sends expiry reminders.
- **Subscription-style validity:** each sticker has an expiry date; owners get a reminder before it runs out.
- **QR codes stored in Cloudflare R2** and served from a public URL; stickers are still created if the upload fails and can be regenerated later.
- **Safe by default:** JWT auth, throttling for anonymous traffic, owner's `telegram_id` is never rendered into public HTML, and message history is staff-only.

## How it works

```
                         ┌────────────────────────┐
   Guest scans QR ─────► │  /mesh/<uuid>/ (Django) │
                         └───────────┬────────────┘
                                     │ opens t.me/<bot>?start=<uuid>
                                     ▼
┌──────────┐  copy_message  ┌────────────────┐  REST + JWT  ┌──────────────────┐
│  Guest   │ ◄────────────► │  Telegram bot  │ ◄──────────► │  Django REST API │
└──────────┘                │   (aiogram 3)  │              │  + Admin panel   │
┌──────────┐  copy_message  │  SQLite state  │   poller     │  PostgreSQL / R2 │
│  Owner   │ ◄────────────► └────────────────┘ ◄─ 3 sec ──► └──────────────────┘
└──────────┘
```

1. **Provisioning.** An admin creates stickers in the panel and prints cards with the QR code and a secret activation code.
2. **Activation.** The buyer scans the QR and sees the *inactive* page with an **Activate** button. It opens the bot (`?start=a_<uuid>`), which asks for the code from the card and, optionally, a contact phone. The bot then calls `PATCH /api/mesh/activate/<uuid>/`.
3. **Contact.** A passer-by scans an active sticker and lands on `open_mesh.html`. After 5 seconds (or on button press) the page opens the bot (`?start=<uuid>`). The guest chooses a ready-made reason or writes their own message, and the bot relays it to the owner.
4. **Conversation.** The owner replies inside the bot. Both sides stay anonymous.
5. **History.** Every message is stored through `/api/message/`. The bot's poller checks the API every few seconds for messages that did not arrive via the bot and delivers them to Telegram.

## Repository layout

```
.
├── Mesh/                 Django project (settings, urls, wsgi/asgi)
├── apps/
│   ├── user/             Custom user model, roles, permissions, /api/user/
│   ├── mesh/             Sticker model, QR generation, activation, public page
│   └── message/          Message history (staff only)
├── bot/                  Telegram bot (aiogram 3) — see "Telegram bot"
│   ├── handlers/         activate, chat, common, meshes
│   ├── api.py            Async client for the backend (JWT, auto-refresh)
│   ├── poller.py         Message sync, stale-chat cleanup, expiry reminders
│   ├── relay.py          Anonymous message delivery core
│   ├── db.py             Local SQLite state (conversations, blocks, language)
│   └── texts.py          Localised strings (RU / UZ)
├── templates/
│   ├── index.html        Admin panel (served at /)
│   ├── open_mesh.html    Landing page of an active sticker
│   ├── unactive_qr.html  Landing page of an inactive / expired sticker
│   └── invalid_uuid.html Landing page for an unknown UUID (HTTP 404)
├── utils/
│   ├── QR.py             QR generation + upload to Cloudflare R2
│   └── drf.py            Pagination and throttle helpers
├── manage.py
└── requirements.txt
```

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`) — access 5 h, refresh 1 day |
| Database | PostgreSQL via `DATABASE_URL` (`dj-database-url`, `psycopg`) |
| File storage | Cloudflare R2 (S3-compatible, `django-storages`, `boto3`) |
| QR codes | `qrcode`, `Pillow` (`segno` for custom-styled QR) |
| Bot | aiogram 3, aiohttp, aiosqlite |
| Frontend | Plain HTML / CSS / JS, no build step |

## Getting started

### Prerequisites

- Python 3.12+ (required by current Django)
- A PostgreSQL database (or any database URL supported by `dj-database-url`)
- A Cloudflare R2 bucket with a public URL
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Backend

```bash
git clone https://github.com/shaxruxpirimbetov/DYLNX-MESH.git
cd DYLNX-MESH

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill it in (or create the file from the template below):

```env
# Django
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000          # required when DEBUG=False
DATABASE_URL=postgres://user:password@localhost:5432/mesh

# Public address of this backend (used inside QR codes), no trailing slash
BACKEND_HERE=http://127.0.0.1:8000

# Telegram
TELEGRAM_BOT_USERNAME=YourMeshBot                   # without @
MESH_BUY_URL=https://example.com/buy                # optional

# Cloudflare R2
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_ACCESS_KEY_ID=...
CLOUDFLARE_SECRET_ACCESS_KEY=...
CLOUDFLARE_R2_BUCKET=...
CLOUDFLARE_R2_PUBLIC_URL=https://pub-xxxx.r2.dev
```

Apply migrations, create an admin, and run:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the admin panel and sign in with the superuser account.

### 2. Telegram bot

The bot authenticates against the backend with a regular account that has `is_staff=True`. Create it in the admin panel (**Users → Add**, tick *Staff*) or with `createsuperuser`.

```bash
cd bot
pip install -r requirements.txt
```

Create `bot/.env`:

```env
BOT_TOKEN=123456:ABC...
API_URL=http://127.0.0.1:8000       # backend root, WITHOUT /api
API_USERNAME=bot
API_PASSWORD=...

# Optional
ADMIN_IDS=111111111,222222222       # Telegram IDs allowed to use /stats
BUY_URL=https://example.com/buy     # adds a "Buy" button
SUPPORT_USERNAME=your_support       # adds a "Support" button, without @
DB_PATH=mesh_bot.sqlite3
POLL_INTERVAL=3                     # seconds between API polls
CHAT_TTL_HOURS=24                   # idle chats are closed after this time
EXPIRY_REMIND_DAYS=3                # remind owners N days before expiry
```

```bash
python bot.py
```

On start the bot verifies the backend connection and prints a clear error if `API_URL`, credentials, `ALLOWED_HOSTS` or migrations are wrong. `opencv-python-headless` is optional and enables reading a QR from a photo during activation.

### Bot commands

| Command | Description |
|---|---|
| `/start` | Welcome / deep-link entry point (`<uuid>` to contact an owner, `a_<uuid>` to activate) |
| `/my` | Your stickers |
| `/chats` | Active conversations |
| `/activate` | Activate a new sticker |
| `/buy` | Where to buy a sticker |
| `/lang` | Switch language (RU / UZ) |
| `/help` | Help |
| `/stats` | Service statistics (only for IDs listed in `ADMIN_IDS`) |

## Tests

The suite covers sticker CRUD and filters, statistics, the activation flow (wrong code, takeover protection, no secret leakage), the public landing pages and the staff-only message API. Cloudflare R2 is mocked, so no external services are needed.

```bash
export SECRET_KEY=test DEBUG=True ALLOWED_HOSTS=testserver,localhost \
  DATABASE_URL="sqlite:///:memory:" BACKEND_HERE=http://testserver \
  TELEGRAM_BOT_USERNAME=TestBot CLOUDFLARE_ACCOUNT_ID=x CLOUDFLARE_ACCESS_KEY_ID=x \
  CLOUDFLARE_SECRET_ACCESS_KEY=x CLOUDFLARE_R2_BUCKET=x CLOUDFLARE_R2_PUBLIC_URL=https://cdn.example.com

python manage.py test
```

The same suite runs on every push through GitHub Actions (`.github/workflows/tests.yml`).

## API reference

All endpoints are under the backend root. Authenticate with `Authorization: Bearer <access_token>`. Lists are paginated (`?page=`, `?page_size=`, max 500).

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain access and refresh tokens |
| `POST` | `/api/refresh/` | Refresh the access token |

### Stickers — `/api/mesh/`

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` / `POST` | `/api/mesh/` | staff | List / create stickers (QR is generated and uploaded on create) |
| `GET` / `PUT` / `PATCH` / `DELETE` | `/api/mesh/<id>/` | staff | Retrieve, update, delete a sticker |
| `POST` | `/api/mesh/<id>/regenerate-qr/` | staff | Re-generate and re-upload the QR code |
| `GET` / `PATCH` | `/api/mesh/uuid/<uuid>/` | staff | Retrieve / update by UUID |
| `GET` | `/api/mesh/stats/` | staff | Totals: active, inactive, expired, expiring soon, owners, messages |
| `PATCH` | `/api/mesh/activate/<uuid>/` | authenticated | Activate a sticker with `password` and `telegram_id` |

**List filters:** `?search=` (UUID, phone, Telegram ID), `?status=active|inactive|expired`, `?telegram_id=`, `?until_lte=YYYY-MM-DD`, `?page_size=`.

**Activation responses:** `200` activated · `400` missing fields or wrong code · `409` already bound to another Telegram account.

### Messages — `/api/message/` (staff only)

| Method | Endpoint | Description |
|---|---|---|
| `GET` / `POST` | `/api/message/` | List / create messages |
| `GET` / `PUT` / `PATCH` / `DELETE` | `/api/message/<id>/` | Manage a message |

**Filters:** `?mesh=<id>`, `?search=`, `?after_id=<id>` (ascending order, used for polling).

### Users — `/api/user/`

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` / `POST` | `/api/user/` | staff | List / create users |
| `GET` | `/api/user/<id>/` | staff | Retrieve a user |
| `GET` | `/api/user/me/` | authenticated | Current user |

### Public pages

| Endpoint | Description |
|---|---|
| `/` | Admin panel |
| `/mesh/<uuid>/` | Sticker landing page: `open_mesh` (active) · `unactive_qr` (inactive or expired) · `invalid_uuid` (404) |

### Rate limits

Anonymous: **10 requests/minute**. Authenticated users: **100 requests/minute**. Staff accounts (including the bot) are exempt.

## Data model

**Mesh** — `uuid`, `user` (creator), `telegram_id`, `phone`, `is_active`, `until`, `password` (activation code), `qrcode`, `url`, timestamps.

**Message** — `mesh`, `message`, `telegram_id` (`0` = sent from the admin panel), timestamps.

**User** — Django `AbstractUser` with a `role` field.

## Security notes

- The owner's `telegram_id` is never included in public HTML.
- Message history and sticker management require staff privileges.
- Activation fails with `409` if the sticker is already bound to another Telegram account; transfer requires an explicit unbind by an admin.
- Always set `DEBUG=False`, a strong `SECRET_KEY`, and a restrictive `CORS_ALLOWED_ORIGINS` in production, and serve the backend over HTTPS.
- Never commit `.env` files or the bot's SQLite database.

## Deployment

- **Backend:** any WSGI/ASGI host (`Mesh.wsgi` / `Mesh.asgi`) with a PostgreSQL database. Run `python manage.py migrate` on each release.
- **Bot:** a single long-running process (`python bot.py`) with a persistent volume for its SQLite file. It uses long polling, so no public webhook endpoint is required.
- `BACKEND_HERE` must be the public HTTPS address of the backend — it is encoded in every QR code.

## About

Mesh is developed by the **DYLNX** team in Nukus, Karakalpakstan, Uzbekistan.

Questions or ideas? Open an issue in this repository.