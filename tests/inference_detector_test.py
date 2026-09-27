from unittest.mock import MagicMock

from ml.inference import detector
from ml.inference.schema import DetectionResult


def test_detector_defaults_use_configured_runtime(tmp_path, monkeypatch):
    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"test")

    fake_yolo = MagicMock()
    monkeypatch.setattr(detector, "YOLO", fake_yolo)

    monkeypatch.setattr(detector.settings, "model_path", str(model_path))
    monkeypatch.setattr(detector.settings, "model_device", "cuda")
    monkeypatch.setattr(detector.settings, "model_confidence", 0.31)
    monkeypatch.setattr(detector.settings, "model_iou", 0.41)
    monkeypatch.setattr(detector.settings, "model_image_size", 768)
    monkeypatch.setattr(detector.settings, "model_name", "test-model")
    monkeypatch.setattr(detector.settings, "model_version", "test-v1")
    monkeypatch.setattr(detector.settings, "model_verify_hash", False)

    instance = detector.MarineDetector()

    assert instance.device == "cuda"
    assert instance.confidence == 0.31
    assert instance.iou == 0.41
    assert instance.image_size == 768
    assert instance.model_name == "test-model"
    assert instance.model_version == "test-v1"
    fake_yolo.assert_called_once_with(str(model_path))


def test_explicit_runtime_overrides_config(tmp_path, monkeypatch):
    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"test")

    fake_yolo = MagicMock()
    monkeypatch.setattr(detector, "YOLO", fake_yolo)

    monkeypatch.setattr(detector.settings, "model_path", str(model_path))
    monkeypatch.setattr(detector.settings, "model_device", "cuda")
    monkeypatch.setattr(detector.settings, "model_confidence", 0.31)
    monkeypatch.setattr(detector.settings, "model_iou", 0.41)
    monkeypatch.setattr(detector.settings, "model_image_size", 768)
    monkeypatch.setattr(detector.settings, "model_verify_hash", False)

    instance = detector.MarineDetector(
        confidence=0.55,
        iou=0.35,
        image_size=640,
        device="cpu",
    )

    assert instance.device == "cpu"
    assert instance.confidence == 0.55
    assert instance.iou == 0.35
    assert instance.image_size == 640


def test_detection_result_preserves_model_version():
    result = DetectionResult(
        model_path="model.pt",
        model_name="test-model",
        model_version="v1",
        image_width=640,
        image_height=640,
        inference_ms=12.5,
        detections=(),
    )

    payload = result.to_dict()

    assert payload["model_name"] == "test-model"
    assert payload["model_version"] == "v1"
    assert payload["detection_count"] == 0
