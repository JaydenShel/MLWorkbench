#!/usr/bin/env python3
"""
Test script to check database paths and connections.
"""

import os
from db import engine, DATABASE_URL
from sqlalchemy import text

def test_database_paths():
    """Test database paths and connections"""
    print(f"Database URL: {DATABASE_URL}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if database file exists
    if "sqlite" in DATABASE_URL:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        print(f"Database file path: {db_path}")
        print(f"Database file exists: {os.path.exists(db_path)}")
        
        if os.path.exists(db_path):
            print(f"Database file size: {os.path.getsize(db_path)} bytes")
    
    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"Tables in database: {tables}")
            
            # Check datasets table
            if 'datasets' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM datasets"))
                count = result.scalar()
                print(f"Number of datasets: {count}")
                
                # Get all datasets
                result = conn.execute(text("SELECT id, filename, rows FROM datasets"))
                datasets = result.fetchall()
                print("Datasets:")
                for dataset in datasets:
                    print(f"  - {dataset[0]}: {dataset[1]} ({dataset[2]} rows)")
            
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    test_database_paths()
