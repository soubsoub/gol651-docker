<#
=============================================================================
GOL651 - Restore ONLY the practice database gol651_exercises
=============================================================================
Usage:  .\scripts\restore-exercises.ps1
Rebuilds the tables, data and views of gol651_exercises from
mysql\init\teaching\. The reference database gol651 and everything else
are NOT touched. MySQL must be running.
=============================================================================
#>
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host 'This replaces all tables and data of gol651_exercises with the original version.'
$answer = Read-Host 'Type yes to continue'
if ($answer -ne 'yes') {
    Write-Host 'Cancelled. Nothing was changed.'
    exit 1
}

# Runs inside the mysql container. Written WITHOUT double quotes on purpose:
# Windows PowerShell 5.1 strips embedded double quotes from native arguments.
# 1. root drops the views (they may be owned by root on volumes created before
#    stage 2.3); 2. the course user reloads everything.
$inner = 'echo DROP VIEW IF EXISTS v_customer_sales, v_low_stock, v_order_totals | ' +
         'MYSQL_PWD=$MYSQL_ROOT_PASSWORD mysql -uroot gol651_exercises || exit 1; ' +
         'for f in /docker-entrypoint-initdb.d/teaching/0*.sql; do echo loading $f; ' +
         'MYSQL_PWD=$MYSQL_PASSWORD mysql -u$MYSQL_USER --default-character-set=utf8mb4 ' +
         'gol651_exercises < $f || exit 1; done'
& docker compose exec -T mysql sh -c $inner
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'gol651_exercises restored.'
