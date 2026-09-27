from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from sqlalchemy import select

from ml.tracking import DeterministicTracker, TrackDetection
from services.api.config import settings
from services.api.db import SessionLocal
from services.api.models import (
    AcousticEvidence,
    Detection,
    DetectionReview,
    IngestionJob,
    SonarFrame,
    Track,
)
from services.worker.pipeline import SSSFramePipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_VERSION = "sss-frame-pipeline-v1"

_pipeline: SSSFramePipeline | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_pipeline() -> SSSFramePipeline:
    global _pipeline

    if _pipeline is None:
        _pipeline = SSSFramePipeline()

    return _pipeline


def process_ingestion_job(
    job_id: int,
) -> dict[str, int | float | str]:
    db = SessionLocal()

    try:
        job = db.get(IngestionJob, job_id)

        if job is None:
            raise ValueError(
                f"Ingestion job not found: {job_id}"
            )

        if job.modality != "side_scan_sonar":
            raise ValueError(
                f"Unsupported ingestion modality: {job.modality}"
            )

        if job.status != "queued":
            return {
                "job_id": job.id,
                "status": job.status,
                "frames_processed": 0,
                "detections_total": 0,
            }

        frames = list(
            db.scalars(
                select(SonarFrame)
                .where(SonarFrame.job_id == job.id)
                .order_by(SonarFrame.frame_index)
            )
        )

        if not frames:
            raise ValueError(
                f"Ingestion job {job.id} contains no SSS frames"
            )

        indices = [
            frame.frame_index
            for frame in frames
        ]

        if indices != list(range(len(frames))):
            raise ValueError(
                "SSS frame indices must be contiguous starting at 0"
            )

        if any(
            frame.modality != "side_scan_sonar"
            for frame in frames
        ):
            raise ValueError(
                "Job contains a non-SSS frame"
            )

        pipeline = _get_pipeline()
        job.status = "running"
        job.started_at = _utcnow()
        job.error_message = None
        job.pipeline_version = PIPELINE_VERSION
        job.model_name = pipeline.detector.model_name
        job.model_version = pipeline.detector.model_version

        db.commit()

        frames_processed = 0
        detections_total = 0
        total_inference_ms = 0.0
        total_preprocessing_ms = 0.0
        total_evidence_ms = 0.0
        total_processing_ms = 0.0
        total_tracking_ms = 0.0

        tracker = DeterministicTracker()
        db_track_ids: dict[int, int] = {}

        for frame in frames:
            image_path = (
                PROJECT_ROOT / frame.image_path
            )

            started = perf_counter()

            result = pipeline.process_frame(
                image_path
            )

            elapsed_ms = (
                perf_counter() - started
            ) * 1000.0

            frame.quality_index = (
                result.quality.quality_index
            )
            frame.quality_status = (
                result.quality.status
            )
            frame.quality_usable = (
                result.quality.usable
            )

            frames_processed += 1
            total_processing_ms += elapsed_ms
            total_preprocessing_ms += (
                result.preprocessing_ms
            )
            total_evidence_ms += (
                result.evidence_ms
            )

            detection_result = (
                result.detection_result
            )

            tracking_detections: list[TrackDetection] = []

            if detection_result is not None:
                tracking_detections = [
                    TrackDetection(
                        frame_index=frame.frame_index,
                        detection_index=detection_index,
                        class_id=detection.class_id,
                        class_name=detection.class_name,
                        confidence=detection.confidence,
                        bbox_xyxy=detection.bbox_xyxy,
                    )
                    for detection_index, detection in enumerate(
                        detection_result.detections
                    )
                ]

            tracking_started = perf_counter()

            tracker.update(
                frame.frame_index,
                tracking_detections,
            )

            total_tracking_ms += (
                perf_counter() - tracking_started
            ) * 1000.0

            if detection_result is None:
                continue

            total_inference_ms += (
                detection_result.inference_ms
            )

            detections_total += len(
                detection_result.detections
            )

            current_track_by_detection_index: dict[
                int,
                int,
            ] = {}

            for candidate_track in tracker.tracks():
                for track_detection in candidate_track.detections:
                    if (
                        track_detection.frame_index
                        == frame.frame_index
                    ):
                        current_track_by_detection_index[
                            track_detection.detection_index
                        ] = candidate_track.track_id

                db_track_id = db_track_ids.get(
                    candidate_track.track_id
                )

                if db_track_id is None:
                    stored_track = Track(
                        sequence_id=frame.sequence_id,
                        class_name=candidate_track.dominant_class,
                        first_frame=candidate_track.first_frame,
                        last_frame=candidate_track.last_frame,
                        detection_count=candidate_track.detection_count,
                        mean_confidence=candidate_track.mean_confidence,
                        max_confidence=candidate_track.max_confidence,
                        persistence_score=candidate_track.persistence_score,
                    )
                    db.add(stored_track)
                    db.flush()

                    db_track_ids[
                        candidate_track.track_id
                    ] = stored_track.id
                else:
                    stored_track = db.get(
                        Track,
                        db_track_id,
                    )

                    if stored_track is None:
                        raise ValueError(
                            "Persisted tracking state is missing "
                            f"for logical track {candidate_track.track_id}"
                        )

                    stored_track.class_name = (
                        candidate_track.dominant_class
                    )
                    stored_track.first_frame = (
                        candidate_track.first_frame
                    )
                    stored_track.last_frame = (
                        candidate_track.last_frame
                    )
                    stored_track.detection_count = (
                        candidate_track.detection_count
                    )
                    stored_track.mean_confidence = (
                        candidate_track.mean_confidence
                    )
                    stored_track.max_confidence = (
                        candidate_track.max_confidence
                    )
                    stored_track.persistence_score = (
                        candidate_track.persistence_score
                    )

            for detection_index, detection in enumerate(
                detection_result.detections
            ):
                logical_track_id = (
                    current_track_by_detection_index.get(
                        detection_index
                    )
                )

                if logical_track_id is None:
                    raise ValueError(
                        "Tracker did not assign a track to "
                        f"frame {frame.frame_index}, "
                        f"detection {detection_index}"
                    )

                stored_detection = Detection(
                    frame_id=frame.id,
                    track_id=db_track_ids[logical_track_id],
                    class_name=detection.class_name,
                    class_id=detection.class_id,
                    confidence=detection.confidence,
                    x1=detection.bbox_xyxy[0],
                    y1=detection.bbox_xyxy[1],
                    x2=detection.bbox_xyxy[2],
                    y2=detection.bbox_xyxy[3],
                    inference_ms=(
                        detection_result.inference_ms
                    ),
                    model_name=detection_result.model_name,
                    model_version=detection_result.model_version,
                )

                db.add(stored_detection)
                db.flush()

                evidence = (
                    result.evidence[detection_index]
                )
                fusion = (
                    result.fusion[detection_index]
                )

                db.add(
                    AcousticEvidence(
                        detection_id=stored_detection.id,
                        object_mean_intensity=(
                            evidence.object_mean_intensity
                        ),
                        object_std_intensity=(
                            evidence.object_std_intensity
                        ),
                        background_mean_intensity=(
                            evidence.background_mean_intensity
                        ),
                        background_std_intensity=(
                            evidence.background_std_intensity
                        ),
                        intensity_contrast=(
                            evidence.intensity_contrast
                        ),
                        edge_density=(
                            evidence.edge_density
                        ),
                        shape_compactness=(
                            evidence.shape_compactness
                        ),
                        shadow_candidate_score=(
                            evidence.shadow_candidate_support
                        ),
                        shadow_candidate_direction=(
                            evidence.shadow_candidate_direction
                        ),
                        physical_shadow_direction_available=(
                            evidence.physical_shadow_direction_available
                        ),
                        evidence_available=(
                            evidence.evidence_available
                        ),
                        evidence_index=(
                            fusion.heuristic_evidence_index
                        ),
                        interpretation=(
                            fusion.interpretation
                        ),
                    )
                )

                db.add(
                    DetectionReview(
                        detection_id=stored_detection.id,
                        decision="pending",
                    )
                )

        job.inference_ms = (
            total_inference_ms
        )

        job.preprocessing_ms = (
            total_preprocessing_ms
        )
        job.evidence_ms = (
            total_evidence_ms
        )
        job.tracking_ms = (
            total_tracking_ms
        )

        job.status = "succeeded"
        job.completed_at = _utcnow()
        job.error_message = None

        db.commit()

        return {
            "job_id": job.id,
            "status": job.status,
            "frames_processed": frames_processed,
            "detections_total": detections_total,
            "inference_ms": round(
                total_inference_ms,
                3,
            ),
            "processing_ms": round(
                total_processing_ms,
                3,
            ),
        }

    except Exception as exc:
        db.rollback()

        failed_job = db.get(
            IngestionJob,
            job_id,
        )

        if failed_job is not None:
            failed_job.status = "failed"
            failed_job.completed_at = _utcnow()
            failed_job.error_message = str(exc)
            db.commit()

        raise

    finally:
        db.close()
