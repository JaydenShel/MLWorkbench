# routers/upload_router.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import pandas.io.common as pdio
import uuid
from services.storage import Storage
from services.storage_s3 import S3Storage

router = APIRouter(prefix="/datasets", tags=["Datasets"])


class UploadResponse(BaseModel):
    """Response model for CSV upload"""

    dataset_id: str
    uri: str
    size_bytes: int
    columns: List[str]
    rows: int


class ErrorResponse(BaseModel):
    """Error response model"""

    detail: str


def get_storage() -> Storage:
    """Dependency to get storage instance"""
    # For local dev and testing, use LocalStorage:
    from services.storage import LocalStorage

    return LocalStorage(base_dir="data")
    # For production with S3, use:
    # return S3Storage(bucket="csv-storage-ml")


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        200: {"description": "CSV file uploaded successfully", "model": UploadResponse},
        400: {
            "description": "Invalid file or CSV parsing error",
            "model": ErrorResponse,
        },
        422: {"description": "Validation error - file parameter missing"},
    },
    summary="Upload CSV Dataset",
    description="Upload a CSV file for machine learning dataset processing. "
    "The file will be validated, parsed, and stored. Returns metadata about the dataset.",
)
async def upload_csv(
    file: UploadFile = File(
        ..., description="CSV file to upload", media_type="text/csv"
    ),
    storage: Storage = Depends(get_storage),
) -> UploadResponse:
    """
    Upload a CSV dataset file.

    - **file**: CSV file to upload (required)
    - **Returns**: Dataset metadata including ID, URI, size, columns, and row count

    The uploaded file will be:
    1. Validated to ensure it's a CSV file
    2. Parsed to extract column information
    3. Stored in the configured storage backend
    4. Metadata returned for further processing
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="File must be a CSV file with .csv extension"
        )

    content = await file.read()

    # Allow empty CSV files (just headers)
    # if len(content) == 0:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Uploaded file is empty"
    #     )

    try:
        df = pd.read_csv(pdio.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {str(e)}")

    uri, size_bytes = await storage.save_bytes(file.filename, content)

    dataset_id = str(uuid.uuid4())
    row_count = len(df)
    columns = list(df.columns)

    # TODO: Save metadata (dataset_id, filename, uri, size, columns, row_count) to database using SQLAlchemy

    return UploadResponse(
        dataset_id=dataset_id,
        uri=uri,
        size_bytes=size_bytes,
        columns=columns,
        rows=row_count,
    )
