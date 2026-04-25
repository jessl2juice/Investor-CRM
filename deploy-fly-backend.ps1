# BetterMind CRM - Deploy Backend to Fly.io
# Usage: .\deploy-fly-backend.ps1

Write-Host "Deploying BetterMind CRM backend to Fly.io..." -ForegroundColor Cyan

# Verify fly CLI is available
if (-not (Get-Command fly -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: fly CLI not found. Install from https://fly.io/docs/flyctl/install/" -ForegroundColor Red
    exit 1
}

# Deploy using fly.toml config
fly deploy -a bettermind-crm-api

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Backend deployed successfully!" -ForegroundColor Green
    Write-Host "API URL: https://bettermind-crm-api.fly.dev" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verify:" -ForegroundColor Yellow
    Write-Host "  fly status -a bettermind-crm-api"
    Write-Host "  curl https://bettermind-crm-api.fly.dev/api/stats"
} else {
    Write-Host "Deploy failed! Check logs:" -ForegroundColor Red
    Write-Host "  fly logs -a bettermind-crm-api"
}
