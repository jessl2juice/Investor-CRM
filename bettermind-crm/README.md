# BetterMind CRM

Contact management, investor pipeline, and program tracking for [BetterMind.Space](https://bettermind.space) — the AI-powered mental health platform by Clinician Assist Inc.

**Live:** [https://bettermind.buzz](https://bettermind.buzz)

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Authentication & Security](#authentication--security)
- [Database](#database)
- [Deployment](#deployment)
- [Testing](#testing)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Google Cloud Run                       │
│  ┌──────────────────────┐  ┌─────────────────────────┐  │
│  │   React SPA (Vite)   │  │   FastAPI Backend        │  │
│  │   Static via /assets │──│   REST API at /api/*     │  │
│  │   SPA fallback at /  │  │   Auth (HMAC tokens)     │  │
│  └──────────────────────┘  └───────────┬─────────────┘  │
│                                        │                 │
│                              ┌─────────▼──────────┐     │
│                              │  Cloud SQL (Postgres)│    │
│                              │  bettermind_crm      │    │
│                              └──────────────────────┘    │
└─────────────────────────────────────────────────────────┘

Local dev: SQLite fallback (no Cloud SQL needed)
```

- **Single container** serves both the React SPA and the FastAPI backend
- **Cloud SQL PostgreSQL** in production, **SQLite** locally (auto-detected)
- **Cloud Run** with serverless scaling (0–3 instances)
- **Custom domain** at bettermind.buzz via Cloud Run domain mapping

---

## Tech Stack

| Layer       | Technology                                          |
|-------------|-----------------------------------------------------|
| Frontend    | React 18, Vite 6, vanilla CSS (inline styles)       |
| Backend     | FastAPI 0.115, Uvicorn, Pydantic v2                 |
| Database    | PostgreSQL (Cloud SQL) / SQLite (local)              |
| ORM         | SQLAlchemy 2.0 (raw SQL via `sqlalchemy.text()`)    |
| Auth        | HMAC-SHA256 tokens (custom, stateless)               |
| Passwords   | PBKDF2-HMAC-SHA256, 600k iterations, random salt    |
| Infra       | Google Cloud Run, Cloud Build, Cloud SQL Connector   |
| Container   | Multi-stage Docker (Node 20 build → Python 3.12 run) |

---

## Project Structure

```
bettermind-crm/
├── README.md                 # This file
├── Dockerfile                # Multi-stage build (frontend + backend)
├── deploy.sh                 # One-command Cloud Run deploy script
├── cloudbuild.yaml           # Alternative: Cloud Build CI/CD config
├── .dockerignore
├── .gcloudignore
│
├── backend/
│   ├── main.py               # FastAPI app — routes, auth, middleware
│   ├── database.py           # Schema, seed data, password hashing
│   ├── requirements.txt      # Python dependencies (pinned)
│   ├── test_fixes.py         # API test suite (62 tests)
│   └── bettermind_crm.db     # SQLite DB (auto-generated on first run)
│
└── frontend/
    ├── package.json           # React + Vite dependencies
    ├── vite.config.js         # Dev proxy (/api → localhost:8080)
    ├── index.html             # SPA entry point
    └── src/
        ├── main.jsx           # React DOM render
        ├── App.jsx            # Full CRM UI (single-file component)
        └── index.css          # Global styles
```

---

## Local Development

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The server starts on `http://localhost:8080`. On first run it creates `bettermind_crm.db` and seeds it with 47 contacts, 21 organizations, 8 interactions, 4 deals, 7 programs, and 1 admin user.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite dev server starts on `http://localhost:5173` and proxies `/api/*` requests to `localhost:8080`.

### Full-stack (production-like)

```bash
cd frontend && npm run build && cd ..
python backend/main.py
```

FastAPI serves the built React app at `http://localhost:8080`.

---

## Environment Variables

| Variable                   | Required | Default                | Description                                           |
|----------------------------|----------|------------------------|-------------------------------------------------------|
| `PORT`                     | No       | `8080`                 | Server port (Cloud Run sets this automatically)       |
| `TOKEN_SECRET`             | **Yes*** | Ephemeral random       | HMAC secret for auth tokens. **Must be stable in prod** or users get logged out on every deploy/cold start |
| `INSTANCE_CONNECTION_NAME` | No       | _(empty → SQLite)_     | Cloud SQL instance (e.g. `project:region:instance`). When set, PostgreSQL is used |
| `DB_USER`                  | No       | `bettermind`           | PostgreSQL username                                   |
| `DB_PASS`                  | No       | `bettermind-crm-2026`  | PostgreSQL password                                   |
| `DB_NAME`                  | No       | `bettermind_crm`       | PostgreSQL database name                              |
| `ALLOWED_ORIGINS`          | No       | See below              | Comma-separated CORS origins. Defaults to Cloud Run URL, bettermind.buzz, localhost |

\* Not technically required — a random secret is generated if missing, but tokens won't survive restarts.

---

## API Reference

All endpoints (except `/api/login`) require a Bearer token in the `Authorization` header.

### Authentication

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| POST   | `/api/login`                   | None     | Login, returns JWT-like token   |
| GET    | `/api/me`                      | User     | Current user info               |

**Login request:**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Login response:**
```json
{ "token": "...", "email": "user@example.com", "name": "User", "role": "admin" }
```

### Contacts

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| GET    | `/api/contacts`                | User     | List contacts (filterable)      |
| GET    | `/api/contacts/{id}`           | User     | Single contact + interactions + deals |
| POST   | `/api/contacts`                | User     | Create contact                  |
| PUT    | `/api/contacts/{id}`           | User     | Update contact (partial)        |
| DELETE | `/api/contacts/{id}`           | User     | Delete contact                  |

**Contact fields:** `first_name`*, `last_name`, `email`, `email_secondary`, `phone`, `phone_secondary`, `linkedin_url`, `organization_id`, `title`, `category`*, `subcategory`, `status`*, `tier`, `last_contact_date`, `next_action`, `next_action_date`, `notes`, `address_line1`, `address_line2`, `city`, `state`, `zip`, `country` (default "US"), `website`, `twitter_url` (* = required on create)

**Query parameters for GET `/api/contacts`:**
- `category` — Filter: `investor`, `google`, `team`, `advisor`, `partner`, `vendor`, `university`, `media`, `other`
- `status` — Filter: `active`, `diligence`, `outreach`, `follow_up`, `scheduled`, `passed`, `connected`, `recruiting`, `searching`, `contact`, `cold`
- `tier` — Filter: `1`, `2`, `3`, `4`
- `search` — Full-text search across name, email, title, notes, org name
- `limit` — Max results (default 200, max 500)
- `offset` — Pagination offset

### Organizations

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| GET    | `/api/organizations`           | User     | List all organizations          |
| GET    | `/api/organizations/{id}`      | User     | Single org + its contacts       |
| POST   | `/api/organizations`           | User     | Create organization             |
| PUT    | `/api/organizations/{id}`      | User     | Update organization (partial)   |
| DELETE | `/api/organizations/{id}`      | User     | Delete organization (nulls contact refs) |

**Valid `type` values:** `vc_firm`, `cvc`, `accelerator`, `tech_company`, `university`, `hospital_system`, `consulting`, `startup`, `media`, `government`, `other`

### Interactions

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| GET    | `/api/interactions`            | User     | List interactions (`?contact_id=`, `?limit=`) |
| GET    | `/api/interactions/{id}`       | User     | Single interaction              |
| POST   | `/api/interactions`            | User     | Log new interaction (auto-updates contact's `last_contact_date`) |
| PUT    | `/api/interactions/{id}`       | User     | Update interaction (partial)    |
| DELETE | `/api/interactions/{id}`       | User     | Delete interaction              |

### Deals (Pipeline)

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| GET    | `/api/deals`                   | User     | List deals (`?stage=`, `?contact_id=`) |
| GET    | `/api/deals/{id}`              | User     | Single deal with contact/org names |
| POST   | `/api/deals`                   | User     | Create deal                     |
| PUT    | `/api/deals/{id}`              | User     | Update deal (partial)           |
| DELETE | `/api/deals/{id}`              | User     | Delete deal                     |

**Valid `stage` values:** `identified`, `outreach`, `meeting`, `diligence`, `term_sheet`, `closed`, `passed`, `dead`

### Programs

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| GET    | `/api/programs`                | User     | List programs (`?status=`)      |
| GET    | `/api/programs/{id}`           | User     | Single program with org/contact names |
| POST   | `/api/programs`                | User     | Create program                  |
| PUT    | `/api/programs/{id}`           | User     | Update program (partial)        |
| DELETE | `/api/programs/{id}`           | User     | Delete program                  |

**Valid `status` values:** `active`, `applied`, `accepted`, `complete`, `planning`

### Tags

| Method | Endpoint                             | Auth     | Description                     |
|--------|--------------------------------------|----------|---------------------------------|
| GET    | `/api/tags`                          | User     | List all tags                   |
| POST   | `/api/tags`                          | User     | Create tag (409 if duplicate)   |
| DELETE | `/api/tags/{id}`                     | User     | Delete tag + remove from contacts |
| GET    | `/api/contacts/{id}/tags`            | User     | List tags for a contact         |
| POST   | `/api/contacts/{id}/tags/{tag_id}`   | User     | Assign tag to contact           |
| DELETE | `/api/contacts/{id}/tags/{tag_id}`   | User     | Remove tag from contact         |

### Bulk Operations

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| PUT    | `/api/bulk/contacts`           | User     | Update multiple contacts at once |

**Bulk update request:**
```json
{ "contact_ids": [1, 2, 3], "status": "follow_up", "category": "investor", "tier": 2 }
```
All fields except `contact_ids` are optional — include only the ones you want to change.

### Stats

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| GET    | `/api/stats`                   | User     | Dashboard stats (counts, breakdowns) |

### User Management (Admin Only)

| Method | Endpoint                       | Auth     | Description                     |
|--------|--------------------------------|----------|---------------------------------|
| GET    | `/api/users`                   | Admin    | List all users                  |
| POST   | `/api/users`                   | Admin    | Create user                     |
| PUT    | `/api/users/{id}/password`     | User*    | Change password (* any user can change own; admin can change any) |
| DELETE | `/api/users/{id}`              | Admin    | Delete user (can't delete self) |

---

## Authentication & Security

### Token Format

Stateless HMAC-SHA256 tokens with the format: `{timestamp}.{base64_payload}.{signature}`

- **Payload:** `{"email": "...", "role": "admin|user"}`
- **TTL:** 7 days
- **Secret:** `TOKEN_SECRET` env var (must be persistent in production)

### Password Hashing

- **New passwords:** PBKDF2-HMAC-SHA256 with 600,000 iterations and a random 16-byte hex salt
- **Legacy support:** Existing SHA-256 single-round hashes are verified via fallback (backward compatible)
- Passwords are never stored in plaintext; only the hash and salt are persisted

### CORS

Origins are restricted to:
- `https://bettermind-crm-340933752067.us-west1.run.app`
- `https://bettermind.buzz`
- `http://localhost:5173` (Vite dev server)
- `http://localhost:8080` (backend direct)

Override with `ALLOWED_ORIGINS` env var (comma-separated).

### Role-Based Access

- **User:** Can access all CRM data (contacts, orgs, deals, programs, interactions, stats). Can change own password.
- **Admin:** All user permissions + user management (create/delete users, change any password). Access to Settings tab in UI.

---

## Database

### Cloud SQL (Production)

- **Instance:** `bettermind-crm:us-west1:bettermind-crm-db`
- **Engine:** PostgreSQL (via Cloud SQL Python Connector + pg8000)
- **Connection pooling:** pool_size=5, max_overflow=2, pool_recycle=1800s

### SQLite (Local Development)

When `INSTANCE_CONNECTION_NAME` is not set, the backend automatically falls back to SQLite at `backend/bettermind_crm.db`.

### Schema

| Table           | Description                                  |
|-----------------|----------------------------------------------|
| `contacts`      | People (investors, team, advisors, etc.) — includes address, website, twitter fields |
| `organizations` | Companies, firms, universities               |
| `interactions`  | Activity log (emails, calls, meetings, notes)|
| `deals`         | Fundraising pipeline stages                  |
| `programs`      | Programs and milestones                      |
| `users`         | CRM login accounts with hashed passwords     |
| `tags`          | Tag definitions                              |
| `contact_tags`  | Many-to-many contact ↔ tag                   |

### Seed Data

On first startup (empty database), the app seeds:
- **21** organizations (VCs, tech companies, universities)
- **47** contacts (investors, Google contacts, team, advisors)
- **8** interactions (emails, meetings)
- **4** deals (fundraising pipeline)
- **7** programs (Google for Startups, YC, campus pilots, etc.)
- **13** tags
- **1** admin user

---

## Deployment

### One-Command Deploy

```bash
chmod +x deploy.sh
./deploy.sh bettermind-crm us-west1
```

This enables APIs, builds via Cloud Build, deploys to Cloud Run with Cloud SQL attached, and prints the live URL.

### Manual Deploy

```bash
# 1. Set project
gcloud config set project bettermind-crm

# 2. Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com sqladmin.googleapis.com

# 3. Deploy
gcloud run deploy bettermind-crm \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --port 8080 \
  --add-cloudsql-instances bettermind-crm:us-west1:bettermind-crm-db \
  --set-env-vars "INSTANCE_CONNECTION_NAME=bettermind-crm:us-west1:bettermind-crm-db,DB_USER=bettermind,DB_PASS=bettermind-crm-2026,DB_NAME=bettermind_crm,TOKEN_SECRET=<your-stable-hex-secret>"

# 4. Get URL
gcloud run services describe bettermind-crm --region us-west1 --format='value(status.url)'
```

### Docker (Local)

```bash
docker build -t bettermind-crm .
docker run -p 8080:8080 bettermind-crm
```

### Custom Domain

The domain `bettermind.buzz` is mapped via Cloud Run domain mapping with A and AAAA DNS records at GoDaddy.

---

## Testing

Run the API test suite (62 tests) against a running local backend:

```bash
# Terminal 1: Start backend
cd backend && python main.py

# Terminal 2: Run tests
cd backend && python test_fixes.py
```

Tests cover:
- **Authentication** — login, token validation, wrong password, role enforcement
- **CRUD** — contacts, interactions, deals (create, read, update, delete)
- **User management** — create user, change password, delete, duplicate prevention
- **Security** — CORS origin validation, 401/403 enforcement, 404 on missing resources
- **Data integrity** — seed data verification, field nulling, search/filtering
- **Error handling** — bad FK references, server resilience after errors

---

## Key Design Decisions

- **Single-file frontend** (`App.jsx`) — keeps the CRM simple and deployable without a complex build pipeline. All state is local React state with `useState`/`useMemo`.
- **No ORM models** — raw SQL via `sqlalchemy.text()` for full control and transparency. Schema defined as DDL strings in `database.py`.
- **Dual database support** — PostgreSQL in production via Cloud SQL Connector, SQLite locally. Detected at startup via `INSTANCE_CONNECTION_NAME`.
- **Stateless auth** — HMAC tokens with embedded claims (email, role). No session store needed. 7-day TTL.
- **PBKDF2 with legacy fallback** — new passwords use 600k-iteration PBKDF2. Old SHA-256 hashes still verify via `_verify_password()` fallback, enabling seamless migration without forcing password resets.
- **Contact Info Card with edit mode** — the contact detail view prominently displays all contact methods (email, phone, LinkedIn, website, Twitter/X, address) with clickable actions (mailto, tel, external links, Google Maps). An inline edit mode allows updating contact info without a separate form.
- **Migration-safe schema evolution** — new columns are added via `ALTER TABLE ADD COLUMN IF NOT EXISTS` (PostgreSQL) or `try/except` (SQLite), so existing databases are upgraded transparently on startup.
