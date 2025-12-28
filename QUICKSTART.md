# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- (Optional) Google Custom Search API credentials

## Setup Steps

1. **Clone and navigate to project**
```bash
cd bayAreaNobodies
```

2. **Create `.env` file** (optional - app works with mock data)
```bash
# Copy example
cp .env.example .env

# Edit and add your keys (optional for MVP)
GOOGLE_CSE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_id_here
```

3. **Start all services**
```bash
docker compose up --build
```

4. **Initialize database** (in a new terminal)
```bash
# Run migrations
docker compose exec api alembic upgrade head

# Seed default queries
docker compose exec api python seed.py
```

5. **Access the app**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## First Steps

1. **Register/Login**: Go to http://localhost:3000/login
2. **View Trending**: Check the Trending tab (may be empty initially)
3. **Add Holdings**: Go to Portfolio tab and add stock holdings
4. **Wait for Jobs**: Background jobs run hourly - check back later for trending articles

## Troubleshooting

**Database not ready?**
```bash
docker compose ps  # Check service status
docker compose logs postgres  # Check logs
```

**API errors?**
```bash
docker compose logs api  # Check API logs
```

**No trending articles?**
- Jobs run hourly - wait for the next run
- Check API logs for job execution
- Verify Google CSE credentials if using real data

## Background Jobs Schedule

- **Search Jobs**: Every hour
- **Trending Snapshots**: Every hour  
- **Coupon Search**: Daily at 6 AM
- **Digests**: 8:30 AM and 4:30 PM (PST)

Jobs start automatically when API starts.

