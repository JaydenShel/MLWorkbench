from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from services.storage import Storage
from routers.upload_router import get_storage
from db.db import get_db
from db.models import Dataset, ModelRun
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import pandas as pd
import pandas.io.common as pdio
import io
import joblib
import uuid


router = APIRouter(prefix="/models", tags=["Models"])


class TrainRequest(BaseModel):
    """Request model for training a linear regression model"""
    dataset_id: str
    target: str
    features: Optional[List[str]] = None
    test_size: Optional[float] = 0.2


class TrainResponse(BaseModel):
    """Response model for training results"""
    run_id: int
    model_type: str
    metrics: Dict[str, float]
    artifact_uri: str


@router.post(
    "/train/linear-regression",
    response_model=TrainResponse,
    responses={
        200: {
            "description": "Model trained successfully",
            "model": TrainResponse
        },
        404: {
            "description": "Dataset not found"
        },
        400: {
            "description": "Invalid training parameters or data"
        }
    },
    summary="Train Linear Regression Model",
    description="Train a linear regression model on a dataset. "
                "Automatically selects numeric features if not specified. "
                "Returns model metrics and artifact URI for the trained model."
)
async def train_linear_regression(
    request: TrainRequest,
    storage: Storage = Depends(get_storage),
    db: Session = Depends(get_db),
) -> TrainResponse:
    """
    Train a linear regression model on a dataset.
    
    - **dataset_id**: ID of the dataset to train on
    - **target**: Target column name for prediction
    - **features**: Optional list of feature columns (auto-selected if not provided)
    - **test_size**: Fraction of data to use for testing (default: 0.2)
    
    Returns model metrics and artifact URI for the trained model.
    """
    try:
        # 1) Look up dataset
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        uri = dataset.uri

        # 2) Load DataFrame from URI
        if uri.startswith("file://"):
            path = uri.replace("file://", "")
            df = pd.read_csv(path)
        elif uri.startswith("s3://"):
            # TODO: Implement S3 loading
            raise HTTPException(status_code=400, detail="S3 loading not implemented yet")
        else:
            raise HTTPException(status_code=400, detail="Unsupported URI format")

        # 3) Select features (numeric-only for now)
        features = request.features
        if not features:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            features = [c for c in numeric_cols if c != request.target]
        
        if request.target not in df.columns:
            raise HTTPException(status_code=400, detail=f"Target column '{request.target}' not found in dataset")
        
        # 4) Prepare data
        X = df[features].dropna()
        y = df.loc[X.index, request.target]
        
        if len(X) == 0:
            raise HTTPException(status_code=400, detail="No valid data for training")

        # 5) Split, train, evaluate
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=request.test_size, random_state=42
        )
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "mse": mean_squared_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred)
        }

        # 6) Serialize model
        buf = io.BytesIO()
        joblib.dump({
            "model": model, 
            "features": features, 
            "target": request.target
        }, buf)
        artifact_bytes = buf.getvalue()

        # 7) Save artifact
        artifact_uri, _ = await storage.save_bytes(f"model_{request.dataset_id}.pkl", artifact_bytes)

        # 8) Persist model run
        run = ModelRun(
            dataset_id=request.dataset_id,
            model_type="linear_regression",
            metrics=metrics,
            artifact_uri=artifact_uri
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # 9) Return response
        return TrainResponse(
            run_id=run.id,
            model_type="linear_regression",
            metrics=metrics,
            artifact_uri=artifact_uri
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")
