import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


class TestTrainRouter:
    """Test cases for the train router"""

    def test_train_linear_regression_endpoint_exists(self, client):
        """Test that the train endpoint exists and returns proper schema"""
        # Test that the endpoint is registered
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Check that the train endpoint exists
        assert "/models/train/linear-regression" in paths
        assert "post" in paths["/models/train/linear-regression"]
        
        # Check endpoint documentation
        endpoint_info = paths["/models/train/linear-regression"]["post"]
        assert "summary" in endpoint_info
        assert "Train Linear Regression Model" in endpoint_info["summary"]
        assert "description" in endpoint_info
        assert "responses" in endpoint_info

    def test_train_linear_regression_request_schema(self, client):
        """Test that the request schema is properly defined"""
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

    def test_train_linear_regression_response_schema(self, client):
        """Test that the response schema is properly defined"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        components = openapi_spec.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check that TrainResponse schema exists
        assert "TrainResponse" in schemas
        train_response_schema = schemas["TrainResponse"]
        assert "properties" in train_response_schema
        assert "run_id" in train_response_schema["properties"]
        assert "model_type" in train_response_schema["properties"]
        assert "metrics" in train_response_schema["properties"]
        assert "artifact_uri" in train_response_schema["properties"]

    def test_train_linear_regression_validation_error(self, client):
        """Test that the endpoint returns validation error for invalid input"""
        # Test with missing required fields
        response = client.post("/models/train/linear-regression", json={})
        assert response.status_code == 422  # Validation error
        
        # Test with invalid data types
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": 123,  # Should be string
            "target": "target",
            "test_size": "invalid"  # Should be number
        })
        assert response.status_code == 422  # Validation error
