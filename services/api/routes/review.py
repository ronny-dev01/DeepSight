from datetime import datetime, timezone
from pathlib import Path
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.api.db import get_db
from services.api.models import (
    AcousticEvidence,
    Detection,
    DetectionReview,
    IngestionJob,
    SonarFrame,
)
from services.api.schemas.review import (
    DetectionReviewListResponse,
    DetectionReviewResponse,
    DetectionReviewUpdate,
    ReviewDecision,
)
from services.api.services.ingestion import PROJECT_ROOT


router = APIRouter(
    prefix="/reviews",
    tags=["human-review"],
)


def _build_review_response(
    review: DetectionReview,
    detection: Detection,
    frame: SonarFrame,
    evidence: AcousticEvidence | None,
) -> DetectionReviewResponse:
    return DetectionReviewResponse(
        id=review.id,
        detection_id=detection.id,
        decision=review.decision,
        note=review.note,
        created_at=review.created_at,
        reviewed_at=review.reviewed_at,
        class_name=detection.class_name,
        class_id=detection.class_id,
        confidence=detection.confidence,
        x1=detection.x1,
        y1=detection.y1,
        x2=detection.x2,
        y2=detection.y2,
        model_name=detection.model_name,
        model_version=detection.model_version,
        frame_id=frame.id,
        source_id=frame.source_id,
        sequence_id=frame.sequence_id,
        frame_index=frame.frame_index,
        image_width=frame.width,
        image_height=frame.height,
        image_url=f"/reviews/{review.id}/image",
        timestamp=frame.timestamp,
        latitude=frame.latitude,
        longitude=frame.longitude,
        heading_deg=frame.heading_deg,
        metadata_verified=frame.metadata_verified,
        track_id=detection.track_id,
        evidence_available=(
            evidence.evidence_available
            if evidence is not None
            else None
        ),
        evidence_index=(
            evidence.evidence_index
            if evidence is not None
            else None
        ),
        interpretation=(
            evidence.interpretation
            if evidence is not None
            else None
        ),
        intensity_contrast=(
            evidence.intensity_contrast
            if evidence is not None
            else None
        ),
        edge_density=(
            evidence.edge_density
            if evidence is not None
            else None
        ),
        shape_compactness=(
            evidence.shape_compactness
            if evidence is not None
            else None
        ),
        shadow_candidate_score=(
            evidence.shadow_candidate_score
            if evidence is not None
            else None
        ),
        shadow_candidate_direction=(
            evidence.shadow_candidate_direction
            if evidence is not None
            else None
        ),
        physical_shadow_direction_available=(
            evidence.physical_shadow_direction_available
            if evidence is not None
            else None
        ),
    )


@router.get(
    "",
    response_model=DetectionReviewListResponse,
)
def list_detection_reviews(
    decision: ReviewDecision = Query(default="pending"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DetectionReviewListResponse:
    try:
        total = (
            db.query(func.count(DetectionReview.id))
            .filter(
                DetectionReview.decision == decision,
            )
            .scalar()
            or 0
        )

        rows = (
            db.query(
                DetectionReview,
                Detection,
                SonarFrame,
                AcousticEvidence,
            )
            .join(
                Detection,
                Detection.id == DetectionReview.detection_id,
            )
            .join(
                SonarFrame,
                SonarFrame.id == Detection.frame_id,
            )
            .outerjoin(
                AcousticEvidence,
                AcousticEvidence.detection_id == Detection.id,
            )
            .filter(
                DetectionReview.decision == decision,
            )
            .order_by(DetectionReview.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [
            _build_review_response(
                review,
                detection,
                frame,
                evidence,
            )
            for review, detection, frame, evidence in rows
        ]

        pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return DetectionReviewListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Human review data temporarily unavailable.",
        ) from exc


@router.get(
    "/job/{job_id}",
    response_model=DetectionReviewListResponse,
)
def list_job_detection_reviews(
    job_id: int,
    decision: ReviewDecision | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DetectionReviewListResponse:
    try:
        job = db.get(IngestionJob, job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Ingestion job not found.",
            )

        base_query = (
            db.query(
                DetectionReview,
                Detection,
                SonarFrame,
                AcousticEvidence,
            )
            .join(
                Detection,
                Detection.id == DetectionReview.detection_id,
            )
            .join(
                SonarFrame,
                SonarFrame.id == Detection.frame_id,
            )
            .outerjoin(
                AcousticEvidence,
                AcousticEvidence.detection_id == Detection.id,
            )
            .filter(
                SonarFrame.job_id == job.id,
            )
        )

        if decision is not None:
            base_query = base_query.filter(
                DetectionReview.decision == decision,
            )

        total = (
            base_query.with_entities(
                func.count(DetectionReview.id),
            )
            .scalar()
            or 0
        )

        rows = (
            base_query
            .order_by(DetectionReview.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [
            _build_review_response(
                review,
                detection,
                frame,
                evidence,
            )
            for review, detection, frame, evidence in rows
        ]

        pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return DetectionReviewListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Review data is temporarily unavailable.",
        ) from exc


@router.get(
    "/{review_id}",
    response_model=DetectionReviewResponse,
)
def get_detection_review(
    review_id: int,
    db: Session = Depends(get_db),
) -> DetectionReviewResponse:
    row = (
        db.query(
            DetectionReview,
            Detection,
            SonarFrame,
            AcousticEvidence,
        )
        .join(
            Detection,
            Detection.id == DetectionReview.detection_id,
        )
        .join(
            SonarFrame,
            SonarFrame.id == Detection.frame_id,
        )
        .outerjoin(
            AcousticEvidence,
            AcousticEvidence.detection_id == Detection.id,
        )
        .filter(
            DetectionReview.id == review_id,
        )
        .one_or_none()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Detection review not found.",
        )

    return _build_review_response(
        row[0],
        row[1],
        row[2],
        row[3],
    )


@router.put(
    "/{review_id}",
    response_model=DetectionReviewResponse,
)
def finalize_detection_review(
    review_id: int,
    payload: DetectionReviewUpdate,
    db: Session = Depends(get_db),
) -> DetectionReviewResponse:
    try:
        review = (
            db.query(DetectionReview)
            .filter(
                DetectionReview.id == review_id,
            )
            .with_for_update()
            .one_or_none()
        )

        if review is None:
            raise HTTPException(
                status_code=404,
                detail="Detection review not found.",
            )

        if review.decision != "pending":
            raise HTTPException(
                status_code=409,
                detail="Detection review is already finalized.",
            )

        review.decision = payload.decision
        review.note = payload.note
        review.reviewed_at = datetime.now(timezone.utc)

        db.commit()

        row = (
            db.query(
                DetectionReview,
                Detection,
                SonarFrame,
                AcousticEvidence,
            )
            .join(
                Detection,
                Detection.id == DetectionReview.detection_id,
            )
            .join(
                SonarFrame,
                SonarFrame.id == Detection.frame_id,
            )
            .outerjoin(
                AcousticEvidence,
                AcousticEvidence.detection_id == Detection.id,
            )
            .filter(
                DetectionReview.id == review_id,
            )
            .one()
        )

        return _build_review_response(
            row[0],
            row[1],
            row[2],
            row[3],
        )

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Human review update temporarily unavailable.",
        ) from exc


@router.get(
    "/{review_id}/image",
    include_in_schema=False,
)
def get_detection_review_image(
    review_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    row = (
        db.query(
            DetectionReview,
            SonarFrame,
        )
        .join(
            Detection,
            Detection.id == DetectionReview.detection_id,
        )
        .join(
            SonarFrame,
            SonarFrame.id == Detection.frame_id,
        )
        .filter(
            DetectionReview.id == review_id,
        )
        .one_or_none()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Detection review not found.",
        )

    frame = row[1]

    storage_root = (
        PROJECT_ROOT / "storage" / "uploads"
    ).resolve()

    image_path = (
        PROJECT_ROOT / frame.image_path
    ).resolve()

    if storage_root not in image_path.parents:
        raise HTTPException(
            status_code=404,
            detail="Review image not found.",
        )

    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Review image not found.",
        )

    media_type = (
        mimetypes.guess_type(str(image_path))[0]
        or "application/octet-stream"
    )

    return FileResponse(
        image_path,
        media_type=media_type,
        filename=image_path.name,
    )
