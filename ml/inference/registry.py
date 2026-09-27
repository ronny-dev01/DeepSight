from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ModelRegistryError(RuntimeError):
    """Raised when the configured model does not match the model registry."""


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest().upper()


def _load_registry(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ModelRegistryError(
            f"Model registry not found: {path}"
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelRegistryError(
            f"Could not read model registry: {path}"
        ) from exc

    if not isinstance(payload, dict):
        raise ModelRegistryError(
            "Model registry root must be a JSON object."
        )

    models = payload.get("models")
    if not isinstance(models, list):
        raise ModelRegistryError(
            "Model registry field 'models' must be a list."
        )

    return payload


def verify_model_artifact(
    *,
    registry_path: str | Path,
    project_root: str | Path,
    model_name: str,
    model_version: str,
    model_path: str | Path,
) -> Path:
    registry_file = Path(registry_path)
    if not registry_file.is_absolute():
        registry_file = Path(project_root) / registry_file

    registry_file = registry_file.resolve()
    registry = _load_registry(registry_file)

    entry = next(
        (
            item
            for item in registry["models"]
            if isinstance(item, dict)
            and item.get("name") == model_name
        ),
        None,
    )

    if entry is None:
        raise ModelRegistryError(
            f"Model '{model_name}' is not registered in {registry_file}."
        )

    registered_version = entry.get("version")
    if registered_version != model_version:
        raise ModelRegistryError(
            f"Model version mismatch for '{model_name}': "
            f"configured={model_version!r}, "
            f"registered={registered_version!r}."
        )

    configured_path = Path(model_path)
    if not configured_path.is_absolute():
        configured_path = Path(project_root) / configured_path

    configured_path = configured_path.resolve()

    registered_artifact = entry.get("artifact")
    if not isinstance(registered_artifact, str) or not registered_artifact:
        raise ModelRegistryError(
            f"Model '{model_name}' has no valid registered artifact path."
        )

    registered_path = (
        Path(project_root) / registered_artifact
    ).resolve()

    if configured_path != registered_path:
        raise ModelRegistryError(
            f"Model artifact mismatch for '{model_name}': "
            f"configured={configured_path}, "
            f"registered={registered_path}."
        )

    if not configured_path.is_file():
        raise ModelRegistryError(
            f"Model artifact not found: {configured_path}"
        )

    expected_hash = entry.get("artifact_sha256")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ModelRegistryError(
            f"Model '{model_name}' has no valid SHA-256 artifact hash."
        )

    actual_hash = _sha256_file(configured_path)

    if actual_hash != expected_hash.upper():
        raise ModelRegistryError(
            f"Model artifact hash mismatch for '{model_name}': "
            f"expected={expected_hash.upper()}, actual={actual_hash}."
        )

    return configured_path
