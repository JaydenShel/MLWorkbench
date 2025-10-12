# services/storage_s3.py
import uuid
import mimetypes
import aioboto3
from typing import Optional
from .storage import Storage


class S3Storage(Storage):
    def __init__(
        self, bucket: str, prefix: Optional[str] = None, region: Optional[str] = None
    ):
        self.bucket = bucket
        self.prefix = prefix.strip("/") if prefix else None
        self.region = region

    async def save_bytes(self, filename: str, data: bytes) -> tuple[str, int]:
        key = f"{uuid.uuid4()}_{filename}"
        if self.prefix:
            key = f"{self.prefix}/{key}"

        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        session = aioboto3.Session()
        async with session.client("s3", region_name=self.region) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        return (f"s3://{self.bucket}/{key}", len(data))
