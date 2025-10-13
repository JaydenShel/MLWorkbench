"""
Initialize the database with tables.
This script should be run inside the Docker container.
"""

import sys
import os
from sqlalchemy import text

# Add the current directory to Python path
sys.path.append('/app')

from db import engine, Base
from models import Dataset, ModelRun

def create_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            if "sqlite" in str(engine.url):
                # SQLite verification
                result = conn.execute(text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """))
                tables = [row[0] for row in result]
                print(f"Created tables: {tables}")
            else:
                # PostgreSQL verification
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result]
                print(f"Created tables: {tables}")
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_tables()
