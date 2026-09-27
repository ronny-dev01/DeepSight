from types import SimpleNamespace

import numpy as np

from ml.inference import detector


class FakeTensor:
    def __init__(self, value):
        self.value = np.asarray(value)

    def cpu(self):
        return self

    def numpy(self):
        return self.value


class FakeBoxes:
    def __init__(self, boxes, confidences, classes):
        self.xyxy = FakeTensor(boxes)
        self.conf = FakeTensor(confidences)
        self.cls = FakeTensor(classes)


class FakeResult:
    def __init__(self, boxes=None):
        self.boxes = boxes


def _make_detector(monkeypatch, tmp_path, tiling_enabled=True):
    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"test-model")

    fake_model = SimpleNamespace(
        names={0: "Crab-Pot"},
        predict=lambda **kwargs: [],
    )

    monkeypatch.setattr(
        detector,
        "YOLO",
        lambda _path: fake_model,
    )

    monkeypatch.setattr(
        detector.settings,
        "model_path",
        str(model_path),
    )
    monkeypatch.setattr(
        detector.settings,
        "model_name",
        "test-model",
    )
    monkeypatch.setattr(
        detector.settings,
        "model_version",
        "test-v1",
    )
    monkeypatch.setattr(
        detector.settings,
        "model_device",
        "cpu",
    )
    monkeypatch.setattr(
        detector.settings,
        "model_confidence",
        0.075,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_iou",
        0.45,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_image_size",
        640,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_tiling_enabled",
        tiling_enabled,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_tile_size",
        384,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_tile_stride",
        256,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_tile_iou",
        0.70,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_tile_nms_iou",
        0.50,
    )
    monkeypatch.setattr(
        detector.settings,
        "model_verify_hash",
        False,
    )

    return detector.MarineDetector()


def test_tile_origins_cover_edges():
    origins = detector.MarineDetector._tile_origins(
        640,
        384,
        256,
    )

    assert origins == (0, 256)


def test_tile_origins_for_small_image():
    origins = detector.MarineDetector._tile_origins(
        300,
        384,
        256,
    )

    assert origins == (0,)


def test_global_nms_suppresses_same_class_overlap(
    monkeypatch,
    tmp_path,
):
    instance = _make_detector(
        monkeypatch,
        tmp_path,
        tiling_enabled=True,
    )

    first = detector.Detection(
        class_id=0,
        class_name="Crab-Pot",
        confidence=0.90,
        bbox_xyxy=(10.0, 10.0, 50.0, 50.0),
    )

    duplicate = detector.Detection(
        class_id=0,
        class_name="Crab-Pot",
        confidence=0.80,
        bbox_xyxy=(12.0, 12.0, 48.0, 48.0),
    )

    kept = instance._global_nms([first, duplicate])

    assert len(kept) == 1
    assert kept[0].confidence == 0.90


def test_global_nms_does_not_suppress_different_classes(
    monkeypatch,
    tmp_path,
):
    instance = _make_detector(
        monkeypatch,
        tmp_path,
        tiling_enabled=True,
    )

    first = detector.Detection(
        class_id=0,
        class_name="Crab-Pot",
        confidence=0.90,
        bbox_xyxy=(10.0, 10.0, 50.0, 50.0),
    )

    second = detector.Detection(
        class_id=1,
        class_name="Other",
        confidence=0.80,
        bbox_xyxy=(12.0, 12.0, 48.0, 48.0),
    )

    kept = instance._global_nms([first, second])

    assert len(kept) == 2


def test_tiled_predict_remaps_boxes_and_preserves_provenance(
    monkeypatch,
    tmp_path,
):
    model = _make_detector(
        monkeypatch,
        tmp_path,
        tiling_enabled=True,
    )

    tile_result = FakeResult(
        FakeBoxes(
            boxes=[[10.0, 20.0, 40.0, 60.0]],
            confidences=[0.90],
            classes=[0],
        )
    )

    model.model.predict = lambda **kwargs: [tile_result]

    image = np.zeros((640, 640, 3), dtype=np.uint8)

    result = model.predict(image)    # Four tiles are generated. Each tile's local box is remapped
    # into a different location in the original 640x640 image.
    assert len(result.detections) == 4

    boxes = {
        detection.bbox_xyxy
        for detection in result.detections
    }

    assert boxes == {
        (10.0, 20.0, 40.0, 60.0),
        (266.0, 20.0, 296.0, 60.0),
        (10.0, 276.0, 40.0, 316.0),
        (266.0, 276.0, 296.0, 316.0),
    }

    box = result.detections[0].bbox_xyxy
    assert box == (10.0, 20.0, 40.0, 60.0)


def test_disabled_tiling_uses_full_frame_path(
    monkeypatch,
    tmp_path,
):
    model = _make_detector(
        monkeypatch,
        tmp_path,
        tiling_enabled=False,
    )

    tile_result = FakeResult(
        FakeBoxes(
            boxes=[[5.0, 6.0, 30.0, 40.0]],
            confidences=[0.88],
            classes=[0],
        )
    )

    calls = []

    def fake_predict(**kwargs):
        calls.append(kwargs)
        return [tile_result]

    model.model.predict = fake_predict

    image = np.zeros((640, 640, 3), dtype=np.uint8)

    result = model.predict(image)

    assert len(calls) == 1
    assert len(result.detections) == 1
    assert result.detections[0].bbox_xyxy == (
        5.0,
        6.0,
        30.0,
        40.0,
    )
