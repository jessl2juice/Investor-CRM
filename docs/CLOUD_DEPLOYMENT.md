# BetterMind CRM: Cloud Deployment (Cloudflare Pages + Fly.io + Neon)

> **Status:** Deployed and live as of April 25, 2026. All phases complete.

## Architecture

```text
┌──────────────────────────────────────────────────────┐
│                   CLOUDFLARE EDGE                     │
│  ┌────────────────────────┐                           │
│  │  Cloudflare Pages       │  bettermind.buzz          │
│  │  React/Vite static      │  (custom domain)          │
│  │  bettermind-crm project │                           │
│  └────────────┬───────────┘                           │
└───────────────┼──────────────────────────────────────┘
                │ HTTPS (fetch to backend)
                ▼
┌──────────────────────────────────────────────────────┐
│                      FLY.IO                           │
│  ┌────────────────────────┐                           │
│  │  bettermind-crm-api     │                           │
│  │  FastAPI (Python 3.12)  │                           │
│  │  Docker container       │                           │
│  │  256MB RAM              │                           │
│  └────────────┬───────────┘                           │
└───────────────┼──────────────────────────────────────┘
                │ postgresql+pg8000 (SSL)
                ▼
┌────────────────────────┐
│  Neon PostgreSQL        │
│  bettermind_crm db      │
│  Serverless, free tier  │
└────────────────────────┘
```

**Monthly Cost:**

| Service | Tier | Cost |
|---------|------|------|
| Cloudflare Pages | Free | $0 |
| Fly.io (256MB, shared CPU) | Hobby | ~$3-5 |
| Neon PostgreSQL | Free (0.5GB) | $0 |
| **Total** | | **~$3-5/mo** |

The previous Docker Desktop + Cloudflare Tunnel setup ($0/mo) was decommissioned in April 2026.

---

## Prerequisites

### Accounts

1. **Cloudflare** — Managing `bettermind.buzz`, `clinicianassist.space`, `casey.care` (Account ID: `6972abee15196f3597aba8a1fd83b771`)
2. **Fly.io** — Running `bettermind-crm-api` and `casey-demo-backend` (personal org)
3. **Neon** — Projects: `bettermind-crm` (this app) and `casey-demo`

### CLI Tools (already installed)

```powershell
# Verify (both already installed)
wrangler --version    # 4.83.0
fly version           # v0.4.36
```

If you need to re-authenticate:

```powershell
# Cloudflare: use API token (OAuth is unreliable)
$env:CLOUDFLARE_API_TOKEN = "your-token"  # Create at dash.cloudflare.com/profile/api-tokens
$env:CLOUDFLARE_ACCOUNT_ID = "6972abee15196f3597aba8a1fd83b771"

# Fly.io
fly auth login          # Opens browser for Fly.io auth
```

---

## Phase 1: Neon PostgreSQL Setup

### 1.1 Create Neon Project

1. Go to https://console.neon.tech
2. Create new project: **bettermind-crm**
3. Region: **US East (Ohio)** — closest to Fly.io's default `iad` region
4. Database name: `bettermind_crm`
5. Note the connection string (use the **direct** endpoint, not the pooler)

> **Important:** Use the direct Neon endpoint (without `-pooler` in the hostname). The pooler endpoint uses PgBouncer in transaction mode, which causes `no schema has been selected to create in` errors during `init_schema()`.

### 1.2 Export from Local PostgreSQL

```powershell
# Dump from local Docker PostgreSQL
docker exec bettermind-db pg_dump -U bettermind -d bettermind_crm `
  --no-owner --no-acl --no-privileges -F c -f /tmp/bettermind_dump.dump

# Copy dump out of Docker
docker cp bettermind-db:/tmp/bettermind_dump.dump .\bettermind_dump.dump
```

### 1.3 Import to Neon

```powershell
# Restore to Neon using the DIRECT endpoint (not pooler)
# Run pg_restore from within Docker if not installed locally
docker exec bettermind-db pg_restore --no-owner --no-acl --no-privileges `
  -d "postgresql://neondb_owner:PASSWORD@ep-xxxxx.us-east-1.aws.neon.tech/bettermind_crm?sslmode=require" `
  /tmp/bettermind_dump.dump
```

### 1.4 Verify

```powershell
# Verify via pg8000 (Python)
python -c "import pg8000, ssl; ctx = ssl.create_default_context(); conn = pg8000.connect(user='neondb_owner', password='PASSWORD', host='ep-xxxxx-pooler.us-east-1.aws.neon.tech', database='bettermind_crm', ssl_context=ctx); print(conn.run('SELECT count(*) FROM contacts'))"
```

---

## Phase 2: Fly.io Backend Deployment

### 2.1 Create Fly App

```powershell
fly apps create bettermind-crm-api --org personal
```

### 2.2 Set Secrets

```powershell
# Database (Neon DIRECT endpoint - pg8000 format, SSL handled by database.py)
fly secrets set DATABASE_URL="postgresql+pg8000://neondb_owner:PASSWORD@ep-xxxxx.us-east-1.aws.neon.tech/bettermind_crm?sslmode=require" -a bettermind-crm-api

# Auth token secret (use the same one from your current deployment, or generate new)
fly secrets set TOKEN_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')" -a bettermind-crm-api
```

> **Important:** The `DATABASE_URL` must use the **direct** Neon endpoint (no `-pooler` in hostname). The `database.py` `_get_direct_pg_engine()` function detects `sslmode=` or `neon.tech` in the URL and configures SSL automatically via `pg8000`'s `ssl_context`.

### 2.3 Deploy

```powershell
fly deploy -a bettermind-crm-api
```

This uses `fly.toml` and `Dockerfile.fly` in the project root.

### 2.4 Verify

```powershell
fly status -a bettermind-crm-api
curl https://bettermind-crm-api.fly.dev/api/stats
```

---

## Phase 3: Cloudflare Pages Frontend

### 3.1 Build Frontend

```powershell
cd frontend
npm run build
```

The build uses `VITE_API_BASE_URL` env var. For production, this is set to the Fly.io backend URL.

### 3.2 Deploy to Cloudflare Pages

Use the deploy script (requires `CLOUDFLARE_API_TOKEN` env var):

```powershell
$env:CLOUDFLARE_API_TOKEN = "your-token"
.\deploy-cf-frontend.ps1
```

Or manually:

```powershell
$env:CLOUDFLARE_API_TOKEN = "your-token"
$env:CLOUDFLARE_ACCOUNT_ID = "6972abee15196f3597aba8a1fd83b771"
$env:VITE_API_BASE_URL = "https://bettermind-crm-api.fly.dev"
cd frontend
npm run build
npx wrangler pages deploy dist --project-name bettermind-crm --commit-dirty=true --branch main
```

Production URL: `https://bettermind-crm.pages.dev`

### 3.3 Custom Domain (bettermind.buzz)

The `bettermind.buzz` CNAME record points to `bettermind-crm.pages.dev` (zone ID: `584148fc5c70e85ebe48a77d8b6ae3a2`). SSL is provisioned automatically by Cloudflare.

---

## Phase 4: Wire Together

### 4.1 CORS

The `fly.toml` sets `ALLOWED_ORIGINS` to include all frontend URLs:
- `https://bettermind.buzz`
- `https://bettermind-crm.pages.dev`
- `http://localhost:5173` (dev)

### 4.2 Verify End-to-End

1. Open `https://bettermind.buzz`
2. Login with `jess@clinicianassist.ai`
3. Verify contacts load
4. Test category tabs (Investors, Legislators, etc.)
5. Test creating/editing a contact

---

## Phase 5: Decommission Local Docker (Completed April 25, 2026)

```powershell
# Stop and remove local containers
docker-compose down

# Remove the Cloudflare Tunnel service (requires admin)
Start-Process -FilePath "cloudflared" -ArgumentList "service","uninstall" -Verb RunAs -Wait

# The pgdata Docker volume is kept as a safety backup
# To remove later: docker volume rm crm_pgdata
```

---

## Deploy Scripts

| Script | Purpose |
|--------|---------|
| `deploy-fly-backend.ps1` | Deploy backend to Fly.io |
| `deploy-cf-frontend.ps1` | Build + deploy frontend to Cloudflare Pages |

---

## Rollback

### Frontend
Cloudflare Pages keeps all deployments. Rollback in the dashboard, or redeploy a previous build.

### Backend
```powershell
fly releases -a bettermind-crm-api         # List releases
fly deploy --image <previous-image> -a bettermind-crm-api  # Rollback
```

### Database
Neon has point-in-time restore (branching). Create a branch before risky migrations.

---

## Differences from Local Docker Setup

| Aspect | Local Docker | Cloud (CF + Fly.io + Neon) |
|--------|-------------|---------------------------|
| Frontend hosting | Docker (FastAPI serves static) | Cloudflare Pages (global CDN) |
| Backend hosting | Docker Desktop | Fly.io (256MB container) |
| Database | Docker PostgreSQL 16 | Neon PostgreSQL (serverless) |
| DNS/SSL | Cloudflare Tunnel | Cloudflare Pages + Fly.io TLS |
| Deploy method | `docker-compose up` | `fly deploy` + `wrangler pages deploy` |
| Cost | $0 (uses your PC) | ~$3-5/mo |
| Uptime | Only when PC is on | 24/7 |
| Backups | `backup-crm.ps1` | Neon auto-backup + branching |

---

## Troubleshooting

### Database connection fails

- Neon requires SSL. The `DATABASE_URL` must include `sslmode=require` or the pg8000 SSL parameter.
- The backend `database.py` `_get_direct_pg_engine()` detects `sslmode=` or `neon.tech` in the URL and auto-configures SSL.
- **Use the direct Neon endpoint** (no `-pooler` in hostname). The pooler causes `no schema has been selected to create in` errors.

### CORS errors

- Check `ALLOWED_ORIGINS` in `fly.toml` includes the exact frontend URL (no trailing slash).
- The backend also has `allow_origin_regex` for `localhost` and `127.0.0.1` on any port (for dev/preview).
- **Cold starts can cause CORS failures.** Set `auto_stop_machines = false` and `min_machines_running = 1` in `fly.toml` to keep at least one machine warm.

### 401 on all API calls
- Ensure `TOKEN_SECRET` on Fly.io matches what was used to create existing tokens.
- If you change `TOKEN_SECRET`, all existing tokens are invalidated — users must re-login.

### Frontend shows blank page
- Check browser console for API URL errors.
- Verify `VITE_API_BASE_URL` was set correctly at build time.
