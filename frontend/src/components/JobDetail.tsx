import { useEffect, useState } from "react"

import {
    getIngestionJob,
    getJobReviews,
    getReviewImageUrl,
} from "../api/client"

import type {
    DetectionReview,
    IngestionJobStatus,
} from "../types/api"

import "./JobDetail.css"
import OperationalMap from "./OperationalMap"

function formatMs(value: number | null): string {
    return value === null ? "N/A" : `${value.toFixed(1)} ms`
}

function formatDate(value: string | null): string {
    if (!value) {
        return "N/A"
    }

    const date = new Date(value)

    return Number.isNaN(date.getTime())
        ? "N/A"
        : date.toLocaleString()
}

function confidence(value: number): string {
    return `${(value * 100).toFixed(1)}%`
}

function DecisionBadge({
    decision,
}: {
    decision: DetectionReview["decision"]
}) {
    return (
        <span className={`job-detail__decision job-detail__decision--${decision}`}>
            {decision}
        </span>
    )
}

function DetectionCard({
    review,
}: {
    review: DetectionReview
}) {
    const left = `${(review.x1 / review.image_width) * 100}%`
    const top = `${(review.y1 / review.image_height) * 100}%`
    const width = `${((review.x2 - review.x1) / review.image_width) * 100}%`
    const height = `${((review.y2 - review.y1) / review.image_height) * 100}%`

    return (
        <article className="detection-card">
            <div className="detection-card__image">
                <img
                    src={getReviewImageUrl(review)}
                    alt={`Frame ${review.frame_index} detection`}
                />

                <div
                    className="detection-card__bbox"
                    style={{
                        left,
                        top,
                        width,
                        height,
                    }}
                >
                    <span>
                        {review.class_name}{" "}
                        {confidence(review.confidence)}
                    </span>
                </div>
            </div>

            <div className="detection-card__body">
                <div className="detection-card__title">
                    <div>
                        <span className="job-detail__eyebrow">
                            DETECTION #{review.detection_id}
                        </span>

                        <h3>{review.class_name}</h3>
                    </div>

                    <DecisionBadge
                        decision={review.decision}
                    />
                </div>

                <div className="detection-card__grid">
                    <div>
                        <span>Confidence</span>
                        <strong>
                            {confidence(review.confidence)}
                        </strong>
                    </div>

                    <div>
                        <span>Frame</span>
                        <strong>
                            #{review.frame_index}
                        </strong>
                    </div>

                    <div>
                        <span>Evidence</span>
                        <strong>
                            {review.evidence_available
                                ? "Available"
                                : "Unavailable"}
                        </strong>
                    </div>

                    <div>
                        <span>Evidence index</span>
                        <strong>
                            {review.evidence_index !== null
                                ? review.evidence_index.toFixed(3)
                                : "N/A"}
                        </strong>
                    </div>
                </div>

                <div className="detection-card__section">
                    <span className="job-detail__eyebrow">
                        ACOUSTIC EVIDENCE
                    </span>

                    <div className="evidence-grid">
                        <div>
                            <span>Interpretation</span>
                            <strong>
                                {review.interpretation ?? "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Intensity contrast</span>
                            <strong>
                                {review.intensity_contrast !== null
                                    ? review.intensity_contrast.toFixed(3)
                                    : "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Edge density</span>
                            <strong>
                                {review.edge_density !== null
                                    ? review.edge_density.toFixed(3)
                                    : "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Shape compactness</span>
                            <strong>
                                {review.shape_compactness !== null
                                    ? review.shape_compactness.toFixed(3)
                                    : "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Shadow score</span>
                            <strong>
                                {review.shadow_candidate_score !== null
                                    ? review.shadow_candidate_score.toFixed(3)
                                    : "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Shadow direction</span>
                            <strong>
                                {review.shadow_candidate_direction ?? "N/A"}
                            </strong>
                        </div>
                    </div>
                </div>

                <div className="detection-card__section">
                    <span className="job-detail__eyebrow">
                        FRAME METADATA
                    </span>

                    <div className="evidence-grid">
                        <div>
                            <span>Source</span>
                            <strong>{review.source_id}</strong>
                        </div>

                        <div>
                            <span>Sequence</span>
                            <strong>{review.sequence_id}</strong>
                        </div>

                        <div>
                            <span>Dimensions</span>
                            <strong>
                                {review.image_width} ×{" "}
                                {review.image_height}
                            </strong>
                        </div>

                        <div>
                            <span>Metadata verified</span>
                            <strong>
                                {review.metadata_verified
                                    ? "Yes"
                                    : "No"}
                            </strong>
                        </div>

                        <div>
                            <span>Latitude</span>
                            <strong>
                                {review.latitude ?? "Unavailable"}
                            </strong>
                        </div>

                        <div>
                            <span>Longitude</span>
                            <strong>
                                {review.longitude ?? "Unavailable"}
                            </strong>
                        </div>
                    </div>
                </div>

                <div className="detection-card__model">
                    Model: {review.model_name} ·{" "}
                    {review.model_version}
                </div>
            </div>
        </article>
    )
}

export default function JobDetail({
    jobId,
    onClose,
}: {
    jobId: number
    onClose: () => void
}) {
    const [job, setJob] =
        useState<IngestionJobStatus | null>(null)

    const [reviews, setReviews] =
        useState<DetectionReview[]>([])

    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let active = true

        async function load() {
            try {
                setLoading(true)
                setError(null)

                const [jobResponse, reviewResponse] =
                    await Promise.all([
                        getIngestionJob(jobId),
                        getJobReviews(jobId),
                    ])

                if (!active) {
                    return
                }

                setJob(jobResponse)
                setReviews(reviewResponse.items)
            } catch (loadError) {
                if (!active) {
                    return
                }

                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Unable to load job details.",
                )
            } finally {
                if (active) {
                    setLoading(false)
                }
            }
        }

        void load()

        return () => {
            active = false
        }
    }, [jobId])

    return (
        <section className="job-detail">
            <div className="job-detail__header">
                <div>
                    <span className="job-detail__eyebrow">
                        JOB DETAIL
                    </span>

                    <h2>
                        Ingestion Job #{jobId}
                    </h2>

                    <p>
                        Real persisted pipeline, detection,
                        evidence and review data.
                    </p>
                </div>

                <button
                    type="button"
                    className="job-detail__close"
                    onClick={onClose}
                >
                    Close
                </button>
            </div>

            {loading ? (
                <div className="job-detail__empty">
                    Loading real job details...
                </div>
            ) : error ? (
                <div className="job-detail__error">
                    {error}
                </div>
            ) : job ? (
                <>
                    <div className="job-detail__metrics">
                        <div>
                            <span>Status</span>
                            <strong>{job.status}</strong>
                        </div>

                        <div>
                            <span>Frames</span>
                            <strong>
                                {job.processed_frame_count}/
                                {job.frame_count}
                            </strong>
                        </div>

                        <div>
                            <span>Detections</span>
                            <strong>
                                {job.detection_count}
                            </strong>
                        </div>

                        <div>
                            <span>Preprocessing</span>
                            <strong>
                                {formatMs(
                                    job.preprocessing_ms,
                                )}
                            </strong>
                        </div>

                        <div>
                            <span>Inference</span>
                            <strong>
                                {formatMs(
                                    job.inference_ms,
                                )}
                            </strong>
                        </div>

                        <div>
                            <span>Evidence</span>
                            <strong>
                                {formatMs(
                                    job.evidence_ms,
                                )}
                            </strong>
                        </div>
                    </div>

                    <div className="job-detail__metadata">
                        <div>
                            <span>Source</span>
                            <strong>{job.source_id}</strong>
                        </div>

                        <div>
                            <span>Sequence</span>
                            <strong>
                                {job.sequence_id ?? "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Pipeline</span>
                            <strong>
                                {job.pipeline_version}
                            </strong>
                        </div>

                        <div>
                            <span>Model</span>
                            <strong>
                                {job.model_name}
                            </strong>
                        </div>

                        <div>
                            <span>Model version</span>
                            <strong>
                                {job.model_version}
                            </strong>
                        </div>

                        <div>
                            <span>Completed</span>
                            <strong>
                                {formatDate(
                                    job.completed_at,
                                )}
                            </strong>
                        </div>
                    </div>

                    <div className="job-detail__detections">
                        <div className="job-detail__section-heading">
                            <div>
                                <span className="job-detail__eyebrow">
                                    DETECTIONS
                                </span>

                                <h3>
                                    Stored detections
                                </h3>
                            </div>

                            <span>
                                {reviews.length} record
                                {reviews.length === 1
                                    ? ""
                                    : "s"}
                            </span>
                        </div>

                        {reviews.length === 0 ? (
                            <div className="job-detail__empty">
                                No detections were persisted
                                for this job.
                            </div>
                        ) : (
                            <div className="detection-list">
                                {reviews.map((review) => (
                                    <DetectionCard
                                        key={review.id}
                                        review={review}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    <OperationalMap reviews={reviews} />
                </>
            ) : null}
        </section>
    )
}
