from datetime import datetime

from pydantic import BaseModel


class JobReportEvidence(BaseModel):
    evidence_available: bool | None
    evidence_index: float | None
    interpretation: str | None
    intensity_contrast: float | None
    edge_density: float | None
    shape_compactness: float | None
    shadow_candidate_score: float | None
    shadow_candidate_direction: str | None
    physical_shadow_direction_available: bool | None


class JobReportReview(BaseModel):
    id: int
    decision: str
    note: str | None
    created_at: datetime
    reviewed_at: datetime | None


class JobReportTrack(BaseModel):
    id: int
    sequence_id: str
    class_name: str
    first_frame: int
    last_frame: int
    detection_count: int
    mean_confidence: float
    max_confidence: float
    persistence_score: float
    created_at: datetime


class JobReportDetection(BaseModel):
    id: int
    frame_id: int
    frame_index: int

    class_name: str
    class_id: int
    confidence: float

    x1: float
    y1: float
    x2: float
    y2: float

    inference_ms: float
    model_name: str
    model_version: str

    track_id: int | None

    timestamp: datetime | None
    latitude: float | None
    longitude: float | None
    heading_deg: float | None
    metadata_verified: bool

    image_width: int
    image_height: int
    image_url: str | None

    evidence: JobReportEvidence | None
    review: JobReportReview | None
    track: JobReportTrack | None


class JobReportFrame(BaseModel):
    id: int
    frame_index: int
    source_id: str
    sequence_id: str

    width: int
    height: int

    quality_index: float | None
    quality_status: str | None
    quality_usable: bool | None

    timestamp: datetime | None
    latitude: float | None
    longitude: float | None
    heading_deg: float | None
    metadata_verified: bool

    detection_count: int


class JobReportResponse(BaseModel):
    generated_at: datetime

    job_id: int
    status: str
    modality: str

    source_id: str
    sequence_id: str | None
    source_checksum: str

    pipeline_version: str
    model_name: str
    model_version: str

    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    preprocessing_ms: float | None
    inference_ms: float | None
    evidence_ms: float | None
    tracking_ms: float | None

    error_message: str | None

    frame_count: int
    processed_frame_count: int
    detection_count: int

    pending_review_count: int
    accepted_review_count: int
    rejected_review_count: int

    located_detection_count: int

    frames: list[JobReportFrame]
    detections: list[JobReportDetection]
