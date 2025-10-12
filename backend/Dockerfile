# Use a slim Python base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system deps (for psycopg2, pandas, etc.)
RUN apt-get update && apt-get install -y gcc libpq-dev

# Copy dependency files first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/mlworkbench

# Expose FastAPI port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for database..."\n\
sleep 10\n\
echo "Initializing database..."\n\
python init_db.py\n\
echo "Starting FastAPI server..."\n\
uvicorn app:app --host 0.0.0.0 --port 8000' > /app/start.sh && chmod +x /app/start.sh

# Start with database initialization
CMD ["/app/start.sh"]
