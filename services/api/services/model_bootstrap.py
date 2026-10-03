from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from services.api.config import settings
from services.api.services.storage import StorageError, storage


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ModelBootstrapError(RuntimeError):
    """Raised when the production model artifact cannot be prepared."""


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest().upper()


def _load_registered_model() -> dict[str, Any]:
    registry_path = Path(settings.model_registry_path)

    if not registry_path.is_absolute():
        registry_path = PROJECT_ROOT / registry_path

    try:
        payload = json.loads(
            registry_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelBootstrapError(
            f"Could not read model registry: {registry_path}"
        ) from exc

    for item in payload.get("models", []):
        if (
            isinstance(item, dict)
            and item.get("name") == settings.model_name
        ):
            if item.get("version") != settings.model_version:
                raise ModelBootstrapError(
                    f"Registered model version mismatch: "
                    f"configured={settings.model_version!r}, "
                    f"registered={item.get('version')!r}"
                )

            expected_hash = item.get("artifact_sha256")

            if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                raise ModelBootstrapError(
                    "Registered model has no valid SHA-256 artifact hash."
                )

            return item

    raise ModelBootstrapError(
        f"Model {settings.model_name!r} is not registered."
    )


def ensure_model_artifact() -> Path:
    """
    Ensure the configured model artifact exists at its registered local path.

    Local storage:
        Requires the model file to already exist.

    S3 storage:
        Downloads the configured artifact when missing or when the existing
        file hash does not match the registered SHA-256. The replacement is
        performed atomically after the downloaded file is verified.
    """
    target = Path(settings.model_path)

    if not target.is_absolute():
        target = PROJECT_ROOT / target

    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    if storage.backend == "local":
        if not target.is_file():
            raise ModelBootstrapError(
                f"Model artifact not found: {target}"
            )

        return target

    registered_model = _load_registered_model()
    expected_hash = str(
        registered_model["artifact_sha256"]
    ).upper()

    if target.is_file():
        actual_hash = _sha256_file(target)

        if actual_hash == expected_hash:
            return target

    temporary = target.with_name(
        f".{target.name}.download"
    )

    try:
        storage.download_to_path(
            settings.model_artifact_key,
            temporary,
        )

        actual_hash = _sha256_file(temporary)

        if actual_hash != expected_hash:
            raise ModelBootstrapError(
                "Downloaded model artifact hash mismatch: "
                f"expected={expected_hash}, actual={actual_hash}"
            )

        os.replace(temporary, target)
        return target

    except (StorageError, OSError) as exc:
        raise ModelBootstrapError(
            f"Could not prepare model artifact: {target}"
        ) from exc
    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass
