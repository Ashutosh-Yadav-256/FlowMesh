#!/usr/bin/env bash
set -e

SONAR_HOST_URL="${SONAR_HOST_URL:-http://localhost:9000}"
SONAR_TOKEN="${SONAR_TOKEN:-}"

echo "=========================================================="
echo "FlowMesh Enterprise - SonarQube Code Quality & Security Scan"
echo "SonarQube Host: ${SONAR_HOST_URL}"
echo "=========================================================="

echo "[1/3] Running Python Pytest with Coverage..."
uv run pytest --cov=apps --cov=connectors --cov=services --cov-report=xml:coverage.xml tests/ -v -q || true

echo "[2/3] Compiling Java Enterprise Worker & Generating JaCoCo Coverage..."
if command -v mvn &> /dev/null; then
    (cd services/enterprise-worker && mvn clean test jacoco:report -B)
else
    docker run --rm -v "$(pwd)/services/enterprise-worker:/app" -w /app maven:3.9.8-eclipse-temurin-17-alpine mvn clean test jacoco:report -B
fi

echo "[3/3] Checking TypeScript / Next.js Test Coverage..."
if [ -d "apps/web/node_modules" ]; then
    (cd apps/web && pnpm test:cov || true)
fi

echo "[4/4] Executing SonarQube Scanner..."
ENV_ARGS=("-e" "SONAR_HOST_URL=${SONAR_HOST_URL}")
if [ -n "${SONAR_TOKEN}" ]; then
    ENV_ARGS+=("-e" "SONAR_TOKEN=${SONAR_TOKEN}")
fi

docker run --rm \
    --network="host" \
    -v "$(pwd):/usr/src" \
    "${ENV_ARGS[@]}" \
    sonarsource/sonar-scanner-cli:latest

echo "SonarQube Quality Gate scan finished!"
echo "Dashboard: ${SONAR_HOST_URL}/dashboard?id=flowmesh-enterprise-orchestrator"
