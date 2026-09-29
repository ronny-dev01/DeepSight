from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.api.db import get_db
from services.api.models import (
    AcousticEvidence,
    Detection,
    DetectionReview,
    IngestionJob,
    SonarFrame,
    Track,
)
from services.api.schemas.report import (
    JobReportDetection,
    JobReportEvidence,
    JobReportFrame,
    JobReportResponse,
    JobReportReview,
    JobReportTrack,
)


router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


@router.get(
    "/jobs/{job_id}",
    response_model=JobReportResponse,
)
def get_job_report(
    job_id: int,
    db: Session = Depends(get_db),
) -> JobReportResponse:
    try:
        job = db.get(IngestionJob, job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Ingestion job not found.",
            )

        frames = (
            db.query(SonarFrame)
            .filter(SonarFrame.job_id == job.id)
            .order_by(SonarFrame.frame_index)
            .all()
        )

        frame_ids = [frame.id for frame in frames]

        detections = (
            db.query(Detection)
            .filter(Detection.frame_id.in_(frame_ids))
            .order_by(
                Detection.frame_id,
                Detection.id,
            )
            .all()
            if frame_ids
            else []
        )

        detection_ids = [detection.id for detection in detections]

        evidence_rows = (
            db.query(AcousticEvidence)
            .filter(
                AcousticEvidence.detection_id.in_(detection_ids)
            )
            .all()
            if detection_ids
            else []
        )

        review_rows = (
            db.query(DetectionReview)
            .filter(
                DetectionReview.detection_id.in_(detection_ids)
            )
            .all()
            if detection_ids
            else []
        )

        track_ids = sorted(
            {
                detection.track_id
                for detection in detections
                if detection.track_id is not None
            }
        )

        track_rows = (
            db.query(Track)
            .filter(Track.id.in_(track_ids))
            .all()
            if track_ids
            else []
        )

        frames_by_id = {
            frame.id: frame
            for frame in frames
        }
        evidence_by_detection_id = {
            evidence.detection_id: evidence
            for evidence in evidence_rows
        }
        reviews_by_detection_id = {
            review.detection_id: review
            for review in review_rows
        }
        tracks_by_id = {
            track.id: track
            for track in track_rows
        }

        frame_detection_counts = {
            frame.id: 0
            for frame in frames
        }

        for detection in detections:
            frame_detection_counts[detection.frame_id] += 1

        processed_frame_count = sum(
            1
            for frame in frames
            if frame.quality_index is not None
        )

        review_counts = {
            "pending": 0,
            "accepted": 0,
            "rejected": 0,
        }

        for review in review_rows:
            if review.decision in review_counts:
                review_counts[review.decision] += 1

        located_detection_count = sum(
            1
            for detection in detections
            if (
                frames_by_id[detection.frame_id].latitude is not None
                and frames_by_id[detection.frame_id].longitude is not None
            )
        )

        sequence_id = (
            frames[0].sequence_id
            if frames
            else None
        )

        report_frames = [
            JobReportFrame(
                id=frame.id,
                frame_index=frame.frame_index,
                source_id=frame.source_id,
                sequence_id=frame.sequence_id,
                width=frame.width,
                height=frame.height,
                quality_index=frame.quality_index,
                quality_status=frame.quality_status,
                quality_usable=frame.quality_usable,
                timestamp=frame.timestamp,
                latitude=frame.latitude,
                longitude=frame.longitude,
                heading_deg=frame.heading_deg,
                metadata_verified=frame.metadata_verified,
                detection_count=frame_detection_counts[frame.id],
            )
            for frame in frames
        ]

        report_detections = []

        for detection in detections:
            frame = frames_by_id[detection.frame_id]
            evidence = evidence_by_detection_id.get(detection.id)
            review = reviews_by_detection_id.get(detection.id)

            report_evidence = (
                JobReportEvidence(
                    evidence_available=evidence.evidence_available,
                    evidence_index=evidence.evidence_index,
                    interpretation=evidence.interpretation,
                    intensity_contrast=evidence.intensity_contrast,
                    edge_density=evidence.edge_density,
                    shape_compactness=evidence.shape_compactness,
                    shadow_candidate_score=evidence.shadow_candidate_score,
                    shadow_candidate_direction=(
                        evidence.shadow_candidate_direction
                    ),
                    physical_shadow_direction_available=(
                        evidence.physical_shadow_direction_available
                    ),
                )
                if evidence is not None
                else None
            )

            report_review = (
                JobReportReview(
                    id=review.id,
                    decision=review.decision,
                    note=review.note,
                    created_at=review.created_at,
                    reviewed_at=review.reviewed_at,
                )
                if review is not None
                else None
            )

            report_track = None

            if detection.track_id is not None:
                track = tracks_by_id.get(detection.track_id)

                if track is not None:
                    report_track = JobReportTrack(
                        id=track.id,
                        sequence_id=track.sequence_id,
                        class_name=track.class_name,
                        first_frame=track.first_frame,
                        last_frame=track.last_frame,
                        detection_count=track.detection_count,
                        mean_confidence=track.mean_confidence,
                        max_confidence=track.max_confidence,
                        persistence_score=track.persistence_score,
                        created_at=track.created_at,
                    )

            report_detections.append(
                JobReportDetection(
                    id=detection.id,
                    frame_id=detection.frame_id,
                    frame_index=frame.frame_index,
                    class_name=detection.class_name,
                    class_id=detection.class_id,
                    confidence=detection.confidence,
                    x1=detection.x1,
                    y1=detection.y1,
                    x2=detection.x2,
                    y2=detection.y2,
                    inference_ms=detection.inference_ms,
                    model_name=detection.model_name,
                    model_version=detection.model_version,
                    track_id=detection.track_id,
                    timestamp=frame.timestamp,
                    latitude=frame.latitude,
                    longitude=frame.longitude,
                    heading_deg=frame.heading_deg,
                    metadata_verified=frame.metadata_verified,
                    image_width=frame.width,
                    image_height=frame.height,
                    image_url=(
                        f"/reviews/{review.id}/image"
                        if review is not None
                        else None
                    ),
                    evidence=report_evidence,
                    review=report_review,
                    track=report_track,
                )
            )

        return JobReportResponse(
            generated_at=datetime.now(timezone.utc),
            job_id=job.id,
            status=job.status,
            modality=job.modality,
            source_id=job.source_id,
            sequence_id=sequence_id,
            source_checksum=job.source_checksum,
            pipeline_version=job.pipeline_version,
            model_name=job.model_name,
            model_version=job.model_version,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            preprocessing_ms=job.preprocessing_ms,
            inference_ms=job.inference_ms,
            evidence_ms=job.evidence_ms,
            tracking_ms=job.tracking_ms,
            error_message=job.error_message,
            frame_count=len(frames),
            processed_frame_count=processed_frame_count,
            detection_count=len(detections),
            pending_review_count=review_counts["pending"],
            accepted_review_count=review_counts["accepted"],
            rejected_review_count=review_counts["rejected"],
            located_detection_count=located_detection_count,
            frames=report_frames,
            detections=report_detections,
        )

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Job report data temporarily unavailable.",
        ) from exc
