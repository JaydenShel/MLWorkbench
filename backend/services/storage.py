from abc import ABC, abstractmethod
from pathlib import Path
import uuid


class Storage(ABC):
    @abstractmethod
    async def save_bytes(self, filename: str, data: bytes) -> tuple[str, int]:
        """Save binary data and return (uri, size_bytes)."""
        pass


class LocalStorage(Storage):
    def __init__(self, base_dir: str = "data"):
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        self.base_dir = Path(base_dir)

    async def save_bytes(self, filename: str, data: bytes) -> tuple[str, int]:
        key = f"{uuid.uuid4()}_{filename}"
        path = self.base_dir / key
        path.write_bytes(data)
        return (f"file://{path.resolve()}", len(data))
