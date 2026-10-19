<#
=============================================================================
GOL651 - FULL MySQL RESET (DELETES THE MYSQL DATABASE)
=============================================================================
Usage:  .\scripts\reset.ps1
Deletes the Docker volume that stores MySQL, then starts again: MySQL is
re-initialized from mysql\init\ (fresh gol651 and gol651_exercises).
NOT deleted: notebooks, code, and files in data\sqlite and data\duckdb.
To repair only gol651_exercises, prefer: .\scripts\restore-exercises.ps1
Equivalent manual commands:
  docker compose --profile marimo --profile web down -v
  docker compose up -d --wait
=============================================================================
#>
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host 'WARNING: This deletes the Docker-managed MySQL database volume and its stored data.'
Write-Host '         Everything in gol651 and gol651_exercises will be lost.'
Write-Host '         Notebooks, code and data\sqlite, data\duckdb files are NOT affected.'
$answer = Read-Host 'Type yes to continue'
if ($answer -ne 'yes') {
    Write-Host 'Cancelled. Nothing was deleted.'
    exit 1
}

Write-Host '+ docker compose --profile marimo --profile web down -v'
& docker compose --profile marimo --profile web down -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host '+ docker compose up -d --wait'
& docker compose up -d --wait
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ''
Write-Host 'MySQL was re-initialized. Default services are running.'
