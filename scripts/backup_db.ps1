# Резервная копия SQLite-базы (Windows / PowerShell).
# Использование: .\scripts\backup_db.ps1

param(
    [string]$DbPath = $env:DB_PATH,
    [string]$BackupDir = ".\backups"
)

if (-not $DbPath) {
    $DbPath = Join-Path $PSScriptRoot "..\bot_database.db" | Resolve-Path
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupDir "bot_database_$timestamp.db"

$backupSql = ".backup '$($backupFile -replace '\\', '/')'"
sqlite3 $DbPath $backupSql
Write-Host "Backup saved: $backupFile"

Get-ChildItem $BackupDir -Filter "bot_database_*.db" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 14 |
    Remove-Item -Force
