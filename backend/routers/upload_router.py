# routers/upload_router.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import pandas as pd
import pandas.io.common as pdio
import uuid
from sqlalchemy.orm import Session

from services.storage import Storage
from services.storage_s3 import S3Storage
from db import get_db
from models import Dataset

router = APIRouter(prefix="/datasets", tags=["Datasets"])

class UploadResponse(BaseModel):
    dataset_id: str
    uri: str
    size_bytes: int
    columns: List[str]
    rows: int

class ErrorResponse(BaseModel):
    detail: str

def get_storage() -> Storage:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    storage_type = os.getenv("STORAGE_TYPE", "local")
    if storage_type == "s3":
        return S3Storage(bucket="csv-storage-ml", region="us-east-1", prefix="datasets")
    else:
        from services.storage import LocalStorage
        return LocalStorage(base_dir="data")

@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        200: {"description": "CSV file uploaded successfully", "model": UploadResponse},
        400: {"description": "Invalid file or CSV parsing error", "model": ErrorResponse},
        422: {"description": "Validation error - file parameter missing"},
    },
    summary="Upload CSV Dataset",
    description="Upload a CSV file for ML processing; validates, parses, stores, and returns metadata.",
)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload", media_type="text/csv"),
    storage: Storage = Depends(get_storage),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """
    Upload a CSV dataset file.
    
    - **file**: CSV file to upload (required)
    - **Returns**: Dataset metadata including ID, URI, size, columns, and row count
    
    The uploaded file will be:
    1. Validated to ensure it's a CSV file
    2. Parsed to extract column information
    3. Stored in the configured storage backend
    4. Metadata saved to database
    5. Metadata returned for further processing
    """
    try:
        # Validate file
        if not file.filename or not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV file with .csv extension")

        # Read and parse CSV
        content = await file.read()
        try:
            df = pd.read_csv(pdio.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading CSV file: {str(e)}")

        # Save file to storage
        uri, size_bytes = await storage.save_bytes(file.filename, content)

        # Prepare dataset metadata
        dataset_id = str(uuid.uuid4())
        row_count = len(df)
        columns = list(df.columns)

        # Save to database
        try:
            dataset = Dataset(
                id=dataset_id,
                filename=file.filename,
                uri=uri,
                size_bytes=size_bytes,
                columns={"columns": columns},
                rows=row_count,
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save dataset to database: {str(e)}")

        # Return response
        return UploadResponse(
            dataset_id=dataset_id,
            uri=uri,
            size_bytes=size_bytes,
            columns=columns,
            rows=row_count,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
