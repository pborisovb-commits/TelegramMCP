$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
docker run --rm -i --env-file "$PSScriptRoot/.env" --mount "type=bind,source=$PSScriptRoot/td_data,target=/data" mcptg-local:0.1
exit $LASTEXITCODE
