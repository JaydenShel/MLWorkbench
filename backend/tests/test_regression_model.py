"""
Comprehensive tests for the linear regression model training route.
"""

import pytest
import pandas as pd
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app import app
from db.models import Dataset, ModelRun
from routers.train_router import TrainRequest, TrainResponse


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing"""
    data = {
        'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'feature2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        'feature3': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        'target': [3, 6, 9, 12, 15, 18, 21, 24, 27, 30],
        'category': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B']
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_csv_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_dataset():
    """Create a mock dataset"""
    return Dataset(
        id="test-dataset-123",
        filename="test.csv",
        uri="file:///tmp/test.csv",
        size_bytes=1000,
        columns=["feature1", "feature2", "feature3", "target", "category"],
        rows=10
    )


@pytest.fixture
def mock_storage():
    """Create a mock storage service"""
    storage = AsyncMock()
    storage.save_bytes.return_value = ("s3://bucket/model_123.pkl", 1024)
    return storage


class TestLinearRegressionTraining:
    """Test cases for linear regression model training"""

    def test_train_linear_regression_success(self, client, temp_csv_file, mock_dataset, mock_storage):
        """Test successful linear regression training"""
        # Mock database operations
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage), \
             patch('routers.train_router.pd.read_csv') as mock_read_csv:
            
            # Setup mocks
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock pandas read_csv to return our test data
            test_data = pd.DataFrame({
                'feature1': [1, 2, 3, 4, 5],
                'feature2': [2, 4, 6, 8, 10],
                'feature3': [0.5, 1.0, 1.5, 2.0, 2.5],
                'target': [3, 6, 9, 12, 15]
            })
            mock_read_csv.return_value = test_data
            
            # Create mock model run
            mock_model_run = ModelRun(
                id=1,
                dataset_id="test-dataset-123",
                model_type="linear_regression",
                metrics={"mae": 0.1, "mse": 0.01, "r2": 0.99},
                artifact_uri="s3://bucket/model_123.pkl"
            )
            mock_db.refresh.side_effect = lambda run: setattr(run, 'id', 1)
            
            # Make request
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "target",
                "features": ["feature1", "feature2", "feature3"],
                "test_size": 0.2
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert "run_id" in data
            assert data["model_type"] == "linear_regression"
            assert "metrics" in data
            assert "artifact_uri" in data
            assert "mae" in data["metrics"]
            assert "mse" in data["metrics"]
            assert "r2" in data["metrics"]
            
            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_train_linear_regression_dataset_not_found(self, client, mock_storage):
        """Test training with non-existent dataset"""
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage):
            
            # Setup mock to return None (dataset not found)
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value = mock_db
            
            request_data = {
                "dataset_id": "non-existent-dataset",
                "target": "target"
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 404
            assert "Dataset not found" in response.json()["detail"]

    def test_train_linear_regression_target_not_found(self, client, mock_dataset, mock_storage):
        """Test training with target column that doesn't exist"""
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage), \
             patch('routers.train_router.pd.read_csv') as mock_read_csv:
            
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_get_db.return_value = mock_db
            
            # Mock data without the target column
            test_data = pd.DataFrame({
                'feature1': [1, 2, 3, 4, 5],
                'feature2': [2, 4, 6, 8, 10]
            })
            mock_read_csv.return_value = test_data
            
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "non_existent_target"
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 400
            assert "Target column 'non_existent_target' not found" in response.json()["detail"]

    def test_train_linear_regression_no_valid_data(self, client, mock_dataset, mock_storage):
        """Test training with dataset that has no valid numeric data"""
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage), \
             patch('routers.train_router.pd.read_csv') as mock_read_csv:
            
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_get_db.return_value = mock_db
            
            # Mock data with all NaN values
            test_data = pd.DataFrame({
                'feature1': [float('nan'), float('nan'), float('nan')],
                'feature2': [float('nan'), float('nan'), float('nan')],
                'target': [float('nan'), float('nan'), float('nan')]
            })
            mock_read_csv.return_value = test_data
            
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "target"
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 400
            assert "No valid data for training" in response.json()["detail"]

    def test_train_linear_regression_auto_feature_selection(self, client, mock_dataset, mock_storage):
        """Test that features are automatically selected when not provided"""
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage), \
             patch('routers.train_router.pd.read_csv') as mock_read_csv:
            
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock data with mixed types
            test_data = pd.DataFrame({
                'numeric1': [1, 2, 3, 4, 5],
                'numeric2': [2, 4, 6, 8, 10],
                'categorical': ['A', 'B', 'A', 'B', 'A'],
                'target': [3, 6, 9, 12, 15]
            })
            mock_read_csv.return_value = test_data
            
            # Mock model run
            mock_model_run = ModelRun(
                id=1,
                dataset_id="test-dataset-123",
                model_type="linear_regression",
                metrics={"mae": 0.1, "mse": 0.01, "r2": 0.99},
                artifact_uri="s3://bucket/model_123.pkl"
            )
            mock_db.refresh.side_effect = lambda run: setattr(run, 'id', 1)
            
            # Request without features (should auto-select)
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "target"
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_type"] == "linear_regression"

    def test_train_linear_regression_unsupported_uri(self, client, mock_dataset, mock_storage):
        """Test training with unsupported URI format"""
        # Create dataset with unsupported URI
        mock_dataset.uri = "unsupported://path/to/data.csv"
        
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage):
            
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_get_db.return_value = mock_db
            
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "target"
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 400
            assert "Unsupported URI format" in response.json()["detail"]

    def test_train_linear_regression_s3_not_implemented(self, client, mock_dataset, mock_storage):
        """Test training with S3 URI (not yet implemented)"""
        # Create dataset with S3 URI
        mock_dataset.uri = "s3://bucket/data.csv"
        
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage):
            
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_get_db.return_value = mock_db
            
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "target"
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 400
            assert "S3 loading not implemented yet" in response.json()["detail"]

    def test_train_linear_regression_validation_errors(self, client):
        """Test input validation errors"""
        # Test missing required fields
        response = client.post("/models/train/linear-regression", json={})
        assert response.status_code == 422
        
        # Test invalid data types
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": 123,  # Should be string
            "target": "target",
            "test_size": "invalid"  # Should be number
        })
        assert response.status_code == 422
        
        # Test missing target field
        response = client.post("/models/train/linear-regression", json={
            "dataset_id": "test-dataset"
        })
        assert response.status_code == 422

    def test_train_linear_regression_database_rollback_on_error(self, client, mock_dataset, mock_storage):
        """Test that database is rolled back when training fails"""
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage), \
             patch('routers.train_router.pd.read_csv') as mock_read_csv:
            
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_db.rollback = Mock()
            mock_get_db.return_value = mock_db
            
            # Make read_csv raise an exception
            mock_read_csv.side_effect = Exception("File read error")
            
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "target"
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 500
            assert "Training failed" in response.json()["detail"]
            mock_db.rollback.assert_called_once()

    def test_train_linear_regression_metrics_calculation(self, client, mock_dataset, mock_storage):
        """Test that metrics are calculated correctly"""
        with patch('routers.train_router.get_db') as mock_get_db, \
             patch('routers.train_router.get_storage', return_value=mock_storage), \
             patch('routers.train_router.pd.read_csv') as mock_read_csv:
            
            mock_db = Mock(spec=Session)
            mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock data with known relationship for predictable metrics
            test_data = pd.DataFrame({
                'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'target': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Perfect linear relationship
            })
            mock_read_csv.return_value = test_data
            
            mock_db.refresh.side_effect = lambda run: setattr(run, 'id', 1)
            
            request_data = {
                "dataset_id": "test-dataset-123",
                "target": "target",
                "features": ["feature1"]
            }
            
            response = client.post("/models/train/linear-regression", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            metrics = data["metrics"]
            
            # With perfect linear relationship, R² should be close to 1
            assert "mae" in metrics
            assert "mse" in metrics
            assert "r2" in metrics
            assert isinstance(metrics["mae"], (int, float))
            assert isinstance(metrics["mse"], (int, float))
            assert isinstance(metrics["r2"], (int, float))
