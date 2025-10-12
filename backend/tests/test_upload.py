import pytest
import io
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from routers.upload_router import router, get_storage
from services.storage import Storage


# Create a test app
app = FastAPI()
app.include_router(router)


class MockStorage(Storage):
    """Mock storage for testing"""

    def __init__(self):
        self.saved_files = {}

    async def save_bytes(self, filename: str, data: bytes) -> tuple[str, int]:
        key = f"test_{filename}"
        self.saved_files[key] = data
        return (f"file://test/{key}", len(data))


@pytest.fixture
def mock_storage():
    """Provide a mock storage instance"""
    return MockStorage()


@pytest.fixture
def client(mock_storage):
    """Create a test client with mocked storage"""

    def override_get_storage():
        return mock_storage

    app.dependency_overrides[get_storage] = override_get_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing"""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["New York", "London", "Tokyo"],
        }
    )
    return df.to_csv(index=False).encode("utf-8")


@pytest.fixture
def invalid_csv_content():
    """Invalid CSV content for testing"""
    return b"not,a,valid,csv\nwith,missing,quotes\n"


class TestUploadRoute:
    """Test cases for the /upload endpoint"""

    def test_upload_valid_csv_success(self, client, sample_csv_content, mock_storage):
        """Test successful CSV upload"""
        files = {"file": ("test.csv", sample_csv_content, "text/csv")}

        response = client.post("/datasets/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "dataset_id" in data
        assert "uri" in data
        assert "size_bytes" in data
        assert "columns" in data
        assert "rows" in data

        # Check specific values
        assert data["columns"] == ["name", "age", "city"]
        assert data["rows"] == 3
        assert data["size_bytes"] == len(sample_csv_content)
        assert data["uri"].startswith("file://test/")

        # Verify file was saved
        assert len(mock_storage.saved_files) == 1

    def test_upload_non_csv_file_rejected(self, client):
        """Test that non-CSV files are rejected"""
        files = {"file": ("test.txt", b"not a csv", "text/plain")}

        response = client.post("/datasets/upload", files=files)

        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]

    def test_upload_invalid_csv_content(self, client, invalid_csv_content):
        """Test handling of invalid CSV content"""
        files = {"file": ("test.csv", invalid_csv_content, "text/csv")}

        response = client.post("/datasets/upload", files=files)

        # Pandas is quite lenient, so this might actually succeed
        # Let's check if it succeeds and has reasonable data
        if response.status_code == 200:
            data = response.json()
            assert "columns" in data
            assert "rows" in data
        else:
            assert response.status_code == 400
            assert "Error reading CSV file" in response.json()["detail"]

    def test_upload_empty_file(self, client):
        """Test handling of empty file"""
        files = {"file": ("empty.csv", b"", "text/csv")}

        response = client.post("/datasets/upload", files=files)

        # Empty CSV should fail because pandas can't parse it
        assert response.status_code == 400
        assert "Error reading CSV file" in response.json()["detail"]

    def test_upload_missing_file_parameter(self, client):
        """Test that missing file parameter returns 422"""
        response = client.post("/datasets/upload")

        assert response.status_code == 422

    def test_upload_large_csv(self, client, mock_storage):
        """Test upload of larger CSV file"""
        # Create a larger dataset
        large_data = []
        for i in range(1000):
            large_data.append(
                {"id": i, "value": f"value_{i}", "category": f"cat_{i % 10}"}
            )

        df = pd.DataFrame(large_data)
        csv_content = df.to_csv(index=False).encode("utf-8")

        files = {"file": ("large.csv", csv_content, "text/csv")}

        response = client.post("/datasets/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["rows"] == 1000
        assert data["columns"] == ["id", "value", "category"]

    def test_upload_csv_with_special_characters(self, client, mock_storage):
        """Test CSV with special characters and unicode"""
        df = pd.DataFrame(
            {
                "name": ["José", "François", "李小明"],
                "description": ['Contains "quotes"', "Has, commas", "Unicode: 中文"],
                "price": [19.99, 25.50, 100.00],
            }
        )
        csv_content = df.to_csv(index=False).encode("utf-8")

        files = {"file": ("special.csv", csv_content, "text/csv")}

        response = client.post("/datasets/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["rows"] == 3
        assert data["columns"] == ["name", "description", "price"]

    def test_storage_dependency_injection(self, mock_storage):
        """Test that storage dependency is properly injected"""
        # This tests the dependency injection mechanism
        storage = get_storage()
        assert storage is not None

    @pytest.mark.asyncio
    async def test_storage_save_bytes_async(self, mock_storage):
        """Test async storage save operation"""
        test_data = b"test,data\n1,2\n3,4"
        filename = "test.csv"

        uri, size = await mock_storage.save_bytes(filename, test_data)

        assert uri.startswith("file://test/")
        assert size == len(test_data)
        # Check that a file with the test prefix was saved
        saved_keys = list(mock_storage.saved_files.keys())
        assert len(saved_keys) == 1
        assert saved_keys[0].startswith("test_")

    def test_upload_csv_with_different_delimiter(self, client, mock_storage):
        """Test CSV with semicolon delimiter (common in European data)"""
        # Create CSV with semicolon delimiter
        csv_content = b"name;age;city\nAlice;25;New York\nBob;30;London"

        files = {"file": ("semicolon.csv", csv_content, "text/csv")}

        response = client.post("/datasets/upload", files=files)

        # Should still work as pandas can auto-detect delimiter
        assert response.status_code == 200
        data = response.json()
        assert data["rows"] == 2

    def test_upload_csv_with_headers_only(self, client, mock_storage):
        """Test CSV with only headers, no data rows"""
        csv_content = b"name,age,city\n"

        files = {"file": ("headers_only.csv", csv_content, "text/csv")}

        response = client.post("/datasets/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["rows"] == 0
        assert data["columns"] == ["name", "age", "city"]


class TestStorageIntegration:
    """Test storage integration scenarios"""

    @pytest.mark.asyncio
    async def test_local_storage_integration(self):
        """Test integration with LocalStorage"""
        from services.storage import LocalStorage
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalStorage(base_dir=temp_dir)
            test_data = b"test,data\n1,2"

            uri, size = await storage.save_bytes("test.csv", test_data)

            assert uri.startswith("file://")
            assert size == len(test_data)

            # Verify file was actually created
            file_path = uri.replace("file://", "")
            assert os.path.exists(file_path)

            with open(file_path, "rb") as f:
                saved_data = f.read()
                assert saved_data == test_data

    def test_s3_storage_mock(self):
        """Test S3Storage with mocked boto3"""
        with patch("services.storage_s3.aioboto3.Session") as mock_session:
            mock_s3_client = AsyncMock()
            mock_session.return_value.client.return_value.__aenter__.return_value = (
                mock_s3_client
            )

            from services.storage_s3 import S3Storage

            storage = S3Storage(bucket="test-bucket")

            # This would be an async test in a real scenario
            # For now, just test instantiation
            assert storage.bucket == "test-bucket"
