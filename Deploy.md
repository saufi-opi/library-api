# Deployment Guide

This guide explains how to deploy the Library API using Docker Compose with Traefik reverse proxy.

## Architecture

The stack includes:
- **Traefik**: Reverse proxy and load balancer (ports 80, 8080)
- **PostgreSQL 17**: Database with persistent storage
- **Redis 7**: Caching and rate limiting
- **Backend**: FastAPI application (4 workers)

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- `.env` file configured (copy from `.env.example`)

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# At minimum, change these:
# - POSTGRES_PASSWORD
# - SECRET_KEY
# - FIRST_SUPERUSER_PASSWORD
```

### 3. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Access the Application

- **API**: http://domain/api/v1/docs
- **API Health**: http://domain/health
- **Traefik Dashboard**: http://domain:8080

## Service Details

### Backend Service

The backend automatically:
1. Waits for database to be healthy
2. Runs Alembic migrations
3. Creates initial superuser
4. Starts Uvicorn with 4 workers

Health check endpoint: `http://localhost:8000/health`

### Database (PostgreSQL)

- Image: `postgres:17`
- Port: 5432 (internal)
- Data: Persistent volume `app-db-data`
- Health check: `pg_isready`

### Redis

- Image: `redis:7-alpine`
- Port: 6379 (internal)
- Data: Persistent volume `app-redis-data`
- Persistence: Saves to disk every 60 seconds if 1+ keys changed

### Traefik

- **Port 80**: HTTP traffic (routes to backend)
- **Port 8080**: Dashboard and API

#### Routing Configuration

**Production** (with custom domain):
- Set `DOMAIN` in `.env`
- Matches: Your custom domain
- Access: http://yourdomain.com

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild backend after code changes
docker-compose up -d --build backend

# View logs
docker-compose logs -f              # All services
docker-compose logs -f backend      # Backend only
docker-compose logs -f traefik      # Traefik only

# Execute commands in backend
docker-compose exec backend bash
docker-compose exec backend python -c "from src.core.config import settings; print(settings.API_V1_STR)"

# Database access
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Redis access
docker-compose exec redis redis-cli

# Check service health
docker-compose ps

# Restart a service
docker-compose restart backend

# Clean up everything (including volumes)
docker-compose down -v
```

## Migrations

Migrations run automatically on startup. To run manually:

```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic revision --autogenerate -m "description"
```

## Troubleshooting

### Backend fails to start

Check logs:
```bash
docker-compose logs backend
```

Common issues:
- Database not ready: Wait for db health check to pass
- Missing .env variables: Ensure all required vars are set
- Port conflicts: Check if port 80 or 8080 is already in use

### Database connection issues

```bash
# Check database is running
docker-compose ps db

# Test database connection
docker-compose exec db pg_isready -U $POSTGRES_USER

# Check backend can reach database
docker-compose exec backend python src/pre_start.py
```

### Cannot access API

1. Check backend is healthy:
   ```bash
   docker-compose ps backend
   curl http://localhost:8000/health
   ```

2. Check Traefik routing:
   ```bash
   docker-compose logs traefik
   # Visit http://traefik.domain for dashboard
   ```

3. Verify network connectivity:
   ```bash
   docker-compose exec backend ping db
   docker-compose exec backend ping redis
   ```

### Reset everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all data
rm -rf volumes/

# Start fresh
docker-compose up -d --build
```

## Production Deployment

For production:

1. **Set environment variables**:
   ```bash
   DOMAIN=api.yourdomain.com
   ENVIRONMENT=production
   SECRET_KEY=<strong-random-key>
   POSTGRES_PASSWORD=<strong-password>
   FIRST_SUPERUSER_PASSWORD=<strong-password>
   ```

2. **Enable HTTPS** (add to traefik command in docker-compose.yml):
   ```yaml
   - --entrypoints.https.address=:443
   - --certificatesresolvers.letsencrypt.acme.email=your@email.com
   - --certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json
   - --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=http
   ```

   Add volume:
   ```yaml
   volumes:
     - ./letsencrypt:/letsencrypt
   ```

3. **Disable insecure API**:
   Replace `--api.insecure=true` with:
   ```yaml
   - --api=true
   ```

4. **Add basic auth to dashboard**:
   ```bash
   # Generate password hash
   htpasswd -nb admin yourpassword

   # Add to traefik labels
   - traefik.http.routers.dashboard.middlewares=auth
   - traefik.http.middlewares.auth.basicauth.users=admin:$$apr1$$...
   ```

5. **Backup volumes regularly**:
   ```bash
   docker run --rm -v app-db-data:/data -v $(pwd):/backup \
     alpine tar czf /backup/db-backup.tar.gz /data
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DOMAIN` | Domain name for Traefik routing | `localhost` | No |
| `PROJECT_NAME` | Project name | - | Yes |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `POSTGRES_USER` | Database user | - | Yes |
| `POSTGRES_PASSWORD` | Database password | - | Yes |
| `POSTGRES_DB` | Database name | - | Yes |
| `FIRST_SUPERUSER` | Admin email | - | Yes |
| `FIRST_SUPERUSER_PASSWORD` | Admin password | - | Yes |

## Monitoring

### Check Service Health

```bash
# All services
docker-compose ps

# Backend health endpoint
curl http://localhost/health

# Database
docker-compose exec db pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

### View Metrics

Traefik dashboard: http://traefik.domain
- Active routers and services
- Request metrics
- Health check status

## Scaling

Scale backend workers:

```bash
# In docker-compose.yml, add:
docker-compose up -d --scale backend=3
```

Or modify `entrypoint.sh` to change Uvicorn workers from 4 to desired number.
