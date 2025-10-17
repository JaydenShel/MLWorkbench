# Script to manually initialize the database

echo "Initializing database tables..."

# Check if we're in Docker
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container"
    python db/init_db.py
else
    echo "Running locally - connecting to Docker database"
    # Set environment for local execution
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mlworkbench"
    python db/init_db.py
fi

echo "Database initialization complete!"
