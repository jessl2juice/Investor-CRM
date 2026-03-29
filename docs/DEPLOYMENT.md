# Deployment Guide (Legacy — Google Cloud Run)

> **Note:** This guide is for the original Google Cloud Run deployment, which has been **deprecated** in favor of self-hosted Docker Desktop + Cloudflare Tunnel. See [SELF_HOSTED.md](SELF_HOSTED.md) for the current deployment guide. All GCP resources (Cloud SQL, Cloud Run, Artifact Registry) were deleted in March 2026.

BetterMind CRM was originally designed to deploy to Google Cloud Run with Cloud SQL (PostgreSQL). This guide is preserved for reference.

## Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
- A GCP project with billing enabled
- Cloud SQL Admin API enabled
- Cloud Run API enabled
- Cloud Build API enabled
- Artifact Registry API enabled

## 1. Create a Cloud SQL Instance

```bash
gcloud sql instances create bettermind-crm-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-west1 \
  --project=YOUR_PROJECT_ID
```

Create the database and user:

```bash
gcloud sql databases create bettermind_crm \
  --instance=bettermind-crm-db \
  --project=YOUR_PROJECT_ID

gcloud sql users create bettermind \
  --instance=bettermind-crm-db \
  --password=YOUR_DB_PASSWORD \
  --project=YOUR_PROJECT_ID
```

## 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```
DB_USER=bettermind
DB_PASS=your-database-password
DB_NAME=bettermind_crm
TOKEN_SECRET=your-random-64-char-hex-string
```

Generate a secure TOKEN_SECRET:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 3. Grant IAM Permissions

The default compute service account needs these roles:

```bash
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

## 4. Deploy

```bash
./deploy.sh YOUR_PROJECT_ID us-west1
```

The deploy script will:

1. Build the Docker image (multi-stage: frontend + backend)
2. Push to Artifact Registry
3. Deploy to Cloud Run with environment variables
4. Output the service URL

## 5. Custom Domain (Optional)

Map a custom domain in the Cloud Run console:

1. Go to Cloud Run > your service > Manage Custom Domains
2. Add your domain
3. Update DNS records as instructed

## Architecture Notes

- **Database detection is automatic.** When `INSTANCE_CONNECTION_NAME` is set, the app connects to Cloud SQL via the Cloud SQL Python Connector. When it is not set, the app uses SQLite for zero-config local development.
- **Schema migrations run on startup.** New columns are added via `ALTER TABLE ADD COLUMN IF NOT EXISTS` (PostgreSQL) or `try/except` (SQLite). No manual migration steps needed.
- **Seed data is idempotent.** The `seed_data` and `seed_users` functions check for existing records before inserting, so restarts are safe.
- **The frontend is built at Docker build time** and served as static files by the FastAPI backend. No separate frontend deployment needed.

## Troubleshooting

**Cloud Run returns 502:**
Check Cloud Run logs. Common causes: missing env vars, Cloud SQL connection errors, or the service account lacking `cloudsql.client` role.

**Database connection refused:**
Ensure `INSTANCE_CONNECTION_NAME` matches `project:region:instance` exactly. Verify the Cloud SQL instance is running and the user/password are correct.

**Frontend shows blank page:**
The frontend build must complete successfully during Docker build. Check that `npm run build` works locally.

**Token errors after redeploy:**
If `TOKEN_SECRET` changes between deploys, all existing tokens become invalid. Users will need to log in again.
