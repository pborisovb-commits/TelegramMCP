$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Install Docker Desktop and start it before setup.'
}
docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker is not running. Start Docker Desktop and retry.' }
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
    Write-Host 'Created .env. Fill in TG_API_ID and TG_API_HASH before login.'
}
New-Item -ItemType Directory -Force td_data | Out-Null
docker build -f Dockerfile.local -t mcptg-local:0.1 .
if ($LASTEXITCODE -ne 0) { throw 'Docker build failed.' }
Write-Host 'Ready. Fill .env, then run login-local.ps1 to scan the Telegram QR code.'
