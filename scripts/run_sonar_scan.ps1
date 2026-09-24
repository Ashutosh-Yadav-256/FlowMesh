
param (
    [string]$SonarHostUrl = $env:SONAR_HOST_URL,
    [string]$SonarToken = $env:SONAR_TOKEN,
    [switch]$SkipTests = $false
)

if (-not $SonarHostUrl) {
    $SonarHostUrl = "http://localhost:9000"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "FlowMesh Enterprise - SonarQube Code Quality & Security Scan" -ForegroundColor Cyan
Write-Host "SonarQube Host: $SonarHostUrl" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not $SkipTests) {
    Write-Host "`n[1/3] Running Python Pytest with Coverage..." -ForegroundColor Yellow
    uv run pytest --cov=apps --cov=connectors --cov=services --cov-report=xml:coverage.xml tests/ -v -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python coverage report generated at ./coverage.xml" -ForegroundColor Green
    } else {
        Write-Host "Python test suite encountered warnings/errors." -ForegroundColor Red
    }

    Write-Host "`n[2/3] Compiling Java Enterprise Worker & Generating JaCoCo Coverage..." -ForegroundColor Yellow
    if (Get-Command mvn -ErrorAction SilentlyContinue) {
        Push-Location "services/enterprise-worker"
        mvn clean test jacoco:report -B
        Pop-Location
        Write-Host "JaCoCo coverage report generated at services/enterprise-worker/target/site/jacoco/jacoco.xml" -ForegroundColor Green
    } else {
        Write-Host "Maven not found on PATH. Attempting Dockerized Maven JaCoCo execution..." -ForegroundColor Yellow
        docker run --rm -v "${PWD}/services/enterprise-worker:/app" -w /app maven:3.9.8-eclipse-temurin-17-alpine mvn clean test jacoco:report -B
        Write-Host "Dockerized JaCoCo coverage completed." -ForegroundColor Green
    }

    Write-Host "`n[3/3] Checking TypeScript / Next.js Test Coverage..." -ForegroundColor Yellow
    if (Test-Path "apps/web/node_modules") {
        Push-Location "apps/web"
        pnpm test:cov
        Pop-Location
    }
}

Write-Host "`n[4/4] Executing SonarQube Scanner..." -ForegroundColor Yellow
$SonarEnvArgs = @(
    "-e", "SONAR_HOST_URL=$SonarHostUrl"
)
if ($SonarToken) {
    $SonarEnvArgs += @("-e", "SONAR_TOKEN=$SonarToken")
}

docker run --rm `
    --network="host" `
    -v "${PWD}:/usr/src" `
    @SonarEnvArgs `
    sonarsource/sonar-scanner-cli:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSonarQube Quality Gate scan dispatched successfully!" -ForegroundColor Green
    Write-Host "View dashboard report at: $SonarHostUrl/dashboard?id=flowmesh-enterprise-orchestrator" -ForegroundColor Cyan
} else {
    Write-Host "`nSonarQube scan failed or Quality Gate condition not met." -ForegroundColor Red
}
