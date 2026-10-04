# RentWise — Rental House Recommendation System

RentWise is a rental marketplace with an **explainable, rule-based recommendation engine**. Users browse and search listings, describe what they need and how much each thing matters, and receive a ranked Top-N shortlist where every result says, in plain language, what it gets right and where it falls short.

It is a modular Django monolith (Django REST Framework, PostgreSQL) with a React + TypeScript frontend, JWT authentication, role-based authorization, and a test suite that covers the engine's rules, the API, security behaviour and performance at 1K–50K listings.

> RentWise does **not** use machine learning. Recommendations come from deterministic, documented rules. [Future ML extension](#future-ml-extension) describes how interaction data recorded today could later feed a learned ranker.

---

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Recommendation algorithm](#recommendation-algorithm)
- [API](#api)
- [Database schema](#database-schema)
- [Authentication](#authentication)
- [Security](#security)
- [Frontend](#frontend)
- [Running locally](#running-locally)
- [Docker setup](#docker-setup) · [Deployment guide](DEPLOYMENT.md)
- [Environment variables](#environment-variables)
- [Testing](#testing)
- [Performance](#performance)
- [Example request and response](#example-request-and-response)
- [Known limitations](#known-limitations)
- [Future improvements](#future-improvements)

---

## Features

**For renters**
- Create an account and sign in (email + password, JWT)
- Browse and search listings with server-side filters, sorting and pagination
- Build a preference profile (location, budget range, bedrooms with *exact* or *at least* mode, furnishing, parking, hard parking requirement) and rate each criterion *must have*, *important*, *preferred* or *optional*
- Get ranked recommendations with a 0–100 match score, a per-criterion score breakdown, strengths and potential mismatches
- An automatic, clearly reported budget relaxation (+10/20/30%) when nothing fits
- Save favourites, compare 2–4 homes side by side, view recommendation history
- Property details with gallery, amenities, availability and a personal match score from saved preferences
- Request information about a listing

**For administrators**
- Dashboard with platform statistics, a daily recommendation-usage chart and engine metrics
- Create, edit, deactivate, flag (for suspicious or invalid listings) and delete listings
- View users, change roles, deactivate accounts
- Review and triage user inquiries

---

## Architecture

```mermaid
flowchart LR
    subgraph Browser
        SPA["React SPA<br/>(TypeScript, Vite, Tailwind)"]
    end
    subgraph Edge["nginx"]
        Static["Static bundle"]
        Proxy["/api reverse proxy<br/>CSP + security headers"]
    end
    subgraph Django["Django REST API (Gunicorn)"]
        MW["Middleware<br/>request ID · access log · CORS · security"]
        Auth["accounts<br/>JWT auth · users · roles"]
        Props["rentals.views<br/>properties · favorites · preferences<br/>history · inquiries · admin"]
        Svc["rentals.services<br/>RecommendationService · analytics"]
        Engine["recommendations.py · explanation.py<br/>recommendation_config.py"]
    end
    DB[("PostgreSQL")]

    SPA -- HTTPS --> Static
    SPA -- "HTTPS /api" --> Proxy --> MW
    MW --> Auth & Props
    Props --> Svc --> Engine
    Auth & Props & Svc --> DB
```

The frontend and API share one origin (nginx in Docker, the Vite proxy in development), so the HttpOnly refresh cookie never needs cross-site CORS.

### Backend layout

```
config/                 settings/{base,development,test,production}.py, urls
core/                   cross-cutting infrastructure
  exceptions.py         consistent {"error": {code, message, details}} envelope
  middleware.py         X-Request-ID + structured access logging
  logging.py            JSON log formatter with request correlation
  permissions.py        IsAdminRole, IsAdminOrReadOnly
  pagination.py, throttles.py, metrics.py, views.py (health)
accounts/               custom email-based User, JWT auth, profile, admin user API
rentals/
  models.py             House (property), PropertyImage, Favorite, UserPreference,
                        RecommendationHistory, PropertyInteraction, Inquiry
  recommendation_config.py   every tunable number of the engine
  recommendations.py    pure per-property scoring (calculate_house_score)
  explanation.py        deterministic explanation generation
  services/
    recommendation_service.py  the pipeline: filter → score → rank → Top-N → explain
    analytics.py               aggregate statistics for the admin dashboard
  serializers/          properties, recommendation requests, user data
  views/                properties, recommendations, favorites, preferences, admin
  filters.py            database-level property search
  management/commands/seed_data.py
```

Views stay thin: they validate input with serializers and delegate to services. The scoring function is pure (no database access) so it can score tens of thousands of candidates per request.

---

## Tech stack

| Layer | Technology |
|---|---|
| API | Python 3.11, Django 5.2, Django REST Framework, djangorestframework-simplejwt, django-filter, drf-spectacular |
| Database | PostgreSQL 16 (SQLite supported for local development and tests) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router, Axios, lucide-react |
| Serving | Gunicorn, nginx, WhiteNoise (Django admin static files) |
| Tooling | Docker Compose, GitHub Actions, ESLint |

---

## Recommendation algorithm

The engine is the core of the original project. The refactor kept its rules and numbers and moved them into a service with clearly separated stages.

```mermaid
flowchart TD
    A[Recommendation request] --> B["Validate<br/>(RecommendationRequestSerializer)"]
    B --> C["Hard constraints in SQL<br/>active · rent range · bedrooms · location · required parking"]
    C -->|no candidates| R{"Budget relaxable?<br/>max_rent set · not must-have · allowed"}
    R -->|yes| R1["Retry with max_rent +10%, +20%, +30%"] --> C
    R -->|no| E[Empty result, with message]
    C -->|candidates| D["Score every candidate<br/>(scoring columns only)"]
    D --> F["Priority multipliers +<br/>must-have penalties, clamp 0–100"]
    F --> G["Deterministic ranking<br/>score ↓ · rent ↑ · area ↓ · id ↑"]
    G --> H[Top-N]
    H --> I["Fetch Top-N in full + primary image<br/>serialize + explain Top-N only"]
    I --> J[Response + history record + metrics]
```

### 1. Hard filtering

Candidates are selected with database filters. Only **active** listings are considered.

| Preference | Filter |
|---|---|
| `max_rent` / `min_rent` | `rent <= max_rent`, `rent >= min_rent` |
| `bedrooms` + `bedroom_mode=exact` | `bedrooms = n` |
| `bedrooms` + `bedroom_mode=minimum` | `bedrooms >= n` |
| `location` | case-insensitive substring match on the locality |
| `required_parking=true` | `parking = true` |

### 2. Weighted scoring

Each criterion the user specified contributes points (`rentals/recommendation_config.py`):

| Criterion | Base points | How points are earned |
|---|---:|---|
| Location | 30 | Locality contains the requested location |
| Budget | 25 | Within `max_rent`: 15 base + up to 10 in proportion to the share of budget saved |
| Bedrooms | 20 | Exact mode: exact match. Minimum mode: 20 for an exact fit, −5 per extra bedroom, floor 10 |
| Furnished | 15 | Matches the requested furnishing |
| Parking | 10 | Matches the parking preference |
| **Total** | **100** | |

`min_rent` is a match/mismatch signal only and earns no points.

### 3. Priority multipliers

| Priority | Multiplier |
|---|---:|
| must_have | ×1.50 |
| important | ×1.25 |
| preferred (default) | ×1.00 |
| optional | ×0.50 |

A criterion's points are multiplied by its priority. Example: a location match marked *important* is worth 30 × 1.25 = 37.5 points.

### 4. Must-have penalty

Every unmet criterion marked *must have* subtracts **20 points**. The final score is clamped to **0–100** and rounded to two decimals.

### 5. Ranking and Top-N

Sorting is fully deterministic: **score descending, then rent ascending, then area descending, then id ascending**. Only the Top-N (default 5, maximum 100) are serialized and explained, so the cost of those stages doesn't depend on how many candidates matched.

### 6. Explanations

`explanation.py` builds a summary, a list of strengths and a list of weaknesses from the property's real attributes and the user's preferences. Example: *"Within your maximum budget of ₹30,000, saving ₹3,500"*, *"Parking was requested but is unavailable"*. No language model is involved; the same input always gives the same text.

### 7. Budget relaxation

When the strict search returns nothing and `max_rent` was given, the engine retries with `max_rent` raised by **10%, 20% and 30%** (configurable through `RECOMMENDATION_BUDGET_RELAXATION_STEPS`), keeping every other constraint. It **never** relaxes when:

- the budget priority is `must_have`, or
- the client sends `allow_budget_relaxation: false`.

A relaxed response always says so (`budget_relaxed`, `original_max_rent`, `relaxed_max_rent`, `relaxation_percentage` and a message). Scores in a relaxed response are computed against the relaxed budget, as in the original engine, but explanations describe each property against the **original** budget: *"Exceeds your maximum budget of ₹26,000 by ₹4,500 (shown because the budget was relaxed)"*.

---

## API

Interactive documentation: **`/api/docs/`** (Swagger UI), **`/api/redoc/`**, raw schema at **`/api/schema/`**. The schema validates with zero warnings in CI.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | public · throttled | Create an account (returns access token, sets refresh cookie) |
| POST | `/api/auth/login/` | public · throttled | Sign in |
| POST | `/api/auth/refresh/` | refresh cookie | Rotate refresh token, get a new access token |
| POST | `/api/auth/logout/` | public | Blacklist refresh token, clear cookie |
| GET/PATCH | `/api/users/me/` | user | Own profile |
| POST | `/api/users/me/password/` | user | Change password (revokes other sessions) |
| GET | `/api/properties/` | public | Search active listings (filters below) |
| POST | `/api/properties/` | admin | Create listing (with images) |
| GET | `/api/properties/{id}/` | public | Details, plus `match` for signed-in users with saved preferences |
| PATCH/PUT/DELETE | `/api/properties/{id}/` | admin | Update, deactivate (`status`), delete |
| GET | `/api/properties/compare/?ids=1,2,3` | public | Compare 2–4 properties (+ match scores) |
| GET | `/api/properties/locations/` | public | Localities with active listing counts |
| POST | `/api/properties/{id}/inquiries/` | user · throttled | Request information |
| POST | `/api/recommendations/` | public · throttled | Recommendations (recorded in history when signed in) |
| GET/DELETE | `/api/recommendations/history/` | user | Own recommendation history / clear it |
| GET | `/api/favorites/` · `/api/favorites/ids/` | user | Own favourites |
| POST/DELETE | `/api/favorites/{property_id}/` | user | Save (idempotent) / remove |
| GET/PUT/PATCH | `/api/preferences/` | user | Saved recommendation preferences |
| GET | `/api/admin/analytics/` | admin | Platform statistics and engine metrics |
| GET/PATCH | `/api/admin/users/` · `/{id}/` | admin | List users; change role / active status |
| GET | `/api/admin/properties/` | admin | All listings, any status, with engagement counts |
| GET/PATCH | `/api/admin/inquiries/` · `/{id}/` | admin | Inquiries and their status |
| GET | `/api/health/` | public | Liveness/readiness probe |

`/api/houses/` remains as an alias of `/api/properties/`, and `/api/recommendations/` keeps its original request and response fields (see [backward compatibility](#backward-compatibility)).

**Property search parameters:** `location` (locality or city), `city`, `min_rent`, `max_rent`, `bedrooms`, `min_bedrooms`, `bathrooms` (minimum), `min_area`, `max_area`, `furnished`, `parking` (`true`/`false`), `property_type`, `available_by` (date), `search` (title, locality, city, description), `ordering` (`rent`, `-rent`, `created_at`, `area_sqft`, …), `page`, `page_size` (default 12, max 50). Invalid values return `400`.

**Errors** always look like this. Stack traces, SQL and settings never reach clients.

```json
{ "error": { "code": "INVALID_REQUEST", "message": "max_rent: Ensure this value is greater than or equal to 0.", "details": { "max_rent": ["Ensure this value is greater than or equal to 0."] } } }
```

Codes: `INVALID_REQUEST`, `MALFORMED_REQUEST`, `NOT_AUTHENTICATED`, `AUTHENTICATION_FAILED`, `PERMISSION_DENIED`, `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `UNSUPPORTED_MEDIA_TYPE`, `RATE_LIMITED` (with `retry_after_seconds`), `INTERNAL_ERROR`.

### Backward compatibility

- `POST /api/recommendations/` accepts the same body as before, plus an optional `allow_budget_relaxation`.
- Responses keep `recommendations[].house`, `score`, `matched_preferences`, `unmatched_preferences`, `explanation`, `total_matches`, `requested_top_n`, `returned_count`, `filters_applied`, `budget_relaxed`, `original_max_rent` and `relaxed_max_rent`. New fields: `rank`, `property` (same object as `house`, which is now deprecated), `score_breakdown` and `relaxation_percentage`.
- **Breaking:** validation errors now use the error envelope above. Field errors moved from the top level to `error.details`.
- **Breaking:** writes to `/api/houses/` now require an admin. Before, anyone could create or delete listings.

---

## Database schema

```mermaid
erDiagram
    User ||--o{ House : "owns (admin who listed)"
    User ||--o| UserPreference : has
    User ||--o{ Favorite : saves
    User ||--o{ RecommendationHistory : requests
    User ||--o{ PropertyInteraction : generates
    User ||--o{ Inquiry : sends
    House ||--o{ PropertyImage : has
    House ||--o{ Favorite : "saved in"
    House ||--o{ PropertyInteraction : receives
    House ||--o{ Inquiry : receives

    User { bigint id string email UK string role "USER|ADMIN" string phone bool is_active }
    House { bigint id string title string location string city int rent int security_deposit int bedrooms int bathrooms int area_sqft bool furnished bool parking string property_type date available_from json amenities string status "active|inactive|flagged" }
    PropertyImage { string image_url string caption bool is_primary }
    Favorite { fk user fk property "UNIQUE(user, property)" }
    UserPreference { string location int min_rent int max_rent int bedrooms string bedroom_mode bool furnished bool parking bool required_parking json priority }
    RecommendationHistory { json request_preferences json result_property_ids float top_score int total_matches bool budget_relaxed float latency_ms }
    PropertyInteraction { string interaction_type "VIEW|FAVORITE|UNFAVORITE|CONTACT" }
    Inquiry { text message string phone string status }
```

The model keeps its original `House` name and table for compatibility; the API calls it a *property*. Check constraints guard rent, deposit, rooms and area at the database level.

### Indexes, and the query each one serves

| Index | Query pattern |
|---|---|
| `house(bedrooms, rent)` (original) | Recommendation hard filter: bedrooms equality/range + rent range |
| `house(status, rent)` | Active-listing search filtered or sorted by rent |
| `house(status, -created_at)` | Default listing order (newest active first) |
| `favorite UNIQUE(user, property)` | Ownership checks, idempotent save, per-user lists |
| `recommendationhistory(user, -created_at)` | A user's history, newest first |
| `recommendationhistory(created_at)` | Admin daily trend and 7-day counts |
| `propertyinteraction(property, interaction_type)` | Most-viewed / engagement counts |
| `propertyinteraction(user, -created_at)` | Per-user interaction timelines (future ranking features) |

Location matching uses `ILIKE '%…%'`, which a B-tree index can't serve; see [future improvements](#future-improvements).

### Query budgets (asserted in tests)

| Request | Queries |
|---|---|
| Anonymous recommendation (strict path) | **2**: candidates (scoring columns only) + Top-N rows with primary image |
| Signed-in recommendation | 4: + user lookup + history insert |
| Property list page | 2: count + page (primary image via correlated subquery) |
| Favourites page | 4, constant in the number of favourites |

---

## Authentication

- **Email + password**, hashed with Django's password hasher (PBKDF2 by default). Django's password validators reject short, common, numeric-only and name-like passwords.
- **Access token**: JWT, 15 minutes (`JWT_ACCESS_TOKEN_MINUTES`), returned in the response body and kept **only in memory** by the frontend, never in `localStorage`.
- **Refresh token**: JWT, 7 days, delivered as an **HttpOnly, SameSite=Lax cookie** scoped to `/api/auth/` (Secure in production). It is rotated on every refresh and the old token is blacklisted.
- **Session restore**: on page load the SPA calls `/api/auth/refresh/`. Axios retries a request that fails with 401 once after a single shared refresh.
- **Logout** blacklists the refresh token and clears the cookie. Changing a password or deactivating a user blacklists all of that user's refresh tokens. An access token stays valid until it expires (at most 15 minutes).
- **Roles**: `USER` and `ADMIN`. Admin-only endpoints use the `IsAdminRole` permission class, and listing writes use `IsAdminOrReadOnly`. A deactivated admin loses access immediately, because a JWT for an inactive user is rejected.

**Trade-off.** An in-memory access token can't be read out of storage by injected script, but script running in the page could still make authenticated calls while it runs. The defences against that are the CSP, React's escaping and never rendering HTML from data. CSRF risk on the cookie-authenticated endpoint is limited: SameSite=Lax blocks cross-site POSTs with the cookie, the cookie is sent only to `/api/auth/`, and the access token comes back in the response body, which cross-origin pages can't read.

---

## Security

- **Settings per environment**; production refuses to start without `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS` and a PostgreSQL `DATABASE_URL`.
- **Secret handling**: no secrets in the repository; `.env` is gitignored and `.env.example` documents every setting. The original repository committed a development `SECRET_KEY`. It has been removed, but it is still in git history, so treat it as compromised and never reuse it.
- **HTTPS in production**: `SECURE_SSL_REDIRECT`, HSTS (1 year, include subdomains; preload is opt-in), secure session, CSRF and refresh cookies, `SECURE_PROXY_SSL_HEADER`.
- **Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, COOP, plus a strict **Content-Security-Policy** from nginx. (`SECURE_BROWSER_XSS_FILTER` no longer exists in Django, and modern browsers ignore the header; CSP replaces it.)
- **CORS**: an explicit allow-list (`CORS_ALLOWED_ORIGINS`); the API never allows all origins.
- **Authorization on the server**: every private or admin endpoint enforces permissions in the API, and all user data is scoped to `request.user`. Tests cover 401/403 for every private endpoint and isolation between users.
- **Input validation** in serializers and filter sets: non-negative and bounded rents, bedroom and bathroom ranges, coordinates, enums, `top_n ≤ 100`, page size ≤ 50, strict booleans, comparison ID lists, image URLs (only `http(s)://` or site-relative paths, so no `javascript:` or `data:` URLs), and an amenity allow-list.
- **Rate limiting** (DRF throttles; set any of them with `THROTTLE_*`):

  | Scope | Default | Applies to |
  |---|---|---|
  | anon / user | 300/hour · 3000/hour | every endpoint |
  | auth | 10/minute per IP | login, password change |
  | refresh | 120/minute | session refresh (runs on every page load) |
  | register | 20/hour | registration |
  | recommendations | 30/minute | `POST /api/recommendations/` |
  | contact | 10/hour | inquiries |

  `NUM_PROXIES=1` in Docker makes throttling key on the real client IP behind nginx.
- **Error hygiene**: unhandled exceptions are logged server-side with their traceback and return a generic `INTERNAL_ERROR`. Login returns the same message for an unknown email, a wrong password and an inactive account.
- **Logging**: structured JSON with request ID, method, path, status, duration and user ID. Query strings, headers, bodies, passwords and tokens are never logged, and sensitive keys are redacted defensively.
- **Frontend**: no secrets in the bundle (only `VITE_API_BASE_URL`), no `dangerouslySetInnerHTML`, listing text rendered as plain text, the access token in memory only, and no credential logging (ESLint `no-console`).
- **Containers**: the backend runs as an unprivileged user and nginx hides its version.

---

## Frontend

`frontend/src/`

```
services/     api.ts (Axios client, token handling, refresh-and-retry), authService,
              propertyService, recommendationService, favoriteService, userService, adminService
context/      AuthProvider, FavoritesProvider, CompareProvider, ToastProvider
hooks/        useAuth, useFavorites, useCompare, useToast, useAsync, useDocumentTitle
layouts/      MainLayout
components/   ui/ (Button, Field, Badge, Card, Modal, Tabs, Pagination, Feedback)
              layout/ (Navbar, Footer, CompareTray, RouteGuards, Page)
              property/ (PropertyCard, PropertyImage with fallback, filters, favourite and compare toggles)
              recommendation/ (PreferenceForm, RecommendationCard, MatchScore,
                               ExplanationPanel, BudgetRelaxationNotice, PreferenceSummary)
              admin/ (Charts, PropertyFormModal, AdminTables)
pages/        Landing, Login, Register, Dashboard, Search, PropertyDetail, Recommend,
              Favorites, Compare, Profile, AdminDashboard, NotFound
types/        API types · utils/ formatting, error normalisation, constants
```

- Every page that loads data handles loading (skeletons), empty, error, offline, unauthorized and not-found states.
- Search filters live in the URL, so results can be shared and the back button works.
- Responsive from 360px phones to desktop; filters become a drawer on mobile, and wide tables scroll inside their container.
- Accessible: labelled controls, a skip link, keyboard-operable menus and dialogs (native `<dialog>`), `aria-live` result regions. Match scores always show the number, never colour alone, and the usage chart has a screen-reader table.
- Pages are code-split with `React.lazy`.
- Demo images are local SVG illustrations (`scripts/generate_demo_images.py`), so the demo works offline. Any broken image falls back to a placeholder.

Route guards are for UX only. The API enforces every permission regardless of what the UI shows.

---

## Running locally

**Prerequisites:** Python 3.11+, Node 20+ (22 recommended), and optionally PostgreSQL 14+.

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# SQLite by default. For PostgreSQL:
# export DATABASE_URL=postgres://rentwise:<password>@localhost:5432/rentwise

python manage.py migrate
SEED_DEMO_PASSWORD='choose-a-demo-password' python manage.py seed_data --demo-users
python manage.py runserver            # http://localhost:8000, docs at /api/docs/
```

`manage.py` defaults to `config.settings.development`, and `manage.py test` uses `config.settings.test`.

Demo accounts created by `--demo-users`: `admin@rentwise.dev` (admin) and `demo@rentwise.dev` (user), with the password from `SEED_DEMO_PASSWORD`. If it isn't set, a random password is generated and printed once.

> Upgrading an old checkout: the project now uses a custom user model, so delete any old `db.sqlite3` before running `migrate`.

### Database setup (PostgreSQL)

```sql
CREATE USER rentwise WITH PASSWORD 'change-me' CREATEDB;
CREATE DATABASE rentwise OWNER rentwise;
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to http://localhost:8000)
npm run lint
npm run build
```

---

## Docker setup

> **Step-by-step guide:** [DEPLOYMENT.md](DEPLOYMENT.md) covers running locally on Windows, macOS or Linux, and free public hosting on Render + Neon.

```bash
cp .env.example .env
# Set DJANGO_SECRET_KEY and POSTGRES_PASSWORD. For a demo, also set:
#   SEED_ON_START=true  SEED_DEMO_PASSWORD=<password>
docker compose up --build
```

| URL | |
|---|---|
| http://localhost:8080 | Application |
| http://localhost:8080/api/docs/ | API documentation |
| http://localhost:8080/django-admin/ | Django admin |

Services: `db` (PostgreSQL 16 with a health check and a named volume), `backend` (Gunicorn with production settings; it migrates and collects static files on start), `frontend` (nginx serving the bundle and proxying `/api`).

The local stack serves plain HTTP, so `.env.example` sets `SECURE_SSL_REDIRECT=False` and `SECURE_COOKIES=False`. In a real deployment behind TLS, set both to `True`, which is the default when they're unset.

---

## Environment variables

See [`.env.example`](.env.example) for the full annotated list. The important ones:

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | required in production | Django signing key |
| `JWT_SIGNING_KEY` | `DJANGO_SECRET_KEY` | Separate key for JWTs |
| `DATABASE_URL` | SQLite (dev only) | e.g. `postgres://user:pass@host:5432/db` |
| `ALLOWED_HOSTS` | required in production | Comma-separated host names |
| `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` | empty | Explicit origin allow-lists |
| `SECURE_SSL_REDIRECT`, `SECURE_COOKIES`, `SECURE_HSTS_SECONDS` | `True`, `True`, 1 year | HTTPS hardening |
| `JWT_ACCESS_TOKEN_MINUTES` / `JWT_REFRESH_TOKEN_DAYS` | 15 / 7 | Token lifetimes |
| `THROTTLE_*` | see [Security](#security) | Rate limits |
| `NUM_PROXIES` | 0 (1 in Docker) | Trusted proxies, for client-IP throttling |
| `API_DOCS_ENABLED` | `True` | Serve `/api/docs/` and `/api/schema/` |
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `SEED_ON_START`, `SEED_DEMO_PASSWORD` | `false`, random | Demo data |
| `VITE_API_BASE_URL` (frontend) | `/api` | The only value exposed to browser code |

---

## Testing

```bash
python manage.py test                                    # 230 tests, SQLite in memory
DATABASE_URL=postgres://... python manage.py test        # the same suite on PostgreSQL
python manage.py makemigrations --check --dry-run        # no missing migrations
python manage.py spectacular --validate --fail-on-warn --file /tmp/schema.yml
cd frontend && npm run lint && npm run build
```

| Area | Files |
|---|---|
| Scoring, priorities, budget scoring, bedroom modes (original) | `rentals/tests/test_recommendations.py` |
| Explanations (original) | `rentals/tests/test_explanation.py` |
| Request validation (original) | `rentals/tests/test_serializers.py` |
| Recommendation API and edge cases (original) | `test_views.py`, `test_edge_cases.py` |
| Query counts, performance, profiling (original) | `test_database.py`, `test_performance.py`, `test_profiling.py` |
| Engine service: tie-breaking, relaxation rules, configurable steps, honest relaxed explanations, metrics, empty DB | `test_recommendation_service.py` |
| Property search, validation, image URL safety, admin CRUD, compare, inquiries | `test_properties_api.py` |
| Favourites, preferences, history | `test_user_data_api.py` |
| 401/403 matrix, user isolation, throttling, error leakage, malformed input, request IDs, CORS, production settings | `test_security.py` |
| Analytics and admin listings | `test_admin_api.py` |
| JWT lifecycle (rotation, blacklist, expiry, forged tokens), profile, admin user management | `accounts/tests/` |
| Seed command | `test_seed_data.py` |

All 85 original tests still pass. The only change to them is that five validation assertions now read field errors from `error.details`.

CI (`.github/workflows/ci.yml`) runs the backend suite against PostgreSQL, the migration check, schema validation, and frontend lint and build.

---

## Performance

The original optimisation (filter → score → rank → Top-N → serialize and explain only the Top-N) is preserved. On top of it:

- Candidates load only the seven columns that scoring needs (`.only(...)`). Profiling showed that instantiating the wider rows dominated latency: loading 25,000 full rows took about 0.50 s, against about 0.30 s with `.only()`, while scoring them took about 0.10 s.
- The Top-N are then fetched in full, with their primary image from a correlated subquery, so the strict path still uses exactly **2 queries**.

Measured in this repository's test suite (`rentals/tests/test_performance.py`, PostgreSQL 16, one run in a container; timings vary by machine). Each benchmark posts `location=HSR, max_rent=40000, bedrooms=2 (exact), top_n=5`:

| Listings in the table | Candidates after hard filters | API response time |
|---:|---:|---:|
| 1,000 | ~167 | 0.012 s |
| 5,000 | ~833 | 0.027 s |
| 10,000 | ~1,667 | 0.064 s |
| 50,000 | ~8,333 | 0.136 s |

---

## Example request and response

```bash
curl -X POST http://localhost:8000/api/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
        "location": "HSR",
        "max_rent": 26000,
        "bedrooms": 2,
        "bedroom_mode": "exact",
        "furnished": true,
        "priority": {"location": "must_have", "budget": "important"},
        "top_n": 1
      }'
```

```json
{
  "recommendations": [
    {
      "rank": 1,
      "property": {
        "id": 11, "title": "Airy 2 BHK Apartment near Agara Lake", "location": "HSR Layout",
        "city": "Bangalore", "rent": 30500, "security_deposit": 61000, "bedrooms": 2,
        "bathrooms": 2, "area_sqft": 1040, "furnished": true, "parking": false,
        "property_type": "apartment", "available_from": "2026-10-04", "status": "active",
        "primary_image": "/images/properties/apartment-1.svg", "created_at": "2026-10-04T07:39:40.201723+05:30"
      },
      "house": { "…": "same object as property (deprecated)" },
      "score": 99.03,
      "matched_preferences": ["location", "budget", "bedrooms", "furnished"],
      "unmatched_preferences": [],
      "score_breakdown": { "location": 45.0, "budget": 19.03, "bedrooms": 20.0, "furnished": 15.0 },
      "explanation": {
        "summary": "Good overall match with several of your preferences satisfied.",
        "strengths": [
          "Matches your preferred location: HSR",
          "Matches your 2-bedroom requirement",
          "Furnished as requested"
        ],
        "weaknesses": [
          "Exceeds your maximum budget of ₹26,000 by ₹4,500 (shown because the budget was relaxed)"
        ]
      }
    }
  ],
  "total_matches": 3,
  "requested_top_n": 1,
  "returned_count": 1,
  "filters_applied": { "location": "HSR", "max_rent": 26000.0, "bedrooms": 2, "bedroom_mode": "exact", "furnished": true, "priority": { "location": "must_have", "budget": "important" }, "top_n": 1, "allow_budget_relaxation": true },
  "budget_relaxed": true,
  "message": "No houses matched your original budget. Showing recommendations with a slightly higher budget.",
  "original_max_rent": 26000.0,
  "relaxed_max_rent": 31200.0,
  "relaxation_percentage": 20
}
```

This is real output from the seeded demo database, abridged only by collapsing `house`. Note how the explanation reports the relaxation honestly while the score reflects the relaxed budget.

---

## Known limitations

- **Score vs. explanation after relaxation**: a relaxed result is scored against the relaxed budget (the original engine's behaviour), so a property can show a high score alongside a "budget exceeded" note. The detail and compare pages score against your *saved* preferences, so the same home can show different scores in different places.
- **Location is substring matching** on the locality name; there is no geographic distance or neighbourhood adjacency.
- **In-process metrics** (`engine_metrics`) are per worker and reset on restart. Durable metrics come from `RecommendationHistory`, which records signed-in users only.
- **Access tokens can't be revoked** before they expire (at most 15 minutes); refresh tokens can.
- **Images are URLs**; there is no upload or object storage.
- **Listings are managed by admins**; there is no landlord self-service role yet.
- **Throttling uses the default local-memory cache**, so limits are per process. Use a shared cache such as Redis when running several Gunicorn workers or hosts.

---

## Future improvements

- **Hybrid ML ranking** (see below), learning-to-rank on the recorded interactions
- **Real geospatial distance**: PostGIS or haversine scoring from the stored coordinates; a `pg_trgm` GIN index for fuzzy location search
- **Redis** for caching and shared throttle counters
- **Availability synchronisation** with listing sources, and expiry of stale listings
- **Cloud object storage** (S3 or GCS) for listing photos, with signed uploads
- **Background analytics** (Celery or RQ) and a Prometheus exporter in place of in-process counters
- Landlord accounts with listing ownership and moderation workflows

### Future ML extension

The current recommender is a transparent rule-based system, and that is a deliberate choice: every score can be explained. `PropertyInteraction` (views, favourites, unfavourites, contacts) and `RecommendationHistory` (what was shown, for which preferences) already capture the implicit feedback a learned model would need.

```mermaid
flowchart LR
    A["Current: rule-based recommender"] --> B["Interaction data<br/>views · saves · contacts · shown results"]
    B --> C["Feature engineering<br/>rule scores · price/area ratios · locality stats · user history"]
    C --> D["Learning-to-rank model<br/>(e.g. LambdaMART)"]
    D --> E["Hybrid recommender"]
    E --> F["Rule constraints filter candidates<br/>ML re-ranks within them<br/>rule explanations stay attached"]
```

Hard constraints and must-have rules would keep defining *which* homes are eligible. A model would only reorder eligible candidates, and its effect would be measured offline (NDCG on logged sessions) and online (A/B tests on save and contact rates) before it replaced the rule-based ordering.
