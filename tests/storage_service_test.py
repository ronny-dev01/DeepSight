from io import BytesIO
from uuid import uuid4

import pytest

from services.api.services.storage import StorageError, storage


def test_local_storage_save_exists_download_delete(tmp_path) -> None:
    key = f"tests/storage/{uuid4()}.bin"
    payload = b"DeepSight storage test"
    destination = tmp_path / "downloaded.bin"

    try:
        storage.save_file(BytesIO(payload), key)

        assert storage.exists(key)

        storage.download_to_path(key, destination)

        assert destination.read_bytes() == payload

        storage.delete_file(key)

        assert not storage.exists(key)
    finally:
        storage.delete_file(key)


def test_local_storage_rejects_empty_key() -> None:
    with pytest.raises(StorageError):
        storage.save_file(BytesIO(b"data"), "")


def test_local_storage_rejects_path_escape() -> None:
    with pytest.raises(StorageError):
        storage.save_file(BytesIO(b"data"), "../../outside.bin")


def test_local_storage_missing_object_download_fails(tmp_path) -> None:
    key = f"tests/storage/missing-{uuid4()}.bin"

    with pytest.raises(StorageError):
        storage.download_to_path(key, tmp_path / "missing.bin")


def test_local_storage_missing_object_exists_is_false() -> None:
    key = f"tests/storage/missing-{uuid4()}.bin"

    assert storage.exists(key) is False

from unittest.mock import MagicMock

from botocore.config import Config

from services.api.services import storage as storage_module


def test_s3_storage_uses_custom_endpoint(monkeypatch):
    fake_client = MagicMock()
    fake_boto_client = MagicMock(return_value=fake_client)

    monkeypatch.setattr(storage_module.boto3, "client", fake_boto_client)
    monkeypatch.setattr(storage_module.settings, "storage_backend", "s3")
    monkeypatch.setattr(storage_module.settings, "storage_bucket", "test-bucket")
    monkeypatch.setattr(storage_module.settings, "storage_region", "auto")
    monkeypatch.setattr(
        storage_module.settings,
        "storage_endpoint_url",
        "https://example.r2.cloudflarestorage.com",
    )
    monkeypatch.setattr(storage_module.settings, "storage_prefix", "deepsight")

    service = storage_module.StorageService()

    assert service.backend == "s3"
    assert service.bucket == "test-bucket"
    assert service.endpoint_url == "https://example.r2.cloudflarestorage.com"
    assert service.prefix == "deepsight"

    fake_boto_client.assert_called_once()
    kwargs = fake_boto_client.call_args.kwargs

    assert fake_boto_client.call_args.args[0] == "s3"
    assert kwargs["region_name"] == "auto"
    assert kwargs["endpoint_url"] == "https://example.r2.cloudflarestorage.com"
    assert isinstance(kwargs["config"], Config)
    assert kwargs["config"].s3["addressing_style"] == "path"


def test_s3_storage_without_custom_endpoint_uses_default_config(monkeypatch):
    fake_client = MagicMock()
    fake_boto_client = MagicMock(return_value=fake_client)

    monkeypatch.setattr(storage_module.boto3, "client", fake_boto_client)
    monkeypatch.setattr(storage_module.settings, "storage_backend", "s3")
    monkeypatch.setattr(storage_module.settings, "storage_bucket", "test-bucket")
    monkeypatch.setattr(storage_module.settings, "storage_region", "us-east-1")
    monkeypatch.setattr(storage_module.settings, "storage_endpoint_url", "")
    monkeypatch.setattr(storage_module.settings, "storage_prefix", "")

    service = storage_module.StorageService()

    assert service.backend == "s3"
    assert service.endpoint_url is None

    kwargs = fake_boto_client.call_args.kwargs

    assert fake_boto_client.call_args.args[0] == "s3"
    assert kwargs["region_name"] == "us-east-1"
    assert kwargs["endpoint_url"] is None
    assert kwargs["config"] is None
