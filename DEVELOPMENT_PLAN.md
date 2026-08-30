# CodeCup.tech — Development Plan

Backend: **Django 5.2 (LTS) + Django REST Framework + PostgreSQL**
Frontend: **Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui** in `/frontend`, **Russian only**
Local DB: **Postgres in Docker**. Production: real Postgres on the server.

Derived from the Claude Design project *CodeCup MVP Design System* (9 screens + `01_PRODUCT.md`, `02_FRONTEND.md`).

---

## 0. Decisions locked in

| Question | Decision |
|---|---|
| Scope | Full Django/DRF backend **and** full Next.js port of all 9 screens |
| Language | **Russian only.** Every UI string and all contest content is `ru`. No language switcher, no per-language fields. The `tg`/`en` dictionaries in the prototypes are dropped for now. |
| Telegram transport | **Webhook** (`/api/telegram/webhook/<secret>/`), ngrok/cloudflared tunnel for local dev |
| Session transport | **httpOnly cookie JWT** (SimpleJWT access + refresh, `Secure`, `SameSite=Lax`) |

Detected toolchain: Python 3.12.0, Node 24.18.1, npm 11.16.0, Docker 29.6.2 + Compose v5.3.1. No `uv`/`pnpm` → we use `venv`+`pip` and `npm`.

---

## 1. What the design actually requires

Reading the screens gives us the real contract. Highlights that shape the schema:

- **Login** is a three-state polling flow: `default` → `waiting` ("Waiting for confirmation…", cancel button) → `error` ("Login link expired"). So the backend needs a **short-lived nonce + status endpoint the frontend polls**, not a redirect callback.
- **Contest Details** has 5 states: `active`, `submitted`, `ended`, `loading`, `error`. CTA changes per state: *Submit your solution* / *Edit your submission* / *Submissions closed*. A live countdown to `deadline`.
- **Create Contest** edits `requirements` as an **ordered, add/remove list of strings**, plus title, description, prize (USD), `datetime-local` deadline, and has **Save as draft** vs **Publish**.
- **Submit Solution**: `github_url` (validated `github.com`), `live_url` (required), `video_url` (optional), `description` (**500 char counter**). Save draft vs Submit. Subheading states *"Only the last submission before deadline counts"* → **one submission per user per contest**, editable until deadline.
- **Review Submission** (admin): `score` 0–100, `reviewer_notes` marked *"Internal notes (not visible to participant)"*, `Mark as winner` checkbox, and **prev/next navigation across the review queue** ("3 / 36").
- **Admin Dashboard** tiles: Total users, Active contests, Submissions, Pending review. Contest rows show participants + prize + status + deadline.
- **Profile**: username, "Joined via Telegram · <month year>", submission count, **wins count**, and a submission history list.
- **Status vocabulary is fixed by the design**: `Draft / Submitted / Reviewed / Winner` for submissions; `Live / Ended` (+ `Draft`) for contests.

---

## 2. Data model

### `apps/users`

**`User(AbstractUser)`** — password auth disabled (`set_unusable_password()`); Telegram is the only credential.

| field | type | notes |
|---|---|---|
| `telegram_id` | `BigIntegerField` unique, indexed | the real identity |
| `telegram_username` | `CharField(64)` null | may be absent on Telegram |
| `username` | inherited, unique | seeded from `telegram_username`, else `user_<telegram_id>` |
| `first_name` / `last_name` | inherited | from Telegram profile |
| `photo_url` | `URLField` blank | |
| `language_code` | `CharField(5)` default `ru` | recorded from Telegram; unused while we ship ru-only |
| `is_staff` | inherited | **this is the Admin role** — no separate role column |
| `notify_opt_in` | `BooleanField` default `True` | powers the landing "Notify me" button |
| `created_at` | `DateTimeField(auto_now_add)` | drives "Joined via Telegram · Jun 2026" |

**`TelegramAuthToken`** — one login attempt.

| field | notes |
|---|---|
| `nonce` | 32-char urlsafe, unique, indexed. Travels through Telegram in the deep link. |
| `client_secret_hash` | SHA-256 of a secret returned **only to the browser** at start |
| `status` | `pending / confirmed / consumed / cancelled / expired` |
| `user` | FK null, set on confirmation |
| `created_at`, `expires_at` | TTL **5 minutes** |
| `confirmed_at`, `consumed_at` | |
| `ip`, `user_agent` | audit |

> **Why `client_secret`:** the nonce is visible inside Telegram, so it alone must not be enough to mint a session. Exchange requires `nonce` **+** the secret only the originating browser holds. Single-use, and the token dies on first exchange.

### `apps/contests`

**`Contest`**

| field | type | notes |
|---|---|---|
| `number` | `PositiveIntegerField` unique, auto-assigned | renders as `#01` |
| `slug` | `SlugField` unique | public URL key |
| `title` | `CharField(200)` | |
| `description` | `TextField` | |
| `requirements` | `JSONField(default=list)` | ordered `list[str]`, validated. Matches the add/remove UI exactly; requirements are never referenced individually, so a child table would be overhead. |
| `prize_pool` | `DecimalField(12,2)` | |
| `currency` | `CharField(3)` default `USD` | |
| `starts_at` | `DateTimeField` null | |
| `deadline` | `DateTimeField` | |
| `status` | `draft / published / archived` | what the admin controls |
| `is_featured` | `BooleanField` | the landing hero contest |
| `created_by` | FK User | |
| `created_at`, `updated_at` | | |

**Derived `state`** (never stored, so a contest can't go stale): `draft` if unpublished, `ended` if `now >= deadline`, else `live`. This is what the API returns and what the UI badges render.

**`NotifySubscription`** — `user` FK, `created_at`. Backs the "Notify me" CTA on the empty-state landing.

### `apps/submissions`

**`Submission`** — `unique_together (contest, user)`.

| field | notes |
|---|---|
| `github_url` | validated against `^https?://(www\.)?github\.com/` — same rule the design's client-side validator uses |
| `live_url` | required at submit time |
| `video_url` | optional |
| `description` | `TextField`, **max 500** |
| `status` | `draft / submitted / reviewed` |
| `is_winner` | bool — source of truth for the Winner badge |
| `score` | `PositiveSmallIntegerField` null, 0–100 |
| `reviewer_notes` | `TextField` blank — **admin-only, never serialized to participants** |
| `reviewed_by`, `reviewed_at` | | 
| `submitted_at`, `created_at`, `updated_at` | |

`display_status` (serializer-only) = `winner` if `is_winner` else `status` → exactly the 4 badges the design draws.

**Server-enforced rules** (the client-side checks in the prototypes are advisory only):
1. No create/edit/submit after `deadline` → `409 CONTEST_CLOSED`.
2. No submission against a `draft` or `archived` contest.
3. One submission per user per contest; `draft → submitted` is the only participant transition.
4. `score`, `reviewer_notes`, `reviewed_by` are stripped from every non-admin response.
5. `participants_count` counts submissions with `status != draft`.

---

## 3. API surface

Auth (`/api/auth/`)
```
POST /telegram/start/      → { nonce, client_secret, deep_link, expires_at }
GET  /telegram/status/     → { status }                      # frontend polls every 2s
POST /telegram/exchange/   → sets httpOnly cookies, returns user
POST /refresh/             → rotates access cookie
POST /logout/              → clears cookies, blacklists refresh
GET  /me/                  → current user
```

Public
```
GET /contests/                    ?state=live|ended  (paginated)
GET /contests/featured/           landing hero contest
GET /contests/<slug>/             includes my_submission when authenticated
GET /stats/                       hero tiles: prize pool, participants, time left
GET /users/<username>/            public profile + submission history
```

Participant
```
GET   /contests/<slug>/submission/          my submission
PUT   /contests/<slug>/submission/          upsert draft  (Save draft)
POST  /contests/<slug>/submission/submit/   draft → submitted
GET   /me/submissions/                      profile list
POST  /me/notify/                           Notify me
```

Admin (`IsAdminUser`)
```
GET  POST        /admin/contests/
GET  PATCH  DEL  /admin/contests/<id>/
POST             /admin/contests/<id>/publish/
GET              /admin/submissions/?contest=&status=   review queue, ordered & indexed
GET  PATCH       /admin/submissions/<id>/               score, notes, is_winner
                                                        → response carries prev_id/next_id/position/total
                                                          for the "3 / 36" navigator
GET              /admin/stats/                          4 dashboard tiles
GET              /admin/users/
```

Telegram
```
POST /telegram/webhook/<secret>/   secret path + X-Telegram-Bot-Api-Secret-Token check
```

### Login sequence
```
Browser                    Backend                     Telegram
  │ POST auth/telegram/start/ │
  │◀── nonce + client_secret ─│
  │ open t.me/<bot>?start=<nonce> ───────────────────────▶│
  │                           │◀── webhook /start <nonce> ─│
  │                           │─ sendMessage "Confirm login?" ▶│
  │ poll status/ (2s)         │                            │
  │                           │◀── callback_query confirm ─│
  │                           │  get_or_create user, mark confirmed
  │◀── {status:"confirmed"} ──│
  │ POST exchange/ {nonce, client_secret}                 │
  │◀── Set-Cookie access+refresh ─│
```
Expiry after 5 min drives the design's *"Login link expired"* error state. `start/` is DRF-throttled to stop nonce flooding.

---

## 4. Repository layout

```
codecup/                          ← backend at repo root, as requested
├── manage.py
├── requirements/{base,dev,prod}.txt
├── .env.example                  ← committed; .env is gitignored
├── docker-compose.yml            ← Postgres 17 (local only)
├── Makefile                      ← up/down/migrate/run/test/lint/seed
├── config/
│   ├── settings/{base,local,production}.py
│   └── urls.py  wsgi.py  asgi.py
├── apps/
│   ├── common/                   pagination, error envelope, mixins
│   ├── users/                    User, TelegramAuthToken, JWT-cookie auth
│   ├── contests/
│   ├── submissions/
│   └── telegrambot/              webhook view, Bot API client, set_webhook cmd
├── deploy/                       Dockerfile, gunicorn, nginx, runbook
└── frontend/                     Next.js 15 app
    ├── src/app/                  (public) / (participant) / (admin) route groups
    ├── src/components/ui/        shadcn
    ├── src/lib/api/              typed client, generated from OpenAPI
    └── src/messages/ru.ts        strings lifted verbatim from the prototypes' `ru` dictionaries
```

Libraries: `djangorestframework`, `djangorestframework-simplejwt`, `psycopg[binary]`, `django-environ`, `django-cors-headers`, `drf-spectacular`, `httpx`, `gunicorn`, `whitenoise`; dev: `pytest-django`, `factory-boy`, `ruff`.

> Telegram is called through a thin `httpx` client rather than `python-telegram-bot` — we only need `sendMessage`, `answerCallbackQuery`, `setWebhook`, and PTB's async runtime adds nothing to a sync webhook view.

**No Celery/Redis in the MVP.** Nothing here needs a queue: contest state is derived at read time, and the one broadcast job ("contest opened") runs as a management command from cron. Adding a broker before launch is cost without benefit.

---

## 5. Build steps

I stop after each step for your review.

| # | Step | Deliverable / how you verify it |
|---|---|---|
| **1** | **Skeleton & infra** | `docker-compose.yml` (Postgres 17), settings split, `.env.example`, Makefile, ruff, pytest. `GET /api/health/` → 200. Verify: `make up && make migrate && make run`. |
| **2** | **Users + Telegram auth** | Custom `User`, `TelegramAuthToken`, the 6 auth endpoints, cookie-JWT auth class, webhook view + Bot API client, `set_webhook` command, throttling. Tests simulate real Telegram webhook payloads — **no bot token needed to pass CI**, but a token + tunnel lets you log in for real. |
| **3** | **Contests** | Model + migrations, admin CRUD, public list/detail/featured, `/api/stats/`, derived `state`, Django admin, `seed_demo` command reproducing the design's sample data. Tests. |
| **4** | **Submissions** | Model, upsert-draft + submit, all deadline/ownership rules, `/me/submissions/`, admin review endpoints with prev/next navigation, winner marking. Tests for every rule in §2. |
| **5** | **Admin dashboard + API contract** | `/admin/stats/`, `/admin/users/`, drf-spectacular OpenAPI at `/api/schema/`, TypeScript types generated into `frontend/src/lib/api/types.ts`. Backend is now complete and browsable. |
| **6** | **Frontend foundation** | Next.js 15 + TS + Tailwind + shadcn in `/frontend`. Design tokens lifted from the prototypes (`#09090b`, `#22c55e`, `#3b82f6`, Manrope + JetBrains Mono), `src/messages/ru.ts` holding the prototypes' Russian strings verbatim, typed API client with cookie forwarding for SSR, **Navbar** (guest/participant/admin variants). |
| **7** | **Public screens** | Landing (default / no-contest / loading), Contest Details (active / submitted / ended / loading / error, live countdown), Login (default / waiting / expired, 2s polling). End-to-end Telegram login working. |
| **8** | **Participant screens** | Submit Solution (draft, validation, 500-char counter, success state), User Profile (list / empty / loading). |
| **9** | **Admin screens** | Admin Dashboard, Create + Edit Contest (live preview pane), Review Submission (score, notes, winner, prev/next). |
| **10** | **Production** | `deploy/Dockerfile`, `docker-compose.prod.yml` (app + nginx, connecting to the **server's own Postgres** — no DB container in prod), gunicorn, static/media, HTTPS + webhook registration, DB backup script, and a deployment runbook. |

---

## 6. Git workflow

Remote: `https://github.com/amirymax/codecup.git` (currently empty).

Per step:

1. Branch off `main` — `step-N-<slug>` (e.g. `step-1-skeleton`).
2. Implement the step, commit on that branch, push it.
3. **Stop for your review.**
4. Once you approve — and before the next step starts — merge the branch into `main` and push `main`.
5. The next step branches off the updated `main`.

So `main` only ever contains reviewed work, and every step is one reviewable branch plus one merge.

---

## 7. What I need from you, and when

- **Before step 2 (Telegram auth):** bot token from @BotFather and the bot username (the design references `@CodeCupBot`). Send the token privately — I'll read it from your `.env`, not from chat. Also install a tunnel (`brew install cloudflared` or ngrok) so Telegram can reach localhost.
- **Before step 10 (production):** target domain, server SSH/OS details, and whether TLS is Let's Encrypt or already terminated upstream.

Neither blocks anything earlier — steps 1 and 3–9 run without a bot token.

## 8. Deliberately out of MVP scope

Per `01_PRODUCT.md`: leaderboards, LeetCode integration, teams, chat, achievements, payments. Also excluded by me: Celery/Redis, email, file uploads (all submissions are URLs), and **any language other than Russian** — the Tajik and English dictionaries stay in the design files, unused, until we choose to add a switcher back.
