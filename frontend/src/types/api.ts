export type JobStatus =
    | "queued"
    | "running"
    | "succeeded"
    | "failed"
    | string

export interface IngestionJobSummary {
    id: number
    status: JobStatus
    modality: "side_scan_sonar"
    source_id: string
    pipeline_version: string
    model_name: string
    model_version: string
    frame_count: number
    processed_frame_count: number
    detection_count: number
    created_at: string
    started_at: string | null
    completed_at: string | null
    error_message: string | null
}

export interface IngestionJobListResponse {
    items: IngestionJobSummary[]
    total: number
    page: number
    page_size: number
    pages: number
}

export interface IngestionJobStatus {
    id: number
    status: JobStatus
    modality: "side_scan_sonar"
    source_id: string
    source_checksum: string
    sequence_id: string | null
    pipeline_version: string
    model_name: string
    model_version: string
    frame_count: number
    processed_frame_count: number
    detection_count: number
    started_at: string | null
    completed_at: string | null
    preprocessing_ms: number | null
    inference_ms: number | null
    evidence_ms: number | null
    tracking_ms: number | null
    error_message: string | null
}

export type ReviewDecision =
    | "pending"
    | "accepted"
    | "rejected"

export interface DetectionReview {
    id: number
    detection_id: number
    decision: ReviewDecision
    note: string | null
    created_at: string
    reviewed_at: string | null

    class_name: string
    class_id: number
    confidence: number

    x1: number
    y1: number
    x2: number
    y2: number

    model_name: string
    model_version: string

    frame_id: number
    source_id: string
    sequence_id: string
    frame_index: number

    image_width: number
    image_height: number
    image_url: string

    timestamp: string | null
    latitude: number | null
    longitude: number | null
    heading_deg: number | null
    metadata_verified: boolean

    track_id: number | null

    evidence_available: boolean | null
    evidence_index: number | null
    interpretation: string | null
    intensity_contrast: number | null
    edge_density: number | null
    shape_compactness: number | null
    shadow_candidate_score: number | null
    shadow_candidate_direction: string | null
    physical_shadow_direction_available: boolean | null
}

export interface DetectionReviewListResponse {
    items: DetectionReview[]
    total: number
    page: number
    page_size: number
    pages: number
}

export interface DetectionReviewUpdate {
    decision: "accepted" | "rejected"
    note?: string | null
}
export interface IngestionJobResponse {
    id: number
    status: JobStatus
    modality: "side_scan_sonar"
    source_id: string
    sequence_id: string
    frame_count: number
    source_checksum: string
}
