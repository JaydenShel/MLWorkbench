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

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
