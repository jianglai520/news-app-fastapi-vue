# News App · FastAPI + Vue 3

**English** · [简体中文](README.zh-CN.md)

A full-stack, mobile-first news reader: an asynchronous **FastAPI** REST API on top of **MySQL** with a **Redis** read-cache, paired with a **Vue 3** single-page frontend built with **Vite** and **Vant**.

The project was built as a learning exercise, but it follows a production-shaped layering: routers → schemas → crud → models, with a shared response envelope, global exception handlers, password hashing, opaque-token authentication, and cache-aside reads.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Database](#1-database)
  - [2. Backend](#2-backend)
  - [3. Frontend](#3-frontend)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Response Format](#response-format)
- [Authentication](#authentication)
- [Caching](#caching)
- [Database Schema](#database-schema)
- [Frontend Routes](#frontend-routes)
- [Known Limitations](#known-limitations)
- [Further Documentation](#further-documentation)

---

## Features

**Backend**

- Async end-to-end: `SQLAlchemy 2.0` async engine + `aiomysql`, connection pooling with `pool_pre_ping` / `pool_recycle`
- Layered design — `routers/` (HTTP) → `schemas/` (validation & serialization) → `crud/` (data access) → `models/` (ORM)
- Paginated news feed filtered by category, with `total` and `hasMore`
- News detail with atomic view-count increment and "related news" suggestions
- User registration / login with `bcrypt` password hashing
- Opaque UUID token authentication (7-day expiry, one active token per user)
- Profile update and password change
- Favourites and browsing history (add / list / delete / clear)
- Redis cache-aside for categories and news lists; Redis failures degrade gracefully to the database
- Unified `{ code, message, data }` envelope for every response
- Global exception handlers for `HTTPException`, `IntegrityError`, `SQLAlchemyError`, and unexpected errors

**Frontend**

- Vue 3 `<script setup>` SPA with lazy-loaded routes
- Pinia stores for user, news, favourites, history, theme, and language, persisted to `localStorage`
- Vant 4 mobile UI components
- Chinese / English i18n via `vue-i18n`
- Light / dark theme switching
- AI chat page wired to a DashScope-compatible endpoint (see [Known Limitations](#known-limitations))
- Dev-server proxy so the browser only ever talks to the same origin

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.14 |
| Web framework | FastAPI | 0.125.0 |
| ASGI server | Uvicorn | 0.38.0 |
| ORM | SQLAlchemy (async) | 2.0.45 |
| DB driver | aiomysql / PyMySQL | 0.3.2 / 1.1.2 |
| Database | MySQL | 8.0 |
| Cache | Redis (redis-py asyncio) | ≥ 5.0 |
| Validation | Pydantic | 2.12.5 |
| Password hashing | passlib + bcrypt | 1.7.4 / 3.2.2 |
| Frontend framework | Vue | 3.5 |
| Build tool | Vite | 7.1 |
| State management | Pinia (+ persistedstate) | 3.0 / 4.5 |
| Router | Vue Router | 4.5 |
| UI library | Vant | 4.9 |
| i18n | vue-i18n | 9.8 |
| HTTP client | axios | 1.12 |

---

## Architecture

```
┌──────────────────────────┐        ┌───────────────────────────┐
│  Vue 3 SPA (Vite :5173)  │        │   FastAPI (Uvicorn :8000) │
│                          │  /api  │                           │
│  views ← Pinia stores    │ ─────► │  routers → schemas        │
│         ← axios          │ proxy  │         → crud → models   │
└──────────────────────────┘        └─────────┬─────────┬───────┘
                                              │         │
                                     async SQL │         │ cache-aside
                                              ▼         ▼
                                    ┌──────────────┐ ┌─────────┐
                                    │ MySQL 8      │ │ Redis   │
                                    │ news_app     │ │ db 0    │
                                    └──────────────┘ └─────────┘
```

Request flow for a cached endpoint (e.g. `GET /api/news/categories`):

1. Router injects an `AsyncSession` via the `get_db` dependency.
2. `crud/news_cache.py` asks Redis for `news:categories`.
3. On a cache hit the ORM is skipped entirely; on a miss the query runs and the JSON result is written back with a TTL.
4. The router wraps the payload in the standard envelope and returns it.

---

## Repository Layout

```
news-app-fastapi-vue/
├── .gitignore
├── README.md
│
├── news_app_backend/
│   ├── main.py                  # app factory, lifespan, CORS, router registration
│   ├── requirements.txt
│   ├── database.sql             # schema + seed data (8 tables, 403 demo articles)
│   ├── .env                     # local secrets — NOT committed
│   ├── config/
│   │   ├── db_config.py         # async engine, session factory, get_db / close_db
│   │   └── cache_config.py      # Redis client + get/set helpers
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── news.py              # Category, News
│   │   ├── users.py             # User, UserToken
│   │   ├── favorite.py          # Favorite
│   │   └── history.py           # History
│   ├── schemas/                 # Pydantic request/response models
│   ├── crud/                    # data-access functions
│   │   ├── news.py              # detail, view increment, related news
│   │   ├── news_cache.py        # category / list queries with Redis cache-aside
│   │   ├── users.py             # user + token operations
│   │   ├── favorite.py
│   │   └── history.py
│   ├── routers/                 # HTTP layer, one router per resource
│   ├── cache/
│   │   └── news_cache.py        # cache keys and TTLs for news data
│   ├── utils/
│   │   ├── auth.py              # get_current_user dependency
│   │   ├── security.py          # bcrypt hashing / verification
│   │   ├── response.py          # success envelope helper
│   │   ├── exception.py         # handler implementations
│   │   └── exception_handlers.py
│   └── docs/                    # Chinese design documents
│       ├── API接口规范文档.md
│       └── 项目后端设计说明文档.md
│
└── news_app_frontend/
    ├── package.json
    ├── vite.config.js           # dev server + /api → :8000 proxy
    ├── index.html
    └── src/
        ├── main.js              # app bootstrap, Vant registration, theme init
        ├── App.vue
        ├── config/api.js        # API base URL + AI chat settings
        ├── router/index.js      # 12 routes, lazy loaded
        ├── store/               # Pinia stores (user, theme, language, modules/)
        ├── views/               # page components
        ├── components/          # NewsItem, TabBar, …
        ├── i18n/                # zh-CN / en-US message catalogues
        └── style.css
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python **3.14+** | The project is developed and pinned against 3.14 |
| Node.js **20+** | Vite 7 requires Node 20.19+ or 22.12+ |
| MySQL **8.0** | Listens on `127.0.0.1:3306` |
| Redis **5+** | Listens on `127.0.0.1:6379`; optional in the sense that failures fall back to MySQL, but recommended |

> **Important:** the backend must be started **from inside `news_app_backend/`**. All internal imports (`from config…`, `from crud…`, `from models…`) are resolved relative to that directory, so running Uvicorn from the repository root will fail with `ModuleNotFoundError`.

---

## Getting Started

### 1. Database

The SQL script is self-contained: it creates the `news_app` database, all eight tables, and seeds 8 categories plus 403 demo articles.

```powershell
cd news_app_backend

# Windows PowerShell — `cmd /c` is required because PowerShell treats `<` specially.
# --default-character-set=utf8mb4 is required or Chinese text is corrupted.
cmd /c "mysql --default-character-set=utf8mb4 -u root -p < database.sql"
```

To re-import from scratch (the script only uses `CREATE TABLE IF NOT EXISTS`, so plain inserts will collide on the unique category index):

```powershell
cmd /c 'mysql -u root -p -e "DROP DATABASE IF EXISTS news_app;"'
cmd /c "mysql --default-character-set=utf8mb4 -u root -p < database.sql"
```

Verify (reading with `gbk` makes the output readable in a CP936 console):

```powershell
cmd /c 'mysql --default-character-set=gbk -u root -p -e "SHOW TABLES; SELECT COUNT(*) FROM news;" news_app'
```

### 2. Backend

```powershell
cd news_app_backend

# create the virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# create the .env file (see Configuration below), then:
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

The service starts on `http://127.0.0.1:8000`.

- Interactive docs: <http://127.0.0.1:8000/docs>
- Health probe: `GET /` returns `{"msg": "this is a news_app_fastapi_vue"}`

On startup the `lifespan` handler runs `SELECT 1` against MySQL, so a bad `DATABASE_URL` fails fast instead of surfacing on the first request. On shutdown the connection pool is disposed.

### 3. Frontend

```powershell
cd news_app_frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173`. Requests to `/api/*` are proxied to `http://127.0.0.1:8000` by `vite.config.js`, so the browser performs same-origin calls and no CORS negotiation is involved during development.

Production build:

```powershell
npm run build      # emits dist/
npm run preview    # serve the build locally
```

When the frontend is served from a different origin than the API, set `VITE_API_BASE_URL` at build time (e.g. `https://api.example.com`) — `src/config/api.js` reads it and falls back to an empty string so the proxy keeps working in development.

---

## Configuration

Backend configuration lives in `news_app_backend/.env` (ignored by Git):

```ini
# mysql+aiomysql://<user>:<password>@<host>:<port>/<database>?charset=utf8mb4
DATABASE_URL=mysql+aiomysql://root:your_password@127.0.0.1:3306/news_app?charset=utf8mb4

# Echo every SQL statement to stdout (development only)
DB_ECHO=false
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | — | SQLAlchemy async DSN. Missing value raises `RuntimeError` at import time |
| `DB_ECHO` | no | `false` | `true` prints all executed SQL |

Redis connection settings are currently hardcoded in `config/cache_config.py`:

| Setting | Value |
|---|---|
| Host | `localhost` |
| Port | `6379` |
| Database | `0` |
| Protocol | RESP2 (forced for client/server compatibility) |

---

## API Reference

All endpoints are prefixed with `/api`. “Auth” means the request must carry a valid token in the `Authorization` header.

### News

| Method | Path | Auth | Parameters | Description |
|---|---|---|---|---|
| GET | `/api/news/categories` | — | `skip` (0), `limit` (100) | Category list, cached 2 h |
| GET | `/api/news/list` | — | `categoryId` **(required)**, `page` (1), `pageSize` (10, ≤100) | Paged news for a category, cached 30 min |
| GET | `/api/news/detail` | — | `id` **(required)** | Article body, increments `views`, returns up to 5 related articles |

`GET /api/news/list` response payload:

```json
{
  "list": [ { "id": 1, "title": "…", "description": "…", "image": "…", "author": "…",
              "categoryId": 1, "views": 12500, "publishedTime": "2024-01-01T08:00:00" } ],
  "total": 50,
  "hasMore": true
}
```

### User

| Method | Path | Auth | Body / Parameters | Description |
|---|---|---|---|---|
| POST | `/api/user/register` | — | `{ username, password }` | Create account, returns token + profile |
| POST | `/api/user/login` | — | `{ username, password }` | Authenticate, returns token + profile |
| GET | `/api/user/info` | ✅ | — | Current user profile |
| PUT | `/api/user/update` | ✅ | `{ nickname, avatar, gender, bio, phone }` | Update profile fields |
| PUT | `/api/user/password` | ✅ | `{ oldPassword, newPassword }` | Change password (`newPassword` ≥ 6 chars) |

### Favourites

| Method | Path | Auth | Body / Parameters | Description |
|---|---|---|---|---|
| GET | `/api/favorite/check` | ✅ | `newsId` **(required)** | `{ isFavorite: bool }` |
| POST | `/api/favorite/add` | ✅ | `{ newsId }` | Add to favourites |
| DELETE | `/api/favorite/remove` | ✅ | `newsId` **(required)** | Remove one favourite |
| GET | `/api/favorite/list` | ✅ | `page`, `pageSize` | Paged favourites with `favoriteId` / `favoriteTime` |
| DELETE | `/api/favorite/clear` | ✅ | — | Remove all favourites for the user |

### History

| Method | Path | Auth | Body / Parameters | Description |
|---|---|---|---|---|
| POST | `/api/history/add` | ✅ | `{ newsId }` | Record a view |
| GET | `/api/history/list` | ✅ | `page` (1), `pageSize` (10) | Paged history with `historyId` / `viewTime` |
| DELETE | `/api/history/delete/{history_id}` | ✅ | path param | Delete one entry |
| DELETE | `/api/history/clear` | ✅ | — | Clear all history for the user |

### Misc

| Method | Path | Description |
|---|---|---|
| GET | `/` | Liveness string |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

---

## Response Format

Every endpoint returns the same envelope:

```json
{ "code": 200, "message": "获取新闻列表成功", "data": { } }
```

Errors produced by the global handlers keep the shape and set `code` to the HTTP status:

```json
{
  "code": 401,
  "message": "无效的令牌或已经过期的令牌",
  "data": null
}
```

Handled exception types:

| Handler | Status | Typical message |
|---|---|---|
| `HTTPException` | as raised | the raised `detail` |
| `IntegrityError` | 400 | `用户名已存在`, `关联数据不存在`, `数据约束冲突` |
| `SQLAlchemyError` | 500 | `数据库操作失败，请稍后重试` |
| `Exception` | 500 | `服务器内部错误` |

While `DEBUG_MODE = True` (in `utils/exception.py`) the `data` field of 4xx/5xx responses also contains `error_type`, `error_detail`, `traceback`, and `path`. Turn it off before shipping.

---

## Authentication

The API uses **opaque bearer tokens**, not JWT.

1. `POST /api/user/register` or `POST /api/user/login` generates a UUID v4 token, stores it in `user_token` with a **7-day** expiry, and returns it.
2. Each user has **one** active token row: logging in again overwrites the previous token, which invalidates the old session.
3. Clients send the token in the `Authorization` header. Both forms are accepted because `utils/auth.py` strips an optional `Bearer ` prefix:

   ```
   Authorization: 550e8400-e29b-41d4-a716-446655440000
   Authorization: Bearer 550e8400-e29b-41d4-a716-446655440000
   ```

4. `get_current_user` looks the token up, rejects it if missing or expired (`401`), and hands the `User` ORM object to the route.

Passwords are hashed with `passlib`'s bcrypt context; plaintext passwords are never stored or logged.

There is no logout endpoint and no token refresh — logging out is a client-side operation (`store.logout()` clears state), and the server-side token simply expires.

---

## Caching

Cache-aside with Redis, implemented in `cache/news_cache.py` and used by `crud/news_cache.py`.

| Key pattern | Content | TTL |
|---|---|---|
| `news:categories` | Serialized category list | 7200 s (2 h) |
| `news_list{category}:{page}:{pageSize}` | One page of news items | 1800 s (30 min) |

Design notes:

- TTLs differ per data type so keys do not all expire simultaneously (avoids a cache stampede).
- Values are JSON (`ensure_ascii=False`), stored as strings.
- All Redis calls are wrapped in `try/except` and return `None` on failure, so a Redis outage degrades to plain database queries rather than breaking the API.
- There is currently **no invalidation** on write paths; news edits made directly in MySQL will not be reflected until the TTL expires.

---

## Database Schema

Database: `news_app`, charset `utf8mb4`, engine InnoDB.

| Table | Purpose | Key columns |
|---|---|---|
| `user` | Accounts | `username` (unique), `password` (bcrypt), `nickname`, `avatar`, `gender` (enum), `bio`, `phone` (unique) |
| `user_token` | Active session token | `user_id` FK, `token` (unique), `expires_at` |
| `news_category` | Categories | `name` (unique), `sort_order` |
| `news` | Articles | `title`, `description`, `content`, `image`, `author`, `category_id` FK, `views`, `publish_time` |
| `related_news` | Reserved for article relations | `news_id`, `related_news_id` |
| `favorite` | Favourites | `user_id` + `news_id` unique together |
| `history` | Browsing history | `user_id` FK, `news_id` FK, `view_time` |
| `ai_chat` | Reserved for AI conversation logs | `user_id` FK, message fields |

`user`, `news_category` and `news` all carry `created_at` / `updated_at` timestamps managed by the database.

---

## Frontend Routes

| Path | View | Notes |
|---|---|---|
| `/` | — | Redirects to `/home` |
| `/home` | `Home.vue` | Tabbed news feed with pull-to-refresh and infinite scroll (kept alive) |
| `/news/detail/:id` | `NewsDetail.vue` | Article body, favourite toggle, related news |
| `/category` | `Category.vue` | Category browser (kept alive) |
| `/favorite` | `Favorite.vue` | Favourites list with pagination |
| `/history` | `History.vue` | Browsing history with delete / clear |
| `/aichat` | `AIChat.vue` | AI chat UI (see limitations) |
| `/my` | `My.vue` | Personal centre (kept alive) |
| `/profile` | `Profile.vue` | Edit profile |
| `/settings` | `Settings.vue` | Theme and language |
| `/login`, `/register` | `Login.vue`, `Register.vue` | Auth forms |

State stores: `store/user.js` (token + profile), `store/modules/news.js`, `store/modules/favorite.js`, `store/modules/history.js`, `store/theme.js`, `store/language.js` — all persisted to `localStorage` through `pinia-plugin-persistedstate`.

---

## Known Limitations

These are known shortcuts rather than bugs that block development. They matter before any real deployment.

- **CORS is wide open.** `main.py` uses `allow_origins=["*"]` together with `allow_credentials=True`. That combination is rejected by browsers for credentialed requests and is unsafe in production — pin the real origins.
- **Debug tracebacks are exposed.** `DEBUG_MODE = True` in `utils/exception.py` returns stack traces inside error payloads.
- **The AI chat key ships to the browser.** `AIChat.vue` calls the DashScope-compatible endpoint directly via `fetch` with a key read from `src/config/api.js`. Any key placed there is bundled into the public JavaScript. For real use, proxy the call through the backend.
- **No cache invalidation.** Writing directly to MySQL leaves stale values in Redis until the TTL elapses.
- **`GET /api/favorite/list` has `page: int = Query(10, ge=1)`** — the default page is 10 rather than 1.
- **Mixed timestamp semantics.** `Favorite.created_at` uses `datetime.utcnow` while the other models use local `datetime.now`, so favourited-at values are offset from the rest of the schema.
- **Multiple declarative bases.** `models/news.py`, `models/users.py`, `models/favorite.py`, and `models/history.py` each declare their own `Base`, so cross-model `relationship()` definitions are not available; joins are written explicitly in `crud/`.
- **No route guard.** `router.beforeEach` only sets the document title; protected pages rely on the API answering `401`.
- **Redis settings are not configurable via environment variables** (hardcoded in `config/cache_config.py`), and there is no Docker/compose file — MySQL and Redis are expected to be installed locally.

---

## Further Documentation

Design documents (Chinese) live in `news_app_backend/docs/`:

- `API接口规范文档.md` — endpoint contracts and conventions
- `项目后端设计说明文档.md` — backend design rationale

For live, always-current API documentation, run the backend and open `/docs` (Swagger UI), which is generated from the same schemas the endpoints validate against.

---

## Purpose

This repository is a study project covering asynchronous FastAPI patterns, layered backend design, Redis cache-aside, and a Vue 3 mobile frontend. Credentials in `.env` are local development values only — rotate them before using the code anywhere else.
