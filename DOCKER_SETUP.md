# Docker Setup Guide for FarmWise

## Quick Start

### Prerequisites
- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

### Start the Application

```bash
# Build and start all services
docker-compose up -d

# Create superuser (first time only)
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Access Services

| Service | URL |
|---------|-----|
| Django App | http://localhost:8000 |
| Admin Panel | http://localhost:8000/admin |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

**Default Admin Credentials:**
- Username: (created during `createsuperuser`)
- Password: (created during `createsuperuser`)

## Services Included

### Web (Django)
- Django application with Daphne (ASGI server)
- Automatic migrations on startup
- Static file collection
- Hot reload for development

### PostgreSQL Database
- Version: 15-alpine
- Database: `farmwise`
- User: `farmwise_user`
- Password: `farmwise_password`
- Port: 5432

### Redis
- In-memory cache & message broker
- Used by Celery
- Port: 6379

### Celery Worker
- Background task processing
- Connected to Redis broker
- Processes long-running tasks asynchronously

### Celery Beat
- Scheduled task scheduler
- Runs periodic tasks from `django_celery_beat`

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
```

### Run Management Commands
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Create migrations
docker-compose exec web python manage.py makemigrations

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Django shell
docker-compose exec web python manage.py shell
```

### Stop and Clean
```bash
# Stop services (keep data)
docker-compose stop

# Stop and remove containers (keep volumes)
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

### Rebuild Services
```bash
# Rebuild containers after code changes
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build web
```

## Development Workflow

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Create migrations:**
   ```bash
   docker-compose exec web python manage.py makemigrations
   ```

3. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Create superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access app:**
   - Open http://localhost:8000
   - Admin: http://localhost:8000/admin

6. **Make code changes:**
   - Code changes are automatically reflected (hot reload)
   - No need to restart unless you add new packages

7. **Add dependencies:**
   ```bash
   # Install in container
   docker-compose exec web pip install package-name
   
   # Update requirements.txt
   pip freeze > requirements.txt
   
   # Rebuild container
   docker-compose up -d --build web
   ```

## Environment Configuration

Edit `docker-compose.yml` to change:
- Database credentials (`POSTGRES_PASSWORD`, `POSTGRES_USER`)
- Redis settings
- Django `SECRET_KEY` (generate new one in production)
- Debug mode (`DEBUG: "True"`)

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs web

# Restart service
docker-compose restart web
```

### Database connection error
```bash
# Check if db is healthy
docker-compose ps

# Restart database
docker-compose restart db
docker-compose restart web
```

### Static files not loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Port already in use
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Maps 8001 on host to 8000 in container
```

### Permission denied
```bash
# Fix permissions (Linux/Mac)
sudo chmod 777 -R ..
```

## Production Deployment

For production, use the `Dockerfile` and environment variables:

```bash
docker build -t farmwise:latest .
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e DEBUG="False" \
  -e DATABASE_URL="postgresql://..." \
  farmwise:latest
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Django + Docker Guide](https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/modwsgi/)
- [Celery Documentation](https://docs.celeryproject.io/)
