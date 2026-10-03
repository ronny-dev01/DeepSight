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
