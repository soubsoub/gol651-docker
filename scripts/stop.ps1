<#
=============================================================================
GOL651 - Stop the environment. NO DATA IS DELETED.
=============================================================================
Usage:  .\scripts\stop.ps1
Stops and removes the containers of all services (including the optional
profiles). The MySQL database (Docker volume) and your files are kept.
Equivalent manual command:  docker compose --profile marimo --profile web down
=============================================================================
#>
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host '+ docker compose --profile marimo --profile web down'
& docker compose --profile marimo --profile web down
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ''
Write-Host 'Stopped. MySQL data, notebooks and data\ files are kept.'
Write-Host 'Start again with:  .\scripts\start.ps1'
