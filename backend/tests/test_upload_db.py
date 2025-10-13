import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app
from routers.upload_router import get_storage, get_db


@pytest.fixture
def client():
    """Create a test client with dependency overrides"""
    def override_get_storage():
        mock_storage = MagicMock()
        # Make save_bytes an async method that returns a tuple
        async def mock_save_bytes(filename, content):
            return ("file://test/test.csv", len(content))
        mock_storage.save_bytes = mock_save_bytes
        return mock_storage
    
    def override_get_db():
        mock_db = MagicMock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        return mock_db
    
    app.dependency_overrides[get_storage] = override_get_storage
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


class TestUploadWithDatabase:
    """Test cases for upload route with database integration"""

    def test_upload_csv_saves_to_database(self, client):
        """Test that CSV upload saves metadata to database"""
        import pandas as pd
        
        # Create sample CSV content
        df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['New York', 'London', 'Tokyo']
        })
        csv_content = df.to_csv(index=False).encode('utf-8')
        
        # Test upload
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = client.post("/datasets/upload", files=files)
        
        # Debug: Print response if it's not 200
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "dataset_id" in data
        assert "uri" in data
        assert "columns" in data
        assert "rows" in data
        assert data["columns"] == ["name", "age", "city"]
        assert data["rows"] == 3

    def test_upload_csv_validation_errors(self, client):
        """Test that validation errors are handled properly"""
        # Test with non-CSV file
        files = {"file": ("test.txt", b"not a csv", "text/plain")}
        response = client.post("/datasets/upload", files=files)
        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]

    def test_upload_csv_response_structure(self, client):
        """Test that the response has the correct structure"""
        import pandas as pd
        
        # Create sample CSV content
        df = pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6],
            'target': [7, 8, 9]
        })
        csv_content = df.to_csv(index=False).encode('utf-8')
        
        # Test upload
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = client.post("/datasets/upload", files=files)
        
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["dataset_id", "uri", "size_bytes", "columns", "rows"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(data["dataset_id"], str)
        assert isinstance(data["uri"], str)
        assert isinstance(data["size_bytes"], int)
        assert isinstance(data["columns"], list)
        assert isinstance(data["rows"], int)
        
        # Check values
        assert data["columns"] == ["feature1", "feature2", "target"]
        assert data["rows"] == 3
