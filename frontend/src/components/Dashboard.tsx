
import { useCallback, useEffect, useState } from "react";

import {
    getIngestionJobs,
    getPendingReviews,
    getReviewImageUrl,
    updateReview,
} from "../api/client";

import type {
    DetectionReview,
    IngestionJobSummary,
} from "../types/api";

import "./Dashboard.css";
import JobDetail from "./JobDetail";
import UploadPanel from "./UploadPanel";

const REFRESH_MS = 5000;

function formatDate(value: string | null): string {
    if (!value) return "N/A";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) return "N/A";

    return date.toLocaleString();
}

function statusClass(status: string): string {
    const normalized = status.toLowerCase();

    if (
        normalized === "succeeded" ||
        normalized === "running" ||
        normalized === "queued" ||
        normalized === "failed"
    ) {
        return `status-${normalized}`;
    }

    return "status-unknown";
}

function formatConfidence(value: number): string {
    return `${(value * 100).toFixed(1)}%`;
}

function formatMetric(value: number | null): string {
    return value !== null ? value.toFixed(3) : "N/A";
}

function getErrorMessage(
    error: unknown,
    fallback: string,
): string {
    return error instanceof Error ? error.message : fallback;
}

function ReviewCard({
    review,
    busy,
    onDecision,
}: {
    review: DetectionReview;
    busy: boolean;
    onDecision: (
        reviewId: number,
        decision: "accepted" | "rejected",
    ) => void;
}) {
    return (
        <article className="review-card">
            <div className="review-card__image">
                <img
                    src={getReviewImageUrl(review)}
                    alt={`Sonar frame ${review.frame_index}`}
                    loading="lazy"
                />
                <span className="review-card__image-label">
                    FRAME {review.frame_index}
                </span>
            </div>

            <div className="review-card__content">
                <div className="review-card__header">
                    <div className="review-card__identity">
                        <span className="review-label">
                            DETECTION #{review.detection_id}
                        </span>
                        <h3>{review.class_name}</h3>
                    </div>

                    <span
                        className="review-confidence"
                        aria-label={`Model confidence ${formatConfidence(review.confidence)}`}
                    >
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
                            {formatMetric(review.evidence_index)}
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
                        <span>Frame</span>
                        <strong>#{review.frame_index}</strong>
                    </div>
                </div>

                <section
                    className="review-evidence"
                    aria-label="Detection evidence"
                >
                    <div className="review-evidence__header">
                        <div>
                            <span className="review-evidence__eyebrow">
                                EXPLAINABLE EVIDENCE
                            </span>
                            <h4>Evidence analysis</h4>
                        </div>

                        <span
                            className={`review-evidence__availability ${
                                review.evidence_available
                                    ? "is-available"
                                    : "is-unavailable"
                            }`}
                        >
                            <span className="availability-dot" />
                            {review.evidence_available
                                ? "Evidence available"
                                : "Evidence unavailable"}
                        </span>
                    </div>

                    <div className="review-evidence__summary">
                        <div>
                            <span>Heuristic evidence index</span>
                            <strong>
                                {formatMetric(review.evidence_index)}
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
                                {formatMetric(review.intensity_contrast)}
                            </strong>
                        </div>

                        <div>
                            <span>Edge density</span>
                            <strong>
                                {formatMetric(review.edge_density)}
                            </strong>
                        </div>

                        <div>
                            <span>Shape compactness</span>
                            <strong>
                                {formatMetric(review.shape_compactness)}
                            </strong>
                        </div>

                        <div>
                            <span>Shadow support</span>
                            <strong>
                                {formatMetric(review.shadow_candidate_score)}
                            </strong>
                        </div>
                    </div>

                    <p className="review-evidence__note">
                        The heuristic evidence index is an engineering
                        signal for review support, not a probability of
                        object identity.
                    </p>
                </section>

                <div className="review-source">
                    <span>
                        <span className="review-source__label">SOURCE</span>
                        {review.source_id}
                    </span>
                    <span>
                        <span className="review-source__label">MODEL</span>
                        {review.model_name}
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
                        {busy ? "Saving..." : "Accept detection"}
                    </button>

                    <button
                        type="button"
                        className="review-button review-button--reject"
                        disabled={busy}
                        onClick={() =>
                            onDecision(review.id, "rejected")
                        }
                    >
                        {busy ? "Saving..." : "Reject detection"}
                    </button>
                </div>
            </div>
        </article>
    );
}

export default function Dashboard() {
    const [jobs, setJobs] = useState<IngestionJobSummary[]>([]);
    const [totalJobs, setTotalJobs] = useState(0);
    const [pendingReviews, setPendingReviews] = useState<DetectionReview[]>([]);

    const [loading, setLoading] = useState(true);
    const [reviewLoading, setReviewLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [reviewError, setReviewError] = useState<string | null>(null);

    const [busyReviewId, setBusyReviewId] = useState<number | null>(null);
    const [selectedJobId, setSelectedJobId] = useState<number | null>(null);

    const loadDashboard = useCallback(async () => {
        const [jobResult, reviewResult] = await Promise.allSettled([
            getIngestionJobs(1, 25),
            getPendingReviews(1, 25),
        ]);

        if (jobResult.status === "fulfilled") {
            setJobs(jobResult.value.items);
            setTotalJobs(jobResult.value.total);
            setError(null);
        } else {
            setError(
                getErrorMessage(
                    jobResult.reason,
                    "Unable to load ingestion jobs.",
                ),
            );
        }

        if (reviewResult.status === "fulfilled") {
            setPendingReviews(reviewResult.value.items);
            setReviewError(null);
        } else {
            setReviewError(
                getErrorMessage(
                    reviewResult.reason,
                    "Unable to load pending reviews.",
                ),
            );
        }

        setLoading(false);
        setReviewLoading(false);
    }, []);

    useEffect(() => {
        const initialLoad = window.setTimeout(() => {
            void loadDashboard();
        }, 0);

        const timer = window.setInterval(() => {
            void loadDashboard();
        }, REFRESH_MS);

        return () => {
            window.clearTimeout(initialLoad);
            window.clearInterval(timer);
        };
    }, [loadDashboard]);

    const handleDecision = async (
        reviewId: number,
        decision: "accepted" | "rejected",
    ) => {
        setBusyReviewId(reviewId);
        setReviewError(null);

        try {
            await updateReview(reviewId, { decision });

            setPendingReviews((current) =>
                current.filter((review) => review.id !== reviewId),
            );
        } catch (decisionError) {
            setReviewError(
                getErrorMessage(
                    decisionError,
                    "Unable to update review.",
                ),
            );
        } finally {
            setBusyReviewId(null);
        }
    };

    const latestJob = jobs[0] ?? null;

    return (
        <div className="dashboard">
            <section id="ingestion" className="dashboard-anchor">
                <UploadPanel onCreated={() => void loadDashboard()} />
            </section>

            <section
                id="overview"
                className="dashboard-summary dashboard-anchor"
                aria-label="Mission overview"
            >
                <article className="summary-card summary-card--cyan">
                    <span className="summary-card__label">Total jobs</span>
                    <strong>{loading ? "..." : totalJobs}</strong>
                    <span className="summary-card__footnote">
                        Recorded ingestion jobs
                    </span>
                </article>

                <article className="summary-card summary-card--blue">
                    <span className="summary-card__label">Jobs loaded</span>
                    <strong>{loading ? "..." : jobs.length}</strong>
                    <span className="summary-card__footnote">
                        Latest page · up to 25
                    </span>
                </article>

                <article className="summary-card summary-card--amber">
                    <span className="summary-card__label">Pending review</span>
                    <strong>
                        {reviewLoading ? "..." : pendingReviews.length}
                    </strong>
                    <span className="summary-card__footnote">
                        Loaded review records
                    </span>
                </article>

                <article className="summary-card summary-card--green">
                    <span className="summary-card__label">Latest status</span>
                    <strong className="summary-status">
                        {latestJob ? latestJob.status : "N/A"}
                    </strong>
                    <span className="summary-card__footnote">
                        {latestJob
                            ? `Job #${latestJob.id}`
                            : "No job available"}
                    </span>
                </article>
            </section>

            {error && (
                <div className="dashboard-error" role="alert">
                    <strong>Ingestion jobs unavailable</strong>
                    <span>{error}</span>
                </div>
            )}

            <section
                id="jobs"
                className="dashboard-panel dashboard-anchor"
            >
                <div className="panel-heading">
                    <div className="panel-heading__copy">
                        <span className="panel-eyebrow">
                            MONITORING / 01
                        </span>
                        <h2>Ingestion Jobs</h2>
                        <p>
                            Persisted jobs from the marine sonar processing
                            pipeline.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="refresh-button"
                        onClick={() => void loadDashboard()}
                    >
                        <span className="refresh-button__symbol">↻</span>
                        Refresh data
                    </button>
                </div>

                <div className="jobs-table-wrap">
                    <table className="jobs-table">
                        <thead>
                            <tr>
                                <th scope="col">ID</th>
                                <th scope="col">Status</th>
                                <th scope="col">Source</th>
                                <th scope="col">Frames</th>
                                <th scope="col">Detections</th>
                                <th scope="col">Model</th>
                                <th scope="col">Created</th>
                            </tr>
                        </thead>

                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={7} className="table-empty">
                                        <span className="table-empty__title">
                                            Loading ingestion jobs
                                        </span>
                                        <span className="table-empty__detail">
                                            Retrieving persisted job records...
                                        </span>
                                    </td>
                                </tr>
                            ) : error && jobs.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="table-empty">
                                        <span className="table-empty__title">
                                            Job records unavailable
                                        </span>
                                        <span className="table-empty__detail">
                                            The request failed. Refresh data
                                            to try again.
                                        </span>
                                    </td>
                                </tr>
                            ) : jobs.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="table-empty">
                                        <span className="table-empty__title">
                                            No ingestion jobs recorded
                                        </span>
                                        <span className="table-empty__detail">
                                            Upload sonar imagery to create
                                            the first ingestion job.
                                        </span>
                                    </td>
                                </tr>
                            ) : (
                                jobs.map((job) => (
                                    <tr
                                        key={job.id}
                                        className={`job-row-clickable ${
                                            selectedJobId === job.id
                                                ? "is-selected"
                                                : ""
                                        }`}
                                        tabIndex={0}
                                        aria-label={`Open ingestion job ${job.id}`}
                                        aria-pressed={selectedJobId === job.id}
                                        onClick={() =>
                                            setSelectedJobId(job.id)
                                        }
                                        onKeyDown={(event) => {
                                            if (
                                                event.key === "Enter" ||
                                                event.key === " "
                                            ) {
                                                event.preventDefault();
                                                setSelectedJobId(job.id);
                                            }
                                        }}
                                        title={`Open job #${job.id}`}
                                    >
                                        <td className="job-id-cell">
                                            <span>#{job.id}</span>
                                        </td>
                                        <td>
                                            <span
                                                className={`status-pill ${statusClass(
                                                    job.status,
                                                )}`}
                                            >
                                                <span className="status-pill__dot" />
                                                {job.status}
                                            </span>
                                        </td>
                                        <td className="job-source-cell">
                                            {job.source_id}
                                        </td>
                                        <td className="numeric-cell">
                                            {job.frame_count}
                                        </td>
                                        <td className="numeric-cell">
                                            {job.detection_count}
                                        </td>
                                        <td className="job-model-cell">
                                            {job.model_name}
                                        </td>
                                        <td className="job-date-cell">
                                            {formatDate(job.created_at)}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="panel-footer">
                    <span>
                        Showing {jobs.length} of {totalJobs} recorded jobs
                    </span>
                    <span className="panel-footer__hint">
                        Select a row to inspect job details
                    </span>
                </div>
            </section>

            {selectedJobId !== null && (
                <JobDetail
                    jobId={selectedJobId}
                    onClose={() => setSelectedJobId(null)}
                />
            )}

            <section
                id="review"
                className="dashboard-panel dashboard-anchor"
            >
                <div className="panel-heading">
                    <div className="panel-heading__copy">
                        <span className="panel-eyebrow">
                            HUMAN REVIEW / 02
                        </span>
                        <h2>Pending Detections</h2>
                        <p>
                            Inspect model detections and record a human
                            review decision.
                        </p>
                    </div>

                    <span className="review-count">
                        <span className="review-count__dot" />
                        {reviewLoading
                            ? "Loading..."
                            : reviewError && pendingReviews.length === 0
                              ? "Unavailable"
                              : `${pendingReviews.length} pending`}
                    </span>
                </div>

                {reviewError && (
                    <div className="review-error" role="alert">
                        <strong>Review queue unavailable</strong>
                        <span>{reviewError}</span>
                    </div>
                )}

                {reviewLoading ? (
                    <div className="review-empty" aria-live="polite">
                        <span className="review-empty__mark review-empty__mark--loading">
                            ◌
                        </span>
                        <strong>Loading pending reviews</strong>
                        <span>
                            Retrieving available review records...
                        </span>
                    </div>
                ) : reviewError && pendingReviews.length === 0 ? (
                    <div className="review-empty review-empty--error">
                        <span className="review-empty__mark">!</span>
                        <strong>Review queue could not be loaded</strong>
                        <span>
                            The latest request failed. Refresh data to
                            try again.
                        </span>
                    </div>
                ) : pendingReviews.length === 0 ? (
                    <div className="review-empty">
                        <span className="review-empty__mark">✓</span>
                        <strong>No pending detections</strong>
                        <span>
                            There are currently no loaded detections
                            requiring review.
                        </span>
                    </div>
                ) : (
                    <div className="review-list">
                        {pendingReviews.map((review) => (
                            <ReviewCard
                                key={review.id}
                                review={review}
                                busy={busyReviewId === review.id}
                                onDecision={handleDecision}
                            />
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}