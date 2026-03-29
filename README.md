# Investor-CRM

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend: React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://react.dev)
[![Deploy: Docker + Cloudflare](https://img.shields.io/badge/Deploy-Docker%20%2B%20Cloudflare-F38020.svg)](docs/SELF_HOSTED.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> Open source investor pipeline and contact management for startups. Built by founders, for founders.

**Live:** [https://bettermind.buzz](https://bettermind.buzz)

<!-- TODO: Add screenshot of dashboard here -->
<!-- ![BetterMind CRM Dashboard](docs/screenshots/dashboard.png) -->

## Why This Exists

Fundraising is chaos. Spreadsheets break. Notion gets messy. Expensive CRMs are overkill for a seed-stage startup tracking 50 investors. BetterMind CRM is the investor tracking tool we built for ourselves and are now sharing with the community.

## Features

- **Investor pipeline tracking** with customizable stages and probability tracking
- **Contact management** with full address, website, social links, and completeness indicators
- **Organization directory** linking contacts to companies and firms
- **Interaction logging** for emails, calls, meetings, and notes
- **Multi-user support** with role-based access (admin / user)
- **Tag system** for flexible categorization
- **Contact Info Card** with clickable email, phone, LinkedIn, website, Twitter/X, and Google Maps links
- **Inline edit mode** for updating contact details without leaving the detail view
- **In-app help** with a built-in user manual viewer
- **Full REST API** with interactive docs (FastAPI / Swagger at `/docs`)
- **Self-hosted** on Docker Desktop with Cloudflare Tunnel ($0/month)
- **Mobile-responsive** React frontend
- **PostgreSQL 16** database with automated backups

## Quick Start

### Option 1: Docker with PostgreSQL (production — recommended)

```bash
git clone https://github.com/jessl2juice/Investor-CRM.git
cd Investor-CRM
docker-compose up -d
# Open http://localhost:8080
```

This starts **PostgreSQL 16** and the **FastAPI + React** app. The database schema is created automatically on first run with demo seed data.

Default login: `admin@example.com` / `changeme123!` (created on first run). Change via `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD` env vars.

### Option 2: Manual Setup (development)

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
# API running at http://localhost:8080

# Frontend (in a second terminal, for hot reload during development)
cd frontend
npm install
npm run dev
# Dev server at http://localhost:5173 (proxies API to :8080)
```

### Option 3: Self-Hosted with Cloudflare Tunnel (internet-accessible, $0/month)

See [docs/SELF_HOSTED.md](docs/SELF_HOSTED.md) for the complete guide to running the CRM on your own machine with HTTPS access from anywhere.

## Screenshots

| Login | Dashboard | Contact Detail | Help / User Manual |
|-------|-----------|----------------|-------------------|
| ![Login](docs/screenshots/CRM-login.PNG) | ![Dashboard](docs/screenshots/CRM-main.PNG) | ![Contact Detail](docs/screenshots/CRM-detail.PNG) | ![Help](docs/screenshots/CRM-help.PNG) |

> **Live:** [bettermind.buzz](https://bettermind.buzz)

## Project Structure

```text
Investor-CRM/
  Dockerfile              # Multi-stage build (Node frontend + Python backend)
  docker-compose.yml      # PostgreSQL 16 + FastAPI app stack
  backup-crm.ps1          # Weekly PostgreSQL backup script (Windows)
  import_data.py          # Import data from JSON backups into PostgreSQL
  export_from_cloud.py    # Export data from Cloud SQL (migration tool)
  deploy.sh               # Cloud Run deploy script (legacy)
  .env.example            # Environment variable template
  backend/
    main.py               # FastAPI app entry point
    database.py           # Schema, migrations, seed data
    auth.py               # Token creation and verification
    models.py             # Pydantic request/response models
    deps.py               # Shared DB helpers
    routes/               # API route modules
      contacts.py
      organizations.py
      interactions.py
      deals.py
      programs.py
    requirements.txt      # Python dependencies
    test_fixes.py         # API test suite
  frontend/
    src/
      App.jsx             # Main React app
      api.js              # API client with auth
      components/         # UI components
        ContactDetail.jsx
        HelpModal.jsx
        LoginScreen.jsx
        UserManagement.jsx
        ui.jsx
      index.css           # Global styles
      main.jsx            # Entry point
    vite.config.js        # Vite config with API proxy
    package.json
  docs/
    SELF_HOSTED.md        # Self-hosted deployment guide (Docker + Cloudflare)
    DEPLOYMENT.md         # Legacy Cloud Run deployment guide
    USER_MANUAL.md        # End-user documentation
    API_REFERENCE.md      # Full API reference
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| **Frontend** | React 18, Vite 6 |
| **Database** | PostgreSQL 16 (Docker), SQLite (dev fallback) |
| **Auth** | HMAC token-based (stateless, 24-hour TTL) |
| **Infrastructure** | Docker Desktop, Cloudflare Tunnel |
| **DNS/SSL** | Cloudflare (free tier — auto-provisioned HTTPS) |
| **Backups** | `pg_dump` via `backup-crm.ps1` (Windows Task Scheduler) |

## Architecture

```text
                    Internet
                       |
              +--------+--------+
              | Cloudflare CDN  |
              |  SSL/TLS + DNS  |
              |  bettermind.buzz|
              +--------+--------+
                       |
              +--------+--------+
              | Cloudflare      |
              | Tunnel (local)  |
              | cloudflared svc |
              +--------+--------+
                       |
               localhost:8080
                       |
+----------------------------------------------+
|              Docker Desktop                  |
|                                              |
|  +--------------------+  +--------------+    |
|  |  bettermind-app    |  | bettermind-db|    |
|  |  FastAPI + React   |--| PostgreSQL 16|    |
|  |  Port 8080         |  | Port 5432    |    |
|  +--------------------+  +--------------+    |
|                              |               |
|                          pgdata volume       |
+----------------------------------------------+
```

**Survives a reboot — everything auto-starts:**

- **Docker Desktop** starts on login (Settings → General → "Start Docker Desktop when you sign in")
- **PostgreSQL + App containers** restart automatically (`restart: unless-stopped`)
- **Cloudflare Tunnel** runs as a Windows service (`cloudflared`, StartType: Automatic)
- **SSL certificates** are provisioned and renewed by Cloudflare automatically
- **PostgreSQL data** persists in a Docker named volume (`pgdata`)
- **Monthly cost: $0** — Cloudflare free tier + Docker Desktop

## API Documentation

Interactive API docs are available at `/docs` (Swagger UI) when running locally or in production.

Full reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Authenticate and get token |
| GET | `/api/contacts` | List contacts (filterable, searchable) |
| POST | `/api/contacts` | Create contact |
| GET | `/api/contacts/{id}` | Get contact with interactions and deals |
| PUT | `/api/contacts/{id}` | Update contact (partial) |
| DELETE | `/api/contacts/{id}` | Delete contact |
| GET | `/api/organizations` | List organizations |
| GET | `/api/deals` | List deals (pipeline) |
| GET | `/api/programs` | List programs |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/help` | User manual content |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Docker | Full PostgreSQL connection string (set in `docker-compose.yml`) |
| `TOKEN_SECRET` | Yes | Secret for signing auth tokens. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `PORT` | No | Server port (default: `8080`) |
| `ALLOWED_ORIGINS` | No | Comma-separated list of allowed CORS origins |
| `INSTANCE_CONNECTION_NAME` | Cloud SQL only | Cloud SQL connection string (legacy) |
| `DB_USER` | Cloud SQL only | Database username (legacy) |
| `DB_PASS` | Cloud SQL only | Database password (legacy) |
| `DB_NAME` | Cloud SQL only | Database name (legacy) |

When `DATABASE_URL` is set, the app connects to PostgreSQL via pg8000. When `INSTANCE_CONNECTION_NAME` is set, it uses Cloud SQL Connector. Otherwise, it falls back to SQLite.

See [.env.example](.env.example) for a template.

## Backups

The `backup-crm.ps1` script creates date-stamped PostgreSQL dumps:

```powershell
# Run manually
.\backup-crm.ps1

# Backups saved to C:\CRM-Backups\bettermind-YYYY-MM-DD.sql
# Automatically keeps only the last 12 backups
```

**Schedule weekly backups** via Windows Task Scheduler:

1. Open Task Scheduler → Create Basic Task
2. Name: `BetterMind CRM Backup`
3. Trigger: Weekly
4. Action: Start a program
5. Program: `powershell.exe`
6. Arguments: `-ExecutionPolicy Bypass -File "C:\Users\Jess\Desktop\BetterMind\CRM\backup-crm.ps1"`

**Restore from backup:**

```powershell
# Stop the app, drop and recreate the database, then restore
docker-compose stop app
docker exec -i bettermind-db psql -U bettermind -d postgres -c "DROP DATABASE bettermind_crm;"
docker exec -i bettermind-db psql -U bettermind -d postgres -c "CREATE DATABASE bettermind_crm;"
Get-Content C:\CRM-Backups\bettermind-2026-03-29.sql | docker exec -i bettermind-db psql -U bettermind -d bettermind_crm
docker-compose start app
```

## Data Import / Export

### Import from JSON backups

```bash
# Ensure containers are running
docker-compose up -d

# Run the import script (connects to PostgreSQL on localhost:5433)
python import_data.py
```

The `import_data.py` script loads data from JSON files (`orgs_full.json`, `contacts_full.json`, etc.), preserves original IDs, resets PostgreSQL sequences, and creates user accounts.

### Export from Cloud SQL (migration tool)

```bash
# Requires gcloud auth and Cloud SQL Python Connector
python export_from_cloud.py
```

The `export_from_cloud.py` script was used to migrate data from the original Google Cloud SQL instance. It exports all tables to JSON files for use with `import_data.py`.

## Design Decisions

- **Single-file frontend** (`App.jsx`): keeps the CRM simple and deployable without a complex build pipeline. All state is local React state with `useState`/`useMemo`.
- **No ORM models**: raw SQL via `sqlalchemy.text()` for full control and transparency. Schema defined as DDL strings in `database.py`.
- **Dual database support**: PostgreSQL via `DATABASE_URL` or Cloud SQL Connector, with SQLite fallback. Detected at startup.
- **Stateless auth**: HMAC tokens with embedded claims (email, role, password version). No session store needed. 24-hour TTL.
- **Migration-safe schema evolution**: new columns added via `ALTER TABLE ADD COLUMN IF NOT EXISTS` (PostgreSQL) or `try/except` (SQLite), so existing databases upgrade transparently on startup.
- **Self-hosted by design**: migrated from Cloud Run ($150+/month) to Docker Desktop + Cloudflare Tunnel ($0/month) with zero downtime.

## Migration History

BetterMind CRM was originally deployed on Google Cloud Platform:

| Service | Purpose | Monthly Cost |
|---------|---------|-------------|
| Cloud Run | App hosting | ~$5 |
| Cloud SQL (db-f1-micro) | PostgreSQL 15 | ~$140 |
| Artifact Registry | Docker images | ~$5 |
| **Total** | | **~$150/month** |

In March 2026, the CRM was migrated to a self-hosted Docker Desktop setup with Cloudflare Tunnel for $0/month. All GCP resources (Cloud SQL, Cloud Run, Artifact Registry) were deleted. The GCP project (`bettermind-crm`) was preserved but is empty.

See [docs/SELF_HOSTED.md](docs/SELF_HOSTED.md) for the self-hosted deployment guide.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code style (Python: PEP 8, JS: ESLint defaults)

## License

MIT License. See [LICENSE](LICENSE) for details.

## Built By

[BetterMind.Space](https://bettermind.space) | [Clinician Assist Inc.](https://clinicianassist.ai)

Originally built to manage our own $2.5M seed fundraise across 35+ investors. Now open source for every founder who needs it.
