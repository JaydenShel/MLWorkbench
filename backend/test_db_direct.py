#!/usr/bin/env python3
"""
Test script to directly test database operations.
"""

from db import SessionLocal, engine
from models import Dataset
import uuid

def test_database():
    """Test direct database operations"""
    print("Testing database connection...")
    
    # Test connection
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test creating a dataset
    try:
        db = SessionLocal()
        
        # Create a test dataset
        dataset = Dataset(
            id=str(uuid.uuid4()),
            filename="test.csv",
            uri="file://test/test.csv",
            size_bytes=100,
            columns=["col1", "col2"],
            rows=5
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        print("✅ Dataset created successfully")
        print(f"Dataset ID: {dataset.id}")
        
        # Query all datasets
        datasets = db.query(Dataset).all()
        print(f"Total datasets in database: {len(datasets)}")
        
        for d in datasets:
            print(f"- {d.filename}: {d.rows} rows, {len(d.columns)} columns")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")

if __name__ == "__main__":
    test_database()
