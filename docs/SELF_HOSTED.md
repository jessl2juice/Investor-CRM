# Self-Hosted Deployment Guide

Run BetterMind CRM on your own machine with HTTPS access from anywhere, for **$0/month**.

## Overview

This guide covers deploying BetterMind CRM using:

- **Docker Desktop** — runs PostgreSQL 16 and the FastAPI + React app
- **Cloudflare Tunnel** — exposes the CRM to the internet with automatic HTTPS
- **Cloudflare DNS** — free-tier DNS with SSL certificate provisioning

## Prerequisites

- Windows 10/11 PC (always on, or on when you need access)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A domain name (e.g., `bettermind.buzz`) — any registrar works
- A [Cloudflare account](https://dash.cloudflare.com/sign-up) (free tier)
- Python 3.10+ (for the import script, if migrating data)

## Step 1: Start the Docker Stack

```bash
git clone https://github.com/jessl2juice/Investor-CRM.git
cd Investor-CRM
docker-compose up -d
```

This starts two containers:

| Container | Image | Purpose | Port |
|-----------|-------|---------|------|
| `bettermind-db` | `postgres:16-alpine` | PostgreSQL database | 5433 (external) → 5432 (internal) |
| `bettermind-app` | Built from `Dockerfile` | FastAPI + React app | 8080 |

Verify both are running:

```bash
docker-compose ps
```

The app should be accessible at `http://localhost:8080`.

## Step 2: Import Data (Optional)

If you have JSON backup files from a previous deployment:

```bash
python import_data.py
```

This imports organizations, contacts, interactions, deals, programs, tags, and user accounts from JSON files. See `import_data.py` for details.

If starting fresh, the app creates demo seed data automatically on first run.

## Step 3: Create a Cloudflare Tunnel

### 3a. Add your domain to Cloudflare

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Click **Add a site** → enter your domain → select the **Free** plan
3. Cloudflare will scan existing DNS records — continue through the wizard
4. Cloudflare assigns two nameservers (e.g., `desi.ns.cloudflare.com`, `walt.ns.cloudflare.com`)
5. Go to your domain registrar and **change the nameservers** to the Cloudflare ones
6. Wait for DNS propagation (5–30 minutes, up to 48 hours in rare cases)

### 3b. Create the tunnel in Cloudflare Zero Trust

1. Go to [one.dash.cloudflare.com](https://one.dash.cloudflare.com)
2. Navigate to **Networks → Connectors**
3. Click **Create a tunnel** → select **Cloudflared** → name it (e.g., `bettermind-crm`)
4. Copy the **connector token** (starts with `eyJ...`)

### 3c. Install cloudflared on Windows

Download the binary:

```powershell
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
```

Install as a Windows service (run PowerShell as Administrator):

```powershell
.\cloudflared.exe service install <YOUR_TUNNEL_TOKEN>
```

Verify the service is running:

```powershell
Get-Service cloudflared
# Status should be: Running
# StartType should be: Automatic
```

### 3d. Configure tunnel ingress via Cloudflare API

Create an API token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) with **Cloudflare Tunnel: Edit** permission.

Then configure the tunnel to route your domain to `localhost:8080`:

```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_API_TOKEN"
    "Content-Type" = "application/json"
}
$accountId = "YOUR_ACCOUNT_ID"  # Found in Cloudflare dashboard overview
$tunnelId = "YOUR_TUNNEL_ID"    # From step 3b

$body = '{"config":{"ingress":[{"hostname":"yourdomain.com","service":"http://localhost:8080"},{"service":"http_status:404"}]}}'

Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/accounts/$accountId/cfd_tunnel/$tunnelId/configurations" -Method PUT -Headers $headers -Body $body
```

### 3e. Add DNS CNAME record

Create another API token with **Zone DNS: Edit** permission, then:

```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_DNS_API_TOKEN"
    "Content-Type" = "application/json"
}
$zoneId = "YOUR_ZONE_ID"  # From Cloudflare API: /zones?name=yourdomain.com

$body = '{"type":"CNAME","name":"yourdomain.com","content":"YOUR_TUNNEL_ID.cfargotunnel.com","proxied":true}'

Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records" -Method POST -Headers $headers -Body $body
```

Or add the CNAME manually in the Cloudflare dashboard:

1. Go to your domain → **DNS** → **Records**
2. Add record: **CNAME**, Name: `@`, Target: `YOUR_TUNNEL_ID.cfargotunnel.com`, Proxy: ON

### 3f. Verify

```bash
curl https://yourdomain.com/
# Should return the BetterMind CRM HTML page
```

SSL is provisioned automatically by Cloudflare. It may take a few minutes on first setup.

## Step 4: Configure CORS Origins

Update `ALLOWED_ORIGINS` in `docker-compose.yml` to include your domain:

```yaml
ALLOWED_ORIGINS: "https://yourdomain.com,http://localhost:8080,http://localhost:5173"
```

Then restart the app:

```bash
docker-compose up -d app
```

## Step 5: Set Up Backups

### Manual backup

```powershell
.\backup-crm.ps1
# Creates C:\CRM-Backups\bettermind-YYYY-MM-DD.sql
```

### Schedule weekly backups

1. Open **Windows Task Scheduler** → Create Basic Task
2. Name: `BetterMind CRM Backup`
3. Trigger: **Weekly** (pick a day and time)
4. Action: **Start a program**
5. Program: `powershell.exe`
6. Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\backup-crm.ps1"`

The script keeps the last 12 backups and deletes older ones automatically.

### Restore from backup

```powershell
docker-compose stop app
docker exec -i bettermind-db psql -U bettermind -d postgres -c "DROP DATABASE bettermind_crm;"
docker exec -i bettermind-db psql -U bettermind -d postgres -c "CREATE DATABASE bettermind_crm;"
Get-Content C:\CRM-Backups\bettermind-YYYY-MM-DD.sql | docker exec -i bettermind-db psql -U bettermind -d bettermind_crm
docker-compose start app
```

## What Survives a Reboot

| Component | Auto-starts? | How |
|-----------|-------------|-----|
| Docker Desktop | Yes (if configured) | Settings → General → Start Docker Desktop when you sign in |
| PostgreSQL + App containers | Yes | `restart: unless-stopped` in `docker-compose.yml` |
| Cloudflare Tunnel | Yes | Installed as Windows service with `Automatic` start type |

After a reboot, the CRM should be accessible within 1–2 minutes once Docker Desktop starts.

## Troubleshooting

**Site returns 404 or "Page not found":**
- Check the tunnel is running: `Get-Service cloudflared`
- Check containers are running: `docker-compose ps`
- Verify DNS: `nslookup yourdomain.com 1.1.1.1` — should return Cloudflare IPs
- Verify tunnel config: check ingress rules via Cloudflare API

**SSL certificate errors:**
- New domains take 5–15 minutes for Cloudflare to provision SSL
- Check SSL/TLS mode in Cloudflare dashboard (should be "Flexible" or "Full")

**Cannot connect to database:**
- Check PostgreSQL container: `docker logs bettermind-db`
- Verify port 5433 is not in use: `netstat -an | findstr 5433`

**App container keeps restarting:**
- Check logs: `docker logs bettermind-app`
- Common cause: database not ready yet (healthcheck should handle this)

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Docker Desktop | Free (personal use) |
| Cloudflare free tier (DNS, Tunnel, SSL) | Free |
| Domain renewal (annual) | ~$10/year |
| Electricity (PC running 24/7) | ~$5/month |
| **Total** | **~$0–5/month** |

Compared to the previous Google Cloud deployment at **~$150/month**.

## Security Notes

- **Cloudflare Tunnel** does not expose any ports on your machine — all traffic goes through Cloudflare's network
- **HTTPS** is enforced by Cloudflare with auto-renewed certificates
- **Database** is only accessible from the Docker network (port 5433 is exposed locally for admin access but not to the internet)
- **Auth tokens** expire after 24 hours
- **Passwords** are hashed with PBKDF2 (SHA-256, random salt)

## Reference: Key Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Docker stack config (PostgreSQL + app) |
| `backup-crm.ps1` | Weekly backup script |
| `import_data.py` | Data import from JSON |
| `export_from_cloud.py` | Data export from Cloud SQL (migration) |
| `.env.example` | Environment variable template |
