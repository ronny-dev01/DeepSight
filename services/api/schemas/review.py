from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ReviewDecision = Literal["pending", "accepted", "rejected"]


class DetectionReviewUpdate(BaseModel):
    decision: Literal["accepted", "rejected"]
    note: str | None = Field(
        default=None,
        max_length=2000,
    )


class DetectionReviewResponse(BaseModel):
    id: int
    detection_id: int
    decision: ReviewDecision
    note: str | None

    created_at: datetime
    reviewed_at: datetime | None

    class_name: str
    class_id: int
    confidence: float

    x1: float
    y1: float
    x2: float
    y2: float

    model_name: str
    model_version: str

    frame_id: int
    source_id: str
    sequence_id: str
    frame_index: int

    image_width: int
    image_height: int
    image_url: str

    timestamp: datetime | None
    latitude: float | None
    longitude: float | None
    heading_deg: float | None
    metadata_verified: bool

    track_id: int | None

    evidence_available: bool | None
    evidence_index: float | None
    interpretation: str | None
    intensity_contrast: float | None
    edge_density: float | None
    shape_compactness: float | None
    shadow_candidate_score: float | None
    shadow_candidate_direction: str | None
    physical_shadow_direction_available: bool | None


class DetectionReviewListResponse(BaseModel):
    items: list[DetectionReviewResponse]
    total: int
    page: int
    page_size: int
    pages: int
