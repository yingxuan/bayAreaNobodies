# Production deployment script for Bay Area Nobodies (PowerShell)

Write-Host "🚀 Starting production deployment..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with required environment variables."
    Write-Host "See DEPLOYMENT.md for details."
    exit 1
}

# Check if docker-compose.prod.yml exists
if (-not (Test-Path docker-compose.prod.yml)) {
    Write-Host "❌ Error: docker-compose.prod.yml not found!" -ForegroundColor Red
    exit 1
}

# Build and start services
Write-Host "📦 Building and starting services..." -ForegroundColor Yellow
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run database migrations
Write-Host "🗄️  Running database migrations..." -ForegroundColor Yellow
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Migration failed or already up to date" -ForegroundColor Yellow
}

# Check service status
Write-Host "✅ Checking service status..." -ForegroundColor Yellow
docker compose -f docker-compose.prod.yml ps

Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Services are running:"
Write-Host "  - API: http://localhost:8000"
Write-Host "  - Web: http://localhost:3000"
Write-Host "  - API Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  docker compose -f docker-compose.prod.yml logs -f"

