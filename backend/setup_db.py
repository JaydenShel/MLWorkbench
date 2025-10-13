"""
Database setup script that works both locally and in Docker
"""

import os
import sys
from sqlalchemy import create_engine, text

def setup_database():
    """Setup database with proper connection"""
    
    # Determine database URL based on environment
    if os.path.exists('/.dockerenv'):
        # Running in Docker
        database_url = "postgresql://postgres:postgres@db:5432/mlworkbench"
        print("Running in Docker - connecting to db service")
    else:
        # Running locally
        database_url = "postgresql://postgres:postgres@localhost:5432/mlworkbench"
        print("Running locally - connecting to localhost")
    
    print(f"Database URL: {database_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        print("Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"Connected to PostgreSQL: {version}")
        
        # Import and create tables
        print("Creating tables...")
        from db import Base
        from models import Dataset, ModelRun
        
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"Created tables: {tables}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
