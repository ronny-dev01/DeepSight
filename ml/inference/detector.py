from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
from ultralytics import YOLO

from services.api.config import settings
from .registry import verify_model_artifact
from .schema import Detection, DetectionResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "storage"
    / "runs"
    / "crab_pot_full"
    / "weights"
    / "best.pt"
)

DEFAULT_CONFIDENCE = 0.25
DEFAULT_IOU = 0.45
DEFAULT_IMAGE_SIZE = 640


class MarineDetector:
    """
    Reusable YOLO detector.

    The model is loaded once when the detector is constructed.
    No model reload occurs for individual frames.

    Tiled inference is optional and disabled by default. When enabled,
    overlapping tiles are inferred independently, remapped to original
    image coordinates, and merged using global class-aware NMS.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        confidence: float | None = None,
        iou: float | None = None,
        image_size: int | None = None,
        device: str | None = None,
        tiling_enabled: bool | None = None,
        tile_size: int | None = None,
        tile_stride: int | None = None,
        tile_iou: float | None = None,
        tile_nms_iou: float | None = None,
    ) -> None:
        configured_path = (
            model_path
            or os.getenv("MARINE_MODEL_PATH")
            or settings.model_path
            or DEFAULT_MODEL_PATH
        )

        self.model_path = Path(configured_path)

        if not self.model_path.is_absolute():
            self.model_path = PROJECT_ROOT / self.model_path

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        self.model_name = settings.model_name
        self.model_version = settings.model_version

        if settings.model_verify_hash:
            verify_model_artifact(
                registry_path=settings.model_registry_path,
                project_root=PROJECT_ROOT,
                model_name=self.model_name,
                model_version=self.model_version,
                model_path=self.model_path,
            )

        resolved_confidence = (
            settings.model_confidence
            if confidence is None
            else confidence
        )
        resolved_iou = (
            settings.model_iou
            if iou is None
            else iou
        )
        resolved_image_size = (
            settings.model_image_size
            if image_size is None
            else image_size
        )
        resolved_device = (
            settings.model_device
            if device is None
            else device
        )
        resolved_tiling_enabled = (
            settings.model_tiling_enabled
            if tiling_enabled is None
            else tiling_enabled
        )
        resolved_tile_size = (
            settings.model_tile_size
            if tile_size is None
            else tile_size
        )
        resolved_tile_stride = (
            settings.model_tile_stride
            if tile_stride is None
            else tile_stride
        )
        resolved_tile_iou = (
            settings.model_tile_iou
            if tile_iou is None
            else tile_iou
        )
        resolved_tile_nms_iou = (
            settings.model_tile_nms_iou
            if tile_nms_iou is None
            else tile_nms_iou
        )

        if resolved_confidence <= 0.0 or resolved_confidence >= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if resolved_iou <= 0.0 or resolved_iou >= 1.0:
            raise ValueError(
                "iou must be between 0 and 1"
            )

        if resolved_image_size <= 0:
            raise ValueError(
                "image_size must be positive"
            )

        if not isinstance(resolved_device, str) or not resolved_device.strip():
            raise ValueError(
                "device must be a non-empty string"
            )

        if not isinstance(resolved_tiling_enabled, bool):
            raise ValueError(
                "tiling_enabled must be a boolean"
            )

        if resolved_tile_size <= 0:
            raise ValueError(
                "tile_size must be positive"
            )

        if resolved_tile_stride <= 0:
            raise ValueError(
                "tile_stride must be positive"
            )

        if resolved_tile_stride > resolved_tile_size:
            raise ValueError(
                "tile_stride must be less than or equal to tile_size"
            )

        if resolved_tile_iou <= 0.0 or resolved_tile_iou >= 1.0:
            raise ValueError(
                "tile_iou must be between 0 and 1"
            )

        if resolved_tile_nms_iou <= 0.0 or resolved_tile_nms_iou >= 1.0:
            raise ValueError(
                "tile_nms_iou must be between 0 and 1"
            )

        self.confidence = resolved_confidence
        self.iou = resolved_iou
        self.image_size = resolved_image_size
        self.device = resolved_device

        self.tiling_enabled = resolved_tiling_enabled
        self.tile_size = resolved_tile_size
        self.tile_stride = resolved_tile_stride
        self.tile_iou = resolved_tile_iou
        self.tile_nms_iou = resolved_tile_nms_iou

        self.model = YOLO(str(self.model_path))

        names = self.model.names

        if isinstance(names, dict):
            self.class_names = {
                int(class_id): str(name)
                for class_id, name in names.items()
            }
        else:
            self.class_names = {
                class_id: str(name)
                for class_id, name in enumerate(names)
            }

    @staticmethod
    def _validate_image(image: np.ndarray) -> None:
        if not isinstance(image, np.ndarray):
            raise TypeError(
                "image must be a numpy.ndarray"
            )

        if image.size == 0:
            raise ValueError("image is empty")

        if image.ndim not in (2, 3):
            raise ValueError(
                f"unsupported image dimensions: {image.shape}"
            )

    @staticmethod
    def _tile_origins(
        length: int,
        tile_size: int,
        stride: int,
    ) -> tuple[int, ...]:
        if length <= tile_size:
            return (0,)

        last_origin = length - tile_size
        origins = list(range(0, last_origin + 1, stride))

        if origins[-1] != last_origin:
            origins.append(last_origin)

        return tuple(origins)

    @staticmethod
    def _bbox_iou(
        left: tuple[float, float, float, float],
        right: tuple[float, float, float, float],
    ) -> float:
        left_x1, left_y1, left_x2, left_y2 = left
        right_x1, right_y1, right_x2, right_y2 = right

        intersection_x1 = max(left_x1, right_x1)
        intersection_y1 = max(left_y1, right_y1)
        intersection_x2 = min(left_x2, right_x2)
        intersection_y2 = min(left_y2, right_y2)

        intersection_width = max(
            0.0,
            intersection_x2 - intersection_x1,
        )
        intersection_height = max(
            0.0,
            intersection_y2 - intersection_y1,
        )

        intersection_area = (
            intersection_width * intersection_height
        )

        left_area = (
            max(0.0, left_x2 - left_x1)
            * max(0.0, left_y2 - left_y1)
        )
        right_area = (
            max(0.0, right_x2 - right_x1)
            * max(0.0, right_y2 - right_y1)
        )

        union_area = (
            left_area
            + right_area
            - intersection_area
        )

        if union_area <= 0.0:
            return 0.0

        return intersection_area / union_area

    def _global_nms(
        self,
        detections: list[Detection],
    ) -> tuple[Detection, ...]:
        if not detections:
            return ()

        ordered = sorted(
            detections,
            key=lambda detection: detection.confidence,
            reverse=True,
        )

        kept: list[Detection] = []

        for candidate in ordered:
            suppress = False

            for existing in kept:
                if candidate.class_id != existing.class_id:
                    continue

                if (
                    self._bbox_iou(
                        candidate.bbox_xyxy,
                        existing.bbox_xyxy,
                    )
                    >= self.tile_nms_iou
                ):
                    suppress = True
                    break

            if not suppress:
                kept.append(candidate)

        return tuple(kept)

    def _detections_from_result(
        self,
        result,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> list[Detection]:
        if result.boxes is None:
            return []

        xyxy = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        class_ids = (
            result.boxes.cls.cpu().numpy().astype(int)
        )

        parsed: list[Detection] = []

        for box, confidence, class_id in zip(
            xyxy,
            confidences,
            class_ids,
        ):
            class_name = self.class_names.get(
                int(class_id),
                f"class_{class_id}",
            )

            parsed.append(
                Detection(
                    class_id=int(class_id),
                    class_name=class_name,
                    confidence=float(confidence),
                    bbox_xyxy=(
                        float(box[0]) + offset_x,
                        float(box[1]) + offset_y,
                        float(box[2]) + offset_x,
                        float(box[3]) + offset_y,
                    ),
                )
            )

        return parsed

    def _run_model(self, image: np.ndarray):
        return self.model.predict(
            source=image,
            conf=self.confidence,
            iou=self.iou,
            imgsz=self.image_size,
            device=self.device,
            verbose=False,
        )

    def _run_tiled_model(
        self,
        image: np.ndarray,
    ) -> tuple[Detection, ...]:
        height, width = image.shape[:2]

        x_origins = self._tile_origins(
            width,
            self.tile_size,
            self.tile_stride,
        )
        y_origins = self._tile_origins(
            height,
            self.tile_size,
            self.tile_stride,
        )

        detections: list[Detection] = []

        for y_origin in y_origins:
            for x_origin in x_origins:
                tile = image[
                    y_origin : min(
                        y_origin + self.tile_size,
                        height,
                    ),
                    x_origin : min(
                        x_origin + self.tile_size,
                        width,
                    ),
                ].copy()

                results = self.model.predict(
                    source=tile,
                    conf=self.confidence,
                    iou=self.tile_iou,
                    imgsz=self.image_size,
                    device=self.device,
                    verbose=False,
                )

                if not results:
                    continue

                detections.extend(
                    self._detections_from_result(
                        results[0],
                        offset_x=float(x_origin),
                        offset_y=float(y_origin),
                    )
                )

        return self._global_nms(detections)

    def warm_up(self, image: np.ndarray) -> float:
        """
        Warm the loaded model/runtime using a real source image.

        The warm-up result is intentionally discarded and is never
        exposed as a detection.
        """
        self._validate_image(image)

        started = time.perf_counter()

        if self.tiling_enabled:
            self._run_tiled_model(image)
        else:
            self._run_model(image)

        return (
            time.perf_counter() - started
        ) * 1000.0

    def predict(
        self,
        image: np.ndarray,
    ) -> DetectionResult:
        self._validate_image(image)

        height, width = image.shape[:2]

        started = time.perf_counter()

        if self.tiling_enabled:
            detections = self._run_tiled_model(image)
        else:
            results = self._run_model(image)

            if not results:
                detections = ()
            else:
                detections = tuple(
                    self._detections_from_result(results[0])
                )

        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000.0

        return DetectionResult(
            model_path=str(self.model_path),
            model_name=self.model_name,
            model_version=self.model_version,
            image_width=int(width),
            image_height=int(height),
            inference_ms=float(elapsed_ms),
            detections=detections,
        )


def load_default_detector() -> MarineDetector:
    return MarineDetector()
