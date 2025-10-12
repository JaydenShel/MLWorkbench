# Database Setup Guide

## Quick Setup

### 1. Start Docker Services
```bash
# From the project root directory
docker-compose up -d
```

### 2. Initialize Database Tables
```bash
# Option A: Run inside Docker container
docker-compose exec backend python setup_db.py

# Option B: Run locally (if you have PostgreSQL running)
python setup_db.py
```

### 3. Verify Tables Created
```bash
# Connect to the database
docker-compose exec db psql -U postgres -d mlworkbench

# In PostgreSQL shell:
\dt
# You should see: datasets, model_runs
```

## Manual Database Connection

If you want to connect to the database manually:

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d mlworkbench

# Or from your local machine (if port 5432 is exposed)
psql -h localhost -p 5432 -U postgres -d mlworkbench
```

## Troubleshooting

### Tables Not Created?
1. Make sure Docker containers are running: `docker-compose ps`
2. Check database logs: `docker-compose logs db`
3. Try running the setup script: `python setup_db.py`

### Connection Issues?
1. Verify database is running: `docker-compose exec db pg_isready`
2. Check if port 5432 is accessible
3. Verify credentials in docker-compose.yml

## Environment Variables

The database connection uses these defaults:
- **Host**: `db` (Docker) or `localhost` (local)
- **Port**: `5432`
- **Database**: `mlworkbench`
- **User**: `postgres`
- **Password**: `postgres`
