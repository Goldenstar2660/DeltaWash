#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run backend integration tests for the Hospital Dashboard

.DESCRIPTION
    This script ensures the test database exists and runs pytest in the backend container.
    Tests are automatically isolated and repeatable.

.PARAMETER TestPath
    Optional path to specific test file or test class. Defaults to all integration tests.

.PARAMETER Verbose
    Show verbose pytest output

.PARAMETER Stop
    Stop on first test failure (-x flag)

.EXAMPLE
    .\scripts\run-tests.ps1
    Run all integration tests

.EXAMPLE
    .\scripts\run-tests.ps1 -TestPath "tests/integration/test_analytics_api.py::TestUnitAnalytics"
    Run specific test class

.EXAMPLE
    .\scripts\run-tests.ps1 -Verbose -Stop
    Run with verbose output and stop on first failure
#>

param(
    [string]$TestPath = "tests/integration/",
    [switch]$Verbose,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Hospital Dashboard Test Runner" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker containers are running
Write-Host "📦 Checking Docker containers..." -ForegroundColor Yellow
$containers = docker compose -f dashboard/docker-compose.dashboard.yml ps --services --filter "status=running"
if (-not $containers -or $containers -notcontains "db" -or $containers -notcontains "backend") {
    Write-Host "❌ Docker containers are not running. Starting them..." -ForegroundColor Red
    docker compose -f dashboard/docker-compose.dashboard.yml up -d
    Start-Sleep -Seconds 5
}
Write-Host "✅ Docker containers are running" -ForegroundColor Green
Write-Host ""

# Ensure test database exists
Write-Host "🗄️  Ensuring test database exists..." -ForegroundColor Yellow
$dbCheck = docker compose -f dashboard/docker-compose.dashboard.yml exec -T db psql -U dashboard_user -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='deltawash_dashboard_test'" 2>$null
if ($dbCheck -ne "1") {
    Write-Host "Creating test database..." -ForegroundColor Yellow
    docker compose -f dashboard/docker-compose.dashboard.yml exec -T db psql -U dashboard_user -d postgres -c "CREATE DATABASE deltawash_dashboard_test;" | Out-Null
    Write-Host "✅ Test database created" -ForegroundColor Green
} else {
    Write-Host "✅ Test database exists" -ForegroundColor Green
}
Write-Host ""

# Build pytest command
$pytestArgs = @($TestPath)
if ($Verbose) {
    $pytestArgs += "-v"
}
if ($Stop) {
    $pytestArgs += "-x"
}
$pytestArgs += "--tb=short"

Write-Host "🚀 Running tests: $TestPath" -ForegroundColor Yellow
Write-Host "Command: pytest $($pytestArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

# Run tests
$testCommand = "pytest $($pytestArgs -join ' ')"
docker compose -f dashboard/docker-compose.dashboard.yml exec backend bash -c $testCommand

$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed (exit code: $exitCode)" -ForegroundColor Red
}

exit $exitCode

