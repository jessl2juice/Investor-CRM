# BetterMind CRM - PostgreSQL Backup Script
# Schedule this in Windows Task Scheduler to run weekly.
# Creates a SQL dump in C:\CRM-Backups with date-stamped filename.

$backupDir = "C:\CRM-Backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

$date = Get-Date -Format "yyyy-MM-dd"
$backupFile = Join-Path $backupDir "bettermind-$date.sql"

Write-Host "Backing up BetterMind CRM database to $backupFile..."
docker exec bettermind-db pg_dump -U bettermind bettermind_crm > $backupFile

if ($LASTEXITCODE -eq 0) {
    $size = (Get-Item $backupFile).Length / 1KB
    Write-Host "Backup complete: $backupFile ($([math]::Round($size, 1)) KB)"

    # Keep only last 12 backups
    $backups = Get-ChildItem $backupDir -Filter "bettermind-*.sql" | Sort-Object LastWriteTime -Descending
    if ($backups.Count -gt 12) {
        $backups | Select-Object -Skip 12 | Remove-Item -Force
        Write-Host "Cleaned up old backups (kept last 12)"
    }
} else {
    Write-Host "ERROR: Backup failed! Is the bettermind-db container running?"
    exit 1
}
