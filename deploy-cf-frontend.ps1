# BetterMind CRM - Deploy Frontend to Cloudflare Pages
# Usage: .\deploy-cf-frontend.ps1

Write-Host "Deploying BetterMind CRM frontend to Cloudflare Pages..." -ForegroundColor Cyan

# Cloudflare API Token auth (avoids flaky OAuth)
$env:CLOUDFLARE_ACCOUNT_ID = "6972abee15196f3597aba8a1fd83b771"
if (-not $env:CLOUDFLARE_API_TOKEN) {
    Write-Host "ERROR: Set CLOUDFLARE_API_TOKEN env var first." -ForegroundColor Red
    Write-Host "  Create at: https://dash.cloudflare.com/profile/api-tokens" -ForegroundColor Yellow
    Write-Host "  Permissions: Account Settings (Read) + Cloudflare Pages (Edit)" -ForegroundColor Yellow
    exit 1
}

# Set the API base URL for production build
$env:VITE_API_BASE_URL = "https://bettermind-crm-api.fly.dev"

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
Push-Location frontend
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Deploy to Cloudflare Pages
Write-Host "Deploying to Cloudflare Pages..." -ForegroundColor Yellow
npx wrangler pages deploy dist --project-name bettermind-crm --commit-dirty=true --branch main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Frontend deployed successfully!" -ForegroundColor Green
    Write-Host "URLs:" -ForegroundColor Cyan
    Write-Host "  https://bettermind-crm.pages.dev"
    Write-Host "  https://bettermind.buzz (after custom domain setup)"
} else {
    Write-Host "Deploy failed!" -ForegroundColor Red
}

Pop-Location

# Clear build env var
Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
