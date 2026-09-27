import { useCallback, useEffect, useState } from "react"

import {
    getIngestionJobs,
    getPendingReviews,
    getReviewImageUrl,
    updateReview,
} from "../api/client"

import type {
    DetectionReview,
    IngestionJobSummary,
} from "../types/api"

import "./Dashboard.css"
import JobDetail from "./JobDetail"
import UploadPanel from "./UploadPanel"

const REFRESH_MS = 5000

function formatDate(value: string | null): string {
    if (!value) {
        return "N/A"
    }

    const date = new Date(value)

    if (Number.isNaN(date.getTime())) {
        return "N/A"
    }

    return date.toLocaleString()
}

function statusClass(status: string): string {
    const normalized = status.toLowerCase()

    if (
        normalized === "succeeded" ||
        normalized === "running" ||
        normalized === "queued" ||
        normalized === "failed"
    ) {
        return `status-${normalized}`
    }

    return "status-unknown"
}

function formatConfidence(value: number): string {
    return `${(value * 100).toFixed(1)}%`
}

function ReviewCard({
    review,
    busy,
    onDecision,
}: {
    review: DetectionReview
    busy: boolean
    onDecision: (
        reviewId: number,
        decision: "accepted" | "rejected",
    ) => void
}) {
    return (
        <article className="review-card">
            <div className="review-card__image">
                <img
                    src={getReviewImageUrl(review)}
                    alt={`Sonar frame ${review.frame_index}`}
                />
            </div>

            <div className="review-card__content">
                <div className="review-card__header">
                    <div>
                        <span className="review-label">
                            Detection #{review.detection_id}
                        </span>

                        <h3>{review.class_name}</h3>
                    </div>

                    <span className="review-confidence">
                        {formatConfidence(review.confidence)}
                    </span>
                </div>

                <div className="review-grid">
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

                    <div>
                        <span>Interpretation</span>
                        <strong>
                            {review.interpretation ?? "N/A"}
                        </strong>
                    </div>

                    <div>
                        <span>Frame</span>
                        <strong>
                            #{review.frame_index}
                        </strong>
                    </div>
                </div>

                <section className="review-evidence" aria-label="Detection evidence">
                    <div className="review-evidence__header">
                        <div>
                            <span className="review-evidence__eyebrow">
                                EXPLAINABLE EVIDENCE
                            </span>

                            <h4>Evidence analysis</h4>
                        </div>

                        <span className="review-evidence__availability">
                            {review.evidence_available
                                ? "Evidence available"
                                : "Evidence unavailable"}
                        </span>
                    </div>

                    <div className="review-evidence__summary">
                        <div>
                            <span>Heuristic evidence index</span>
                            <strong>
                                {review.evidence_index !== null
                                    ? review.evidence_index.toFixed(3)
                                    : "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Interpretation</span>
                            <strong>
                                {review.interpretation
                                    ? review.interpretation.replaceAll("_", " ")
                                    : "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Shadow direction</span>
                            <strong>
                                {review.shadow_candidate_direction ?? "N/A"}
                            </strong>
                        </div>

                        <div>
                            <span>Physical direction</span>
                            <strong>
                                {review.physical_shadow_direction_available
                                    ? "Available"
                                    : "Unavailable"}
                            </strong>
                        </div>
                    </div>

                    <div className="review-evidence__signals">
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
                            <span>Shadow support</span>
                            <strong>
                                {review.shadow_candidate_score !== null
                                    ? review.shadow_candidate_score.toFixed(3)
                                    : "N/A"}
                            </strong>
                        </div>
                    </div>

                    <p className="review-evidence__note">
                        The heuristic evidence index is an engineering signal for review support,
                        not a probability of object identity.
                    </p>
                </section>

                <div className="review-source">
                    <span>
                        Source: {review.source_id}
                    </span>

                    <span>
                        Model: {review.model_name}
                    </span>
                </div>

                <div className="review-actions">
                    <button
                        type="button"
                        className="review-button review-button--accept"
                        disabled={busy}
                        onClick={() =>
                            onDecision(review.id, "accepted")
                        }
                    >
                        {busy ? "Saving..." : "Accept"}
                    </button>

                    <button
                        type="button"
                        className="review-button review-button--reject"
                        disabled={busy}
                        onClick={() =>
                            onDecision(review.id, "rejected")
                        }
                    >
                        {busy ? "Saving..." : "Reject"}
                    </button>
                </div>
            </div>
        </article>
    )
}

export default function Dashboard() {
    const [jobs, setJobs] = useState<IngestionJobSummary[]>([])
    const [totalJobs, setTotalJobs] = useState(0)
    const [pendingReviews, setPendingReviews] = useState<
        DetectionReview[]
    >([])

    const [loading, setLoading] = useState(true)
    const [reviewLoading, setReviewLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [reviewError, setReviewError] =
        useState<string | null>(null)

    const [busyReviewId, setBusyReviewId] =
        useState<number | null>(null)

    const [selectedJobId, setSelectedJobId] =
        useState<number | null>(null)

    const loadDashboard = useCallback(async () => {
        try {
            setError(null)

            const [jobResponse, reviewResponse] =
                await Promise.all([
                    getIngestionJobs(1, 25),
                    getPendingReviews(1, 25),
                ])

            setJobs(jobResponse.items)
            setTotalJobs(jobResponse.total)
            setPendingReviews(reviewResponse.items)

            setLoading(false)
            setReviewLoading(false)
        } catch (loadError) {
            const message =
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load dashboard data."

            setError(message)
            setReviewError(message)
            setLoading(false)
            setReviewLoading(false)
        }
    }, [])

    useEffect(() => {
        const initialLoad = window.setTimeout(() => {
            void loadDashboard()
        }, 0)

        const timer = window.setInterval(
            () => {
                void loadDashboard()
            },
            REFRESH_MS,
        )

        return () => {
            window.clearTimeout(initialLoad)
            window.clearInterval(timer)
        }
    }, [loadDashboard])

    const handleDecision = async (
        reviewId: number,
        decision: "accepted" | "rejected",
    ) => {
        setBusyReviewId(reviewId)
        setReviewError(null)

        try {
            await updateReview(reviewId, {
                decision,
            })

            setPendingReviews((current) =>
                current.filter(
                    (review) => review.id !== reviewId,
                ),
            )
        } catch (decisionError) {
            setReviewError(
                decisionError instanceof Error
                    ? decisionError.message
                    : "Unable to update review.",
            )
        } finally {
            setBusyReviewId(null)
        }
    }

    const latestJob = jobs[0] ?? null

    return (
        <main className="dashboard">
            <UploadPanel
                onCreated={() => void loadDashboard()}
            />

            <section className="dashboard-summary">
                <article className="summary-card">
                    <span>Total jobs</span>
                    <strong>
                        {loading ? "..." : totalJobs}
                    </strong>
                </article>

                <article className="summary-card">
                    <span>Jobs loaded</span>
                    <strong>
                        {loading ? "..." : jobs.length}
                    </strong>
                </article>

                <article className="summary-card">
                    <span>Pending review</span>
                    <strong>
                        {reviewLoading
                            ? "..."
                            : pendingReviews.length}
                    </strong>
                </article>

                <article className="summary-card">
                    <span>Latest status</span>
                    <strong className="summary-status">
                        {latestJob
                            ? latestJob.status
                            : "N/A"}
                    </strong>
                </article>
            </section>

            {error && (
                <div className="dashboard-error">
                    <strong>Dashboard data unavailable.</strong>
                    <span>{error}</span>
                </div>
            )}

            <section className="dashboard-panel">
                <div className="panel-heading">
                    <div>
                        <span className="panel-eyebrow">
                            MONITORING
                        </span>

                        <h2>Ingestion Jobs</h2>

                        <p>
                            Real persisted jobs from the marine
                            sonar processing pipeline.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="refresh-button"
                        onClick={() => void loadDashboard()}
                    >
                        Refresh
                    </button>
                </div>

                <div className="jobs-table-wrap">
                    <table className="jobs-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Status</th>
                                <th>Source</th>
                                <th>Frames</th>
                                <th>Detections</th>
                                <th>Model</th>
                                <th>Created</th>
                            </tr>
                        </thead>

                        <tbody>
                            {loading ? (
                                <tr>
                                    <td
                                        colSpan={7}
                                        className="table-empty"
                                    >
                                        Loading real jobs...
                                    </td>
                                </tr>
                            ) : jobs.length === 0 ? (
                                <tr>
                                    <td
                                        colSpan={7}
                                        className="table-empty"
                                    >
                                        No ingestion jobs recorded.
                                    </td>
                                </tr>
                            ) : (
                                jobs.map((job) => (
                                    <tr
                                        key={job.id}
                                        className="job-row-clickable"
                                        role="button"
                                        tabIndex={0}
                                        onClick={() =>
                                            setSelectedJobId(job.id)
                                        }
                                        onKeyDown={(event) => {
                                            if (
                                                event.key === "Enter" ||
                                                event.key === " "
                                            ) {
                                                event.preventDefault()
                                                setSelectedJobId(job.id)
                                            }
                                        }}
                                        title={`Open job #${job.id}`}
                                    >
                                        <td>
                                            #{job.id}
                                        </td>

                                        <td>
                                            <span
                                                className={`status-pill ${statusClass(
                                                    job.status,
                                                )}`}
                                            >
                                                {job.status}
                                            </span>
                                        </td>

                                        <td>
                                            {job.source_id}
                                        </td>

                                        <td>
                                            {job.frame_count}
                                        </td>

                                        <td>
                                            {job.detection_count}
                                        </td>

                                        <td>
                                            {job.model_name}
                                        </td>

                                        <td>
                                            {formatDate(
                                                job.created_at,
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </section>

            {selectedJobId !== null && (
                <JobDetail
                    jobId={selectedJobId}
                    onClose={() => setSelectedJobId(null)}
                />
            )}

            <section className="dashboard-panel">
                <div className="panel-heading">
                    <div>
                        <span className="panel-eyebrow">
                            HUMAN REVIEW
                        </span>

                        <h2>Pending Detections</h2>

                        <p>
                            Review real model detections and
                            record the final human decision.
                        </p>
                    </div>

                    <span className="review-count">
                        {reviewLoading
                            ? "Loading..."
                            : `${pendingReviews.length} pending`}
                    </span>
                </div>

                {reviewError && (
                    <div className="review-error">
                        {reviewError}
                    </div>
                )}

                {reviewLoading ? (
                    <div className="review-empty">
                        Loading pending reviews...
                    </div>
                ) : pendingReviews.length === 0 ? (
                    <div className="review-empty">
                        No pending detections require review.
                    </div>
                ) : (
                    <div className="review-list">
                        {pendingReviews.map((review) => (
                            <ReviewCard
                                key={review.id}
                                review={review}
                                busy={
                                    busyReviewId ===
                                    review.id
                                }
                                onDecision={
                                    handleDecision
                                }
                            />
                        ))}
                    </div>
                )}
            </section>
        </main>
    )
}
