#!/usr/bin/env python3
"""
Test script to verify the upload route works with a real CSV file.
"""

import requests
import pandas as pd
import io

def test_upload_csv():
    """Test uploading a CSV file to the upload endpoint"""
    
    # Create a sample CSV
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'city': ['New York', 'London', 'Tokyo']
    })
    
    # Convert to CSV bytes
    csv_content = df.to_csv(index=False).encode('utf-8')
    
    # Test the upload endpoint
    url = "http://localhost:8000/datasets/upload"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Upload successful!")
            print(f"Dataset ID: {data['dataset_id']}")
            print(f"URI: {data['uri']}")
            print(f"Size: {data['size_bytes']} bytes")
            print(f"Columns: {data['columns']}")
            print(f"Rows: {data['rows']}")
        else:
            print("❌ Upload failed!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload_csv()
