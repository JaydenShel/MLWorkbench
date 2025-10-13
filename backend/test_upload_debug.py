#!/usr/bin/env python3
"""
Debug script to test the upload route and check database persistence.
"""

import requests
import pandas as pd
from db import SessionLocal
from models import Dataset

def test_upload_and_database():
    """Test upload route and verify database persistence"""
    
    # Create a sample CSV
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'city': ['New York', 'London', 'Tokyo']
    })
    
    # Convert to CSV bytes
    csv_content = df.to_csv(index=False).encode('utf-8')
    
    # Check database before upload
    db = SessionLocal()
    datasets_before = db.query(Dataset).all()
    print(f"Datasets before upload: {len(datasets_before)}")
    db.close()
    
    # Test the upload endpoint
    url = "http://localhost:8000/datasets/upload"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    
    try:
        print("Uploading CSV...")
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Upload successful!")
            print(f"Dataset ID: {data['dataset_id']}")
            
            # Check database after upload
            db = SessionLocal()
            datasets_after = db.query(Dataset).all()
            print(f"Datasets after upload: {len(datasets_after)}")
            
            # Look for the specific dataset
            target_dataset = db.query(Dataset).filter(Dataset.id == data['dataset_id']).first()
            if target_dataset:
                print("✅ Dataset found in database!")
                print(f"Filename: {target_dataset.filename}")
                print(f"Rows: {target_dataset.rows}")
                print(f"Columns: {target_dataset.columns}")
            else:
                print("❌ Dataset not found in database!")
                print("All datasets:")
                for d in datasets_after:
                    print(f"- {d.id}: {d.filename}")
            
            db.close()
        else:
            print("❌ Upload failed!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload_and_database()
