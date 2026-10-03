from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from services.api.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class StorageError(RuntimeError):
    """Raised when an object cannot be stored or retrieved."""


class StorageService:
    """Application storage boundary for local development and S3 production."""

    def __init__(self) -> None:
        backend = settings.storage_backend.strip().lower()

        if backend not in {"local", "s3"}:
            raise StorageError(
                f"Unsupported STORAGE_BACKEND: {settings.storage_backend!r}"
            )

        self.backend = backend
        self.bucket = settings.storage_bucket.strip()
        self.region = settings.storage_region.strip() or None
        self.prefix = settings.storage_prefix.strip("/")

        if self.backend == "s3":
            if not self.bucket:
                raise StorageError(
                    "STORAGE_BUCKET is required when STORAGE_BACKEND=s3."
                )

            self.client = boto3.client("s3", region_name=self.region)
        else:
            self.client = None

    def _s3_key(self, object_key: str) -> str:
        key = object_key.strip().lstrip("/")

        if not key:
            raise StorageError("Storage object key cannot be empty.")

        if self.prefix:
            return f"{self.prefix}/{key}"

        return key

    def _local_path(self, object_key: str) -> Path:
        key = object_key.strip().lstrip("/")

        if not key:
            raise StorageError("Storage object key cannot be empty.")

        path = (PROJECT_ROOT / "storage" / "objects" / key).resolve()
        root = (PROJECT_ROOT / "storage" / "objects").resolve()

        if root not in path.parents:
            raise StorageError("Storage object key escapes the local storage root.")

        return path

    def save_file(self, source: BinaryIO, object_key: str) -> None:
        """Store a binary stream under an application-relative object key."""
        if self.backend == "local":
            destination = self._local_path(object_key)
            destination.parent.mkdir(parents=True, exist_ok=True)

            with destination.open("wb") as output:
                shutil.copyfileobj(source, output)

            return

        key = self._s3_key(object_key)

        try:
            self.client.upload_fileobj(
                source,
                self.bucket,
                key,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(
                f"Failed to upload storage object: {object_key}"
            ) from exc

    def exists(self, object_key: str) -> bool:
        """Return whether an object exists."""
        if self.backend == "local":
            return self._local_path(object_key).is_file()

        key = self._s3_key(object_key)

        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False

            raise StorageError(
                f"Failed to check storage object: {object_key}"
            ) from exc

    def delete_file(self, object_key: str) -> None:
        """Delete a stored object if it exists."""
        if self.backend == "local":
            path = self._local_path(object_key)

            if path.exists():
                path.unlink()

                parent = path.parent
                root = (PROJECT_ROOT / "storage" / "objects").resolve()

                while parent != root and parent.exists():
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent

            return

        key = self._s3_key(object_key)

        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=key,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(
                f"Failed to delete storage object: {object_key}"
            ) from exc

    def download_to_path(self, object_key: str, destination: Path) -> Path:
        """Download an object to a caller-provided local path."""
        destination = destination.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        if self.backend == "local":
            source = self._local_path(object_key)

            if not source.is_file():
                raise StorageError(
                    f"Storage object not found: {object_key}"
                )

            shutil.copy2(source, destination)
            return destination

        key = self._s3_key(object_key)

        try:
            self.client.download_file(
                self.bucket,
                key,
                str(destination),
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(
                f"Failed to download storage object: {object_key}"
            ) from exc

        return destination

    def materialize(self, object_key: str) -> tuple[Path, bool]:
        """
        Return a local filesystem path for an object.

        Returns:
            (path, temporary)
            temporary is True when a temporary S3 download was created.
        """
        if self.backend == "local":
            path = self._local_path(object_key)

            if not path.is_file():
                raise StorageError(
                    f"Storage object not found: {object_key}"
                )

            return path, False

        temp_dir = Path(tempfile.mkdtemp(prefix="deepsight-storage-"))
        destination = temp_dir / Path(object_key).name

        try:
            self.download_to_path(object_key, destination)
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

        return destination, True

    @staticmethod
    def cleanup_materialized(path: Path) -> None:
        """Remove a temporary materialized object when one was created."""
        parent = path.parent

        if parent.name.startswith("deepsight-storage-"):
            shutil.rmtree(parent, ignore_errors=True)


storage = StorageService()
