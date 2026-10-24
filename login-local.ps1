$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force td_data | Out-Null
docker run --rm -it --name mcptg-login --env-file "$PSScriptRoot/.env" --mount "type=bind,source=$PSScriptRoot/td_data,target=/data" mcptg-local:0.1 python scripts/login.py --qr @args
Read-Host 'Press Enter to close'
