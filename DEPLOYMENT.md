# Deployment Guide

This guide covers deploying the Bay Area Nobodies application to production.

## Prerequisites

- Docker and Docker Compose installed
- Environment variables configured (see `.env.example`)
- Domain name and SSL certificate (for production)
- Database backup strategy

## Production Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=bayareanobodies

# API Keys (Required)
GOOGLE_CSE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_search_engine_id
SECRET_KEY=your-strong-secret-key-change-this

# API Keys (Optional)
FINNHUB_API_KEY=your_finnhub_key
GEMINI_API_KEY=your_gemini_key
GOOGLE_MAPS_API_KEY=your_maps_key
DAILY_CSE_BUDGET=1000

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Important**: 
- Use strong, unique passwords for `POSTGRES_PASSWORD` and `SECRET_KEY`
- Never commit `.env` file to version control
- Use environment-specific values for production

## Deployment Steps

### 1. Build and Start Services

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build
```

### 2. Initialize Database

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Seed initial data (optional)
docker compose -f docker-compose.prod.yml exec api python seed.py
```

### 3. Verify Deployment

Check that all services are running:

```bash
docker compose -f docker-compose.prod.yml ps
```

Check logs:

```bash
# API logs
docker compose -f docker-compose.prod.yml logs -f api

# Web logs
docker compose -f docker-compose.prod.yml logs -f web
```

### 4. Health Checks

- API Health: `http://your-server:8000/health`
- API Docs: `http://your-server:8000/docs`
- Frontend: `http://your-server:3000`

## Production Considerations

### Reverse Proxy (Nginx/Traefik)

For production, use a reverse proxy in front of your services:

**Nginx Example** (`/etc/nginx/sites-available/bayareanobodies`):

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL/TLS

Use Let's Encrypt with Certbot:

```bash
sudo certbot --nginx -d yourdomain.com
```

### Database Backups

Set up automated backups:

```bash
# Backup script
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres bayareanobodies > backup_$(date +%Y%m%d).sql

# Restore
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres bayareanobodies < backup_20240101.sql
```

### Monitoring

Consider adding monitoring services:

- **Health checks**: Use `/health` endpoint
- **Log aggregation**: ELK stack, Loki, or CloudWatch
- **Metrics**: Prometheus + Grafana
- **Uptime monitoring**: UptimeRobot, Pingdom

### Scaling

For high traffic, consider:

1. **Horizontal scaling**: Run multiple API instances behind a load balancer
2. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
3. **Caching**: Use Redis for caching (already configured)
4. **CDN**: Use CloudFlare or AWS CloudFront for static assets

### Security

1. **Firewall**: Only expose ports 80/443
2. **Secrets**: Use Docker secrets or a secrets manager (AWS Secrets Manager, HashiCorp Vault)
3. **Updates**: Regularly update dependencies and base images
4. **Rate limiting**: Implement rate limiting on API endpoints
5. **CORS**: Configure CORS properly for production domains

## Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart services
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations if needed
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## Rollback

If you need to rollback:

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Checkout previous version
git checkout <previous-commit>

# Rebuild and start
docker compose -f docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check service status
docker compose -f docker-compose.prod.yml ps
```

### Database connection errors

- Verify `DATABASE_URL` in `.env`
- Check PostgreSQL is healthy: `docker compose -f docker-compose.prod.yml exec postgres pg_isready`
- Verify network connectivity between containers

### Out of memory

- Increase Docker memory limits
- Consider using a managed database service
- Optimize application code

### High API usage

- Check Redis cache is working
- Review `DAILY_CSE_BUDGET` setting
- Monitor API quota usage

## Cloud Platform Deployments

### AWS (ECS/EKS)

- Use ECS Fargate or EKS for container orchestration
- Use RDS for PostgreSQL
- Use ElastiCache for Redis
- Use Application Load Balancer for routing

### Google Cloud Platform

- Use Cloud Run for serverless containers
- Use Cloud SQL for PostgreSQL
- Use Memorystore for Redis
- Use Cloud Load Balancing

### Azure

- Use Azure Container Instances or AKS
- Use Azure Database for PostgreSQL
- Use Azure Cache for Redis
- Use Application Gateway

### DigitalOcean

- Use App Platform or Droplets with Docker
- Use Managed Databases
- Use Load Balancers

## Support

For issues or questions, check:
- Application logs: `docker compose -f docker-compose.prod.yml logs`
- API documentation: `http://your-server:8000/docs`
- README.md for general information

