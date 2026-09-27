import hashlib
import json

import pytest

from ml.inference.registry import (
    ModelRegistryError,
    verify_model_artifact,
)


def _write_registry(
    tmp_path,
    artifact_path,
    model_name="test-model",
    model_version="v1",
    artifact_sha256=None,
):
    registry_path = tmp_path / "model_registry.json"

    registry_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active_model": model_name,
                "models": [
                    {
                        "name": model_name,
                        "version": model_version,
                        "artifact": artifact_path,
                        "artifact_sha256": artifact_sha256 or ("A" * 64),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    return registry_path


def test_registry_rejects_version_mismatch(tmp_path):
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"model")

    registry = _write_registry(
        tmp_path,
        "model.pt",
        model_version="v2",
    )

    with pytest.raises(ModelRegistryError, match="version mismatch"):
        verify_model_artifact(
            registry_path=registry,
            project_root=tmp_path,
            model_name="test-model",
            model_version="v1",
            model_path=artifact,
        )


def test_registry_rejects_hash_mismatch(tmp_path):
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"model")

    registry = _write_registry(
        tmp_path,
        "model.pt",
        model_version="v1",
    )

    with pytest.raises(ModelRegistryError, match="hash mismatch"):
        verify_model_artifact(
            registry_path=registry,
            project_root=tmp_path,
            model_name="test-model",
            model_version="v1",
            model_path=artifact,
        )


def test_registry_accepts_matching_artifact(tmp_path):
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"model")

    digest = hashlib.sha256(b"model").hexdigest().upper()

    registry = _write_registry(
        tmp_path,
        "model.pt",
        model_version="v1",
        artifact_sha256=digest,
    )

    result = verify_model_artifact(
        registry_path=registry,
        project_root=tmp_path,
        model_name="test-model",
        model_version="v1",
        model_path=artifact,
    )

    assert result == artifact.resolve()


def test_registry_rejects_unregistered_model(tmp_path):
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"model")

    registry = _write_registry(
        tmp_path,
        "model.pt",
        model_name="registered-model",
        model_version="v1",
    )

    with pytest.raises(ModelRegistryError, match="not registered"):
        verify_model_artifact(
            registry_path=registry,
            project_root=tmp_path,
            model_name="other-model",
            model_version="v1",
            model_path=artifact,
        )


def test_registry_rejects_artifact_path_mismatch(tmp_path):
    registered = tmp_path / "registered.pt"
    actual = tmp_path / "actual.pt"

    registered.write_bytes(b"model")
    actual.write_bytes(b"model")

    digest = hashlib.sha256(b"model").hexdigest().upper()

    registry = _write_registry(
        tmp_path,
        "registered.pt",
        model_version="v1",
        artifact_sha256=digest,
    )

    with pytest.raises(ModelRegistryError, match="artifact mismatch"):
        verify_model_artifact(
            registry_path=registry,
            project_root=tmp_path,
            model_name="test-model",
            model_version="v1",
            model_path=actual,
        )
