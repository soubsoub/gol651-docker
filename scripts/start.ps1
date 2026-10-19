<#
=============================================================================
GOL651 - Start the environment (thin wrapper around "docker compose")
=============================================================================
Usage (PowerShell, from the project folder):
  .\scripts\start.ps1               default services: mysql, phpmyadmin, jupyter
  .\scripts\start.ps1 marimo        + Marimo
  .\scripts\start.ps1 web           + Streamlit, FastAPI, Flask
  .\scripts\start.ps1 marimo web    + both
  .\scripts\start.ps1 all           everything
If Windows blocks scripts:
  powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
Equivalent manual command:  docker compose [--profile ...] up -d --wait
The image is built automatically on the first start. After updating the
repository, rebuild it once with:  docker compose build
=============================================================================
#>
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Options = @())

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path '.env')) {
    Write-Host 'ERROR: .env not found. Run:  Copy-Item .env.example .env   then edit the passwords.'
    exit 1
}

$profileArgs = @()
foreach ($opt in $Options) {
    switch ($opt) {
        'marimo' { $profileArgs += @('--profile', 'marimo') }
        'web'    { $profileArgs += @('--profile', 'web') }
        'all'    { $profileArgs = @('--profile', 'marimo', '--profile', 'web') }
        default  { Write-Host "Unknown option: $opt  (use: marimo, web, all)"; exit 2 }
    }
}

$dockerArgs = @('compose') + $profileArgs + @('up', '-d', '--wait')
Write-Host ('+ docker ' + ($dockerArgs -join ' '))
& docker @dockerArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

function Get-Port([string]$Name, [string]$Default) {
    $line = Get-Content '.env' | Where-Object { $_ -match "^$Name=" } | Select-Object -Last 1
    if ($line) {
        $value = ($line -split '=', 2)[1].Trim()
        if ($value) { return $value }
    }
    return $Default
}

$profiles = $profileArgs -join ' '
Write-Host ''
Write-Host 'GOL651 is ready:'
Write-Host ('  Jupyter Notebook  http://localhost:' + (Get-Port 'JUPYTER_PORT' '8888'))
Write-Host ('  JupyterLab        http://localhost:' + (Get-Port 'JUPYTER_PORT' '8888') + '/lab')
Write-Host ('  phpMyAdmin        http://localhost:' + (Get-Port 'PHPMYADMIN_PORT' '8080'))
Write-Host ('  MySQL (Workbench) 127.0.0.1:' + (Get-Port 'MYSQL_PORT' '3306'))
if ($profiles -match 'marimo') {
    Write-Host ('  Marimo            http://localhost:' + (Get-Port 'MARIMO_PORT' '2718'))
}
if ($profiles -match 'web') {
    Write-Host ('  Streamlit         http://localhost:' + (Get-Port 'STREAMLIT_PORT' '8501'))
    Write-Host ('  FastAPI           http://localhost:' + (Get-Port 'FASTAPI_PORT' '8000') + '/docs')
    Write-Host ('  Flask             http://localhost:' + (Get-Port 'FLASK_PORT' '5000'))
}
