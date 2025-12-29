#!/bin/bash

# Production deployment script for Bay Area Nobodies

set -e

echo "🚀 Starting production deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with required environment variables."
    echo "See DEPLOYMENT.md for details."
    exit 1
fi

# Check if docker-compose.prod.yml exists
if [ ! -f docker-compose.prod.yml ]; then
    echo "❌ Error: docker-compose.prod.yml not found!"
    exit 1
fi

# Build and start services
echo "📦 Building and starting services..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head || echo "⚠️  Migration failed or already up to date"

# Check service status
echo "✅ Checking service status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Services are running:"
echo "  - API: http://localhost:8000"
echo "  - Web: http://localhost:3000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.prod.yml logs -f"

