# BetterMind CRM — Cloud Run Deployment

## Architecture
- **Backend**: FastAPI (Python) serving SQLite CRM database via REST API
- **Frontend**: React SPA with Vite, served by the same container
- **Infrastructure**: Google Cloud Run (serverless, scales to zero)
- **Database**: SQLite with persistent Cloud Storage backup (optional)

## Prerequisites
- `gcloud` CLI authenticated with a project that has Cloud Run enabled
- Docker installed (Cloud Build can also be used)

## One-Command Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

## Manual Deploy Steps
```bash
# 1. Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# 2. Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# 3. Build and deploy
gcloud run deploy bettermind-crm \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --port 8080

# 4. Get the URL
gcloud run services describe bettermind-crm --region us-west1 --format='value(status.url)'
```

## Project Structure
```
bettermind-crm/
├── README.md
├── deploy.sh              # One-command deploy script
├── Dockerfile             # Multi-stage build (frontend + backend)
├── .dockerignore
├── .gcloudignore
├── backend/
│   ├── main.py            # FastAPI application
│   ├── database.py        # SQLite schema + seed data
│   ├── requirements.txt   # Python dependencies
│   └── bettermind_crm.db  # Pre-seeded database (generated on first run)
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx         # Main CRM application
│       └── index.css
└── cloudbuild.yaml         # Alternative: Cloud Build config
```

## API Endpoints
- `GET /api/contacts` — List all contacts (filterable: ?category=investor&status=active)
- `GET /api/contacts/{id}` — Get single contact with interactions
- `POST /api/contacts` — Create contact
- `PUT /api/contacts/{id}` — Update contact
- `DELETE /api/contacts/{id}` — Delete contact
- `GET /api/organizations` — List organizations
- `GET /api/interactions?contact_id=1` — List interactions
- `POST /api/interactions` — Log interaction
- `GET /api/deals` — Pipeline deals
- `GET /api/programs` — Programs/milestones
- `GET /api/stats` — Dashboard statistics
- `GET /` — Serves React frontend

## Environment Variables (optional)
- `PORT` — Server port (default: 8080, Cloud Run sets this)
- `DATABASE_PATH` — SQLite file path (default: ./bettermind_crm.db)
