"""
Simple tests for the linear regression model training route.
These tests focus on basic functionality without complex mocking.
"""

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


class TestLinearRegressionBasic:
    """Basic test cases for linear regression model training"""

    def test_train_endpoint_exists(self, client):
        """Test that the train endpoint exists and is accessible"""
        # Test that the endpoint is registered
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Check that the train endpoint exists
        assert "/models/train/linear-regression" in paths
        assert "post" in paths["/models/train/linear-regression"]

    def test_train_validation_missing_fields(self, client):
        """Test validation for missing required fields"""
        # Test with empty request
        response = client.post("/models/train/linear-regression", json={})
        assert response.status_code == 422
        
        # Test with missing target
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": "test-dataset"
        })
        assert response.status_code == 422
        
        # Test with missing dataset_id
        response = client.post("/models/train/linear-regression", json={
            "target": "target"
        })
        assert response.status_code == 422

    def test_train_validation_invalid_types(self, client):
        """Test validation for invalid data types"""
        # Test with invalid dataset_id type
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": 123,  # Should be string
            "target": "target"
        })
        assert response.status_code == 422
        
        # Test with invalid test_size type
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": "test-dataset",
            "target": "target",
            "test_size": "invalid"  # Should be number
        })
        assert response.status_code == 422

    def test_train_validation_test_size_range(self, client):
        """Test validation for test_size range"""
        # Test with test_size too large
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": "test-dataset",
            "target": "target",
            "test_size": 1.5  # Should be between 0 and 1
        })
        assert response.status_code == 422
        
        # Test with test_size too small
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": "test-dataset",
            "target": "target",
            "test_size": 0.0  # Should be between 0 and 1
        })
        assert response.status_code == 422

    def test_train_with_valid_request_but_no_dataset(self, client):
        """Test with valid request format but non-existent dataset"""
        # This should return 404 (dataset not found) not 500 (server error)
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": "non-existent-dataset",
            "target": "target",
            "test_size": 0.2
        })
        
        # The response should be either 404 (dataset not found) or 500 (database error)
        # We expect 404 if the database is working, 500 if there's a database connection issue
        assert response.status_code in [404, 500]
        
        if response.status_code == 500:
            # If it's a 500 error, it should be a database connection issue, not a validation issue
            error_detail = response.json().get("detail", "")
            assert "Training failed" in error_detail or "database" in error_detail.lower()

    def test_train_request_schema_validation(self, client):
        """Test that the request schema validation works correctly"""
        # Test with valid request structure
        valid_request = {
            "dataset_id": "test-dataset-123",
            "target": "target_column",
            "features": ["feature1", "feature2"],
            "test_size": 0.3
        }
        
        # This should not return a validation error (422)
        # It might return 404 (dataset not found) or 500 (database error), but not 422
        response = client.post("/models/train/linear-regression", json=valid_request)
        assert response.status_code != 422  # Should not be a validation error

    def test_train_response_schema(self, client):
        """Test that the response schema is properly defined"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        components = openapi_spec.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check that TrainRequest schema exists
        assert "TrainRequest" in schemas
        train_request_schema = schemas["TrainRequest"]
        assert "properties" in train_request_schema
        assert "dataset_id" in train_request_schema["properties"]
        assert "target" in train_request_schema["properties"]
        assert "features" in train_request_schema["properties"]
        assert "test_size" in train_request_schema["properties"]
        
        # Check that TrainResponse schema exists
        assert "TrainResponse" in schemas
        train_response_schema = schemas["TrainResponse"]
        assert "properties" in train_response_schema
        assert "run_id" in train_response_schema["properties"]
        assert "model_type" in train_response_schema["properties"]
        assert "metrics" in train_response_schema["properties"]
        assert "artifact_uri" in train_response_schema["properties"]
