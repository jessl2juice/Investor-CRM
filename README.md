# Investor-CRM

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend: React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://react.dev)
[![Deploy: Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-4285F4.svg)](https://cloud.google.com/run)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> Open source investor pipeline and contact management for startups. Built by founders, for founders.

**Live demo:** [https://bettermind.buzz](https://bettermind.buzz)

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
- **One-click deploy** to Google Cloud Run
- **Mobile-responsive** React frontend
- **PostgreSQL** in production, **SQLite** for local dev (zero config)

## Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/jessl2juice/Investor-CRM.git
cd Investor-CRM
docker-compose up
# Open http://localhost:8080
```

Default login: `admin@example.com` / `changeme123!` (created automatically on first run with SQLite). Change this via `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD` env vars.

### Option 2: Manual Setup

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

### Option 3: Deploy to Google Cloud Run

```bash
cp .env.example .env
# Edit .env with your Cloud SQL credentials and TOKEN_SECRET
./deploy.sh your-gcp-project us-west1
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full deployment guide.

## Screenshots

| Login | Dashboard | Contact Detail | Help / User Manual |
|-------|-----------|----------------|-------------------|
| ![Login](docs/screenshots/CRM-login.PNG) | ![Dashboard](docs/screenshots/CRM-main.PNG) | ![Contact Detail](docs/screenshots/CRM-detail.PNG) | ![Help](docs/screenshots/CRM-help.PNG) |

> **Live demo:** [bettermind.buzz](https://bettermind.buzz)

## Project Structure

```text
Investor-CRM/
  Dockerfile              # Multi-stage build (Node + Python)
  docker-compose.yml      # Local dev with SQLite
  deploy.sh               # Cloud Run deploy script
  .env.example            # Environment variable template
  backend/
    main.py               # FastAPI app entry point
    database.py            # Schema, migrations, seed data
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
    USER_MANUAL.md        # End-user documentation
    API_REFERENCE.md      # Full API reference
    DEPLOYMENT.md         # Cloud Run deployment guide
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| **Frontend** | React 18, Vite 6 |
| **Database** | PostgreSQL 15 (prod), SQLite (local dev) |
| **Auth** | HMAC token-based (stateless, 24-hour TTL) |
| **Infrastructure** | Docker, Google Cloud Run, Cloud SQL |
| **CI/CD** | Cloud Build (`cloudbuild.yaml`) |

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
| `TOKEN_SECRET` | Yes | Secret for signing auth tokens. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `INSTANCE_CONNECTION_NAME` | Cloud SQL only | Cloud SQL connection string (`project:region:instance`) |
| `DB_USER` | Cloud SQL only | Database username |
| `DB_PASS` | Cloud SQL only | Database password |
| `DB_NAME` | Cloud SQL only | Database name |
| `PORT` | No | Server port (default: `8080`, Cloud Run sets this) |

When `INSTANCE_CONNECTION_NAME` is not set, the app automatically uses SQLite for zero-config local development.

See [.env.example](.env.example) for a template.

## Architecture

```text
+---------------------------------------------------+
|                Google Cloud Run                    |
|  +--------------------+  +---------------------+  |
|  |  React SPA (Vite)  |  |  FastAPI Backend     |  |
|  |  Static at /assets |--|  REST API at /api/*  |  |
|  |  SPA fallback at / |  |  Auth (HMAC tokens)  |  |
|  +--------------------+  +----------+----------+  |
|                                      |             |
+---------------------------------------------------+
                                       |
                              +--------+--------+
                              |   Cloud SQL      |
                              |   PostgreSQL 15  |
                              +-----------------+
```

**Local development** uses the same architecture but with SQLite instead of Cloud SQL. The backend auto-detects which database to use at startup.

## Design Decisions

- **Single-file frontend** (`App.jsx`): keeps the CRM simple and deployable without a complex build pipeline. All state is local React state with `useState`/`useMemo`.
- **No ORM models**: raw SQL via `sqlalchemy.text()` for full control and transparency. Schema defined as DDL strings in `database.py`.
- **Dual database support**: PostgreSQL in production via Cloud SQL Connector, SQLite locally. Detected at startup via `INSTANCE_CONNECTION_NAME`.
- **Stateless auth**: HMAC tokens with embedded claims (email, role, password version). No session store needed. 24-hour TTL.
- **Migration-safe schema evolution**: new columns added via `ALTER TABLE ADD COLUMN IF NOT EXISTS` (PostgreSQL) or `try/except` (SQLite), so existing databases upgrade transparently on startup.

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
