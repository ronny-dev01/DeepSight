import {
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";
import type { ReactNode } from "react";
import { RefreshCw, Waves } from "lucide-react";
import { useNavigate } from "react-router-dom";

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

import { useWorkspaceSettings } from "../hooks/useWorkspaceSettings";
import UploadPanel from "./UploadPanel";
import SettingsPanel from "./SettingsPanel";
import JobDetail from "./JobDetail";

import "./Dashboard.css";

export type WorkspaceSection =
    | "overview"
    | "projects"
    | "sonar-analysis"
    | "processing-jobs"
    | "review-queue"
    | "reports"
    | "settings";

type ReviewDecision = "accepted" | "rejected";

const PAGE_SIZE = 25;

const SECTION_ITEMS: {
    id: WorkspaceSection;
    label: string;
}[] = [
    { id: "overview", label: "Overview" },
    { id: "projects", label: "Projects" },
    { id: "sonar-analysis", label: "Sonar analysis" },
    { id: "processing-jobs", label: "Processing jobs" },
    { id: "review-queue", label: "Review queue" },
    { id: "reports", label: "Reports" },
    { id: "settings", label: "Settings" },
];

function getErrorMessage(error: unknown): string {
    if (error instanceof Error) {
        return error.message;
    }

    return "An unexpected error occurred.";
}

function formatDate(value?: string | null): string {
    if (!value) return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

function formatConfidence(value?: number | null): string {
    if (value == null || !Number.isFinite(value)) {
        return "—";
    }

    return `${(value * 100).toFixed(1)}%`;
}

function formatMetric(value?: number | null): string {
    return value == null || !Number.isFinite(value)
        ? "—"
        : value.toLocaleString();
}

function getStatusClass(status?: string | null): string {
    const normalized = (status ?? "unknown").toLowerCase();

    if (
        normalized.includes("complete") ||
        normalized === "success" ||
        normalized === "succeeded"
    ) {
        return "status-badge status-badge--success";
    }

    if (
        normalized.includes("fail") ||
        normalized.includes("error") ||
        normalized === "cancelled"
    ) {
        return "status-badge status-badge--error";
    }

    if (
        normalized.includes("process") ||
        normalized === "running" ||
        normalized === "queued"
    ) {
        return "status-badge status-badge--active";
    }

    return "status-badge status-badge--neutral";
}

function getStatusLabel(status?: string | null): string {
    if (!status) return "Unknown";

    return status
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}

function SectionHeading({
    eyebrow,
    title,
    description,
    action,
}: {
    eyebrow?: string;
    title: string;
    description?: string;
    action?: ReactNode;
}) {
    return (
        <div className="dashboard-section-heading">
            <div>
                {eyebrow && (
                    <span className="dashboard-eyebrow">{eyebrow}</span>
                )}

                <h2>{title}</h2>

                {description && <p>{description}</p>}
            </div>

            {action && (
                <div className="dashboard-section-heading__action">
                    {action}
                </div>
            )}
        </div>
    );
}

function MetricCard({
    label,
    value,
    description,
    accent = "default",
}: {
    label: string;
    value: string | number;
    description: string;
    accent?: "default" | "blue" | "green" | "amber";
}) {
    return (
        <article className={`metric-card metric-card--${accent}`}>
            <span className="metric-card__label">{label}</span>

            <strong className="metric-card__value">{value}</strong>

            <span className="metric-card__description">
                {description}
            </span>
        </article>
    );
}

function StatusBadge({
    status,
}: {
    status?: string | null;
}) {
    return (
        <span className={getStatusClass(status)}>
            <span className="status-badge__dot" />
            {getStatusLabel(status)}
        </span>
    );
}

function EmptyState({
    title,
    description,
}: {
    title: string;
    description: string;
}) {
    return (
        <div className="dashboard-empty-state">
            <div className="dashboard-empty-state__icon">
                <Waves size={22} />
            </div>

            <h3>{title}</h3>

            <p>{description}</p>
        </div>
    );
}

function ReviewCard({
    review,
    compact,
    saving,
    onDecision,
}: {
    review: DetectionReview;
    compact: boolean;
    saving: boolean;
    onDecision: (
        reviewId: number,
        decision: ReviewDecision,
    ) => void;
}) {
    const imageUrl = getReviewImageUrl(review);

    return (
        <article
            className={`review-card ${
                compact ? "review-card--compact" : ""
            }`}
        >
            <div className="review-card__image">
                {imageUrl ? (
                    <img
                        src={imageUrl}
                        alt={`Sonar frame ${
                            review.frame_index ?? "unknown"
                        } containing detection ${review.detection_id}`}
                        loading="lazy"
                    />
                ) : (
                    <div className="review-card__image-placeholder">
                        <Waves size={24} />
                        <span>Frame preview unavailable</span>
                    </div>
                )}

                <span className="review-card__frame">
                    Frame {review.frame_index ?? "—"}
                </span>
            </div>

            <div className="review-card__body">
                <div className="review-card__topline">
                    <span className="review-card__detection-id">
                        Detection #{review.detection_id}
                    </span>

                    <span className="review-card__confidence">
                        {formatConfidence(review.confidence)}
                    </span>
                </div>

                <h3>{review.class_name || "Unclassified detection"}</h3>

                <p className="review-card__meta">
                    Source {review.source_id ?? "—"}
                    <span>·</span>
                    Sequence {review.sequence_id ?? "—"}
                </p>

                {!compact && (
                    <div className="review-card__evidence">
                        <div className="review-card__evidence-heading">
                            <span>Evidence</span>

                            <span>
                                {review.evidence_available
                                    ? "Available"
                                    : "Limited"}
                            </span>
                        </div>

                        {review.interpretation && (
                            <p>{review.interpretation}</p>
                        )}

                        {review.evidence_index != null && (
                            <div className="review-card__evidence-index">
                                Evidence index:{" "}
                                {review.evidence_index.toFixed(3)}
                            </div>
                        )}

                        <div className="review-card__signals">
                            {review.intensity_contrast != null && (
                                <span>
                                    Contrast{" "}
                                    {review.intensity_contrast.toFixed(2)}
                                </span>
                            )}

                            {review.edge_density != null && (
                                <span>
                                    Edge density{" "}
                                    {review.edge_density.toFixed(2)}
                                </span>
                            )}

                            {review.shape_compactness != null && (
                                <span>
                                    Shape{" "}
                                    {review.shape_compactness.toFixed(2)}
                                </span>
                            )}
                        </div>

                        <p className="review-card__disclaimer">
                            Acoustic evidence supports inspection; it is not
                            a confirmed material classification.
                        </p>
                    </div>
                )}

                <div className="review-card__footer">
                    <span className="review-card__date">
                        {formatDate(review.created_at)}
                    </span>

                    <div className="review-card__actions">
                        <button
                            type="button"
                            className="button button--secondary button--small"
                            disabled={saving}
                            onClick={() =>
                                onDecision(review.id, "rejected")
                            }
                        >
                            Reject
                        </button>

                        <button
                            type="button"
                            className="button button--primary button--small"
                            disabled={saving}
                            onClick={() =>
                                onDecision(review.id, "accepted")
                            }
                        >
                            {saving ? "Saving…" : "Accept"}
                        </button>
                    </div>
        </div>
    </div>
</article>
    );
}

export default function Dashboard({
    activeSection,
}: {
    activeSection: WorkspaceSection;
}) {
    const navigate = useNavigate();

    const activeSectionLabel =
        SECTION_ITEMS.find((item) => item.id === activeSection)?.label ??
        "Overview";

    const {
        settings,
        updateSettings,
        resetSettings,
    } = useWorkspaceSettings();

    const [jobs, setJobs] = useState<IngestionJobSummary[]>([]);
    const [totalJobs, setTotalJobs] = useState(0);

    const [reviews, setReviews] = useState<DetectionReview[]>([]);
    const [totalReviews, setTotalReviews] = useState(0);

    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [reviewLoading, setReviewLoading] = useState(true);

    const [error, setError] = useState<string | null>(null);
    const [reviewError, setReviewError] = useState<string | null>(null);

    const [busyReviewId, setBusyReviewId] = useState<number | null>(null);
    const [selectedJobId, setSelectedJobId] = useState<number | null>(null);

    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const refreshWorkspace = useCallback(
        async (showInitialLoading = false) => {
            if (showInitialLoading) {
                setLoading(true);
                setReviewLoading(true);
            } else {
                setRefreshing(true);
            }

            setError(null);
            setReviewError(null);

            try {
                const [jobsResult, reviewsResult] =
                    await Promise.allSettled([
                        getIngestionJobs(1, PAGE_SIZE),
                        getPendingReviews(1, PAGE_SIZE),
                    ]);

                if (jobsResult.status === "fulfilled") {
                    setJobs(jobsResult.value.items);
                    setTotalJobs(jobsResult.value.total);
                } else {
                    setError(getErrorMessage(jobsResult.reason));
                }

                if (reviewsResult.status === "fulfilled") {
                    setReviews(reviewsResult.value.items);
                    setTotalReviews(reviewsResult.value.total);
                } else {
                    setReviewError(getErrorMessage(reviewsResult.reason));
                }

                setLastUpdated(new Date());
            } catch (refreshError) {
                setError(getErrorMessage(refreshError));
            } finally {
                setLoading(false);
                setRefreshing(false);
                setReviewLoading(false);
            }
        },
        [],
    );

    useEffect(() => {
        const timer = window.setTimeout(() => {
            void refreshWorkspace(true);
        }, 0);

        return () => window.clearTimeout(timer);
    }, [refreshWorkspace]);

    useEffect(() => {
        if (!settings.autoRefresh) return;

        const interval = Math.max(
            5,
            Number(settings.refreshInterval) || 30,
        );

        const timer = window.setInterval(() => {
            void refreshWorkspace(false);
        }, interval * 1000);

        return () => window.clearInterval(timer);
    }, [
        settings.autoRefresh,
        settings.refreshInterval,
        refreshWorkspace,
    ]);

    const completedJobs = useMemo(
        () =>
            jobs.filter((job) =>
                [
                    "completed",
                    "complete",
                    "success",
                    "succeeded",
                ].includes((job.status ?? "").toLowerCase()),
            ).length,
        [jobs],
    );

    const projectGroups = useMemo(() => {
        const groups = new Map<string, IngestionJobSummary[]>();

        for (const job of jobs) {
            const key = job.source_id
                ? String(job.source_id)
                : "unassigned";

            const existing = groups.get(key) ?? [];
            existing.push(job);
            groups.set(key, existing);
        }

        return Array.from(groups.entries()).map(
            ([sourceId, sourceJobs]) => ({
                sourceId,
                jobs: sourceJobs,
                latest: sourceJobs[0],
            }),
        );
    }, [jobs]);

    const openAnalysis = useCallback((jobId: number) => {
        setSelectedJobId(jobId);
    }, []);

    const handleReviewDecision = useCallback(
        async (reviewId: number, decision: ReviewDecision) => {
            setBusyReviewId(reviewId);
            setReviewError(null);

            try {
                await updateReview(reviewId, { decision });

                setReviews((current) =>
                    current.filter((review) => review.id !== reviewId),
                );

                setTotalReviews((current) =>
                    Math.max(0, current - 1),
                );
            } catch (decisionError) {
                setReviewError(getErrorMessage(decisionError));
            } finally {
                setBusyReviewId(null);
            }
        },
        [],
    );

    const renderJobTable = (
        tableJobs: IngestionJobSummary[],
    ) => (
        <div className="dashboard-table-wrapper">
            <table className="dashboard-table">
                <thead>
                    <tr>
                        <th>Job</th>
                        <th>Status</th>
                        <th>Source</th>
                        <th>Frames</th>
                        <th>Detections</th>
                        <th>Model</th>
                        <th>Created</th>
                        <th aria-label="Actions" />
                    </tr>
                </thead>

                <tbody>
                    {tableJobs.map((job) => (
                        <tr
                            key={job.id}
                            className="dashboard-table__clickable"
                            onClick={() => openAnalysis(job.id)}
                        >
                            <td>
                                <span className="dashboard-table__job-id">
                                    #{job.id}
                                </span>
                            </td>

                            <td>
                                <StatusBadge status={job.status} />
                            </td>

                            <td>{job.source_id ?? "—"}</td>

                            <td>
                                {formatMetric(
                                    job.processed_frame_count ??
                                    job.frame_count,
                                )}
                            </td>

                            <td>{formatMetric(job.detection_count)}</td>

                            <td>
                                {job.model_name ||
                                    job.model_version ||
                                    "—"}
                            </td>

                            <td>{formatDate(job.created_at)}</td>

                            <td>
                                <button
                                    type="button"
                                    className="table-action"
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        openAnalysis(job.id);
                                    }}
                                >
                                    Open
                                    <span aria-hidden="true">↗</span>
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    const renderOverview = () => (
        <>
            <SectionHeading
                eyebrow={activeSectionLabel}
                title="Sonar operations at a glance"
                description="Monitor ingestion, inspect detections, and review acoustic evidence."
                action={
                    <div className="dashboard-overview-actions">
                        {lastUpdated && (
                            <span className="dashboard-last-updated">
                                Updated{" "}
                                {lastUpdated.toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })}
                            </span>
                        )}

                        <button
                            type="button"
                            className="button button--secondary"
                            onClick={() => void refreshWorkspace(false)}
                            disabled={refreshing}
                        >
                            <RefreshCw
                                size={15}
                                className={refreshing ? "spin" : ""}
                            />
                            {refreshing ? "Refreshing…" : "Refresh"}
                        </button>
                    </div>
                }
            />

            <div className="dashboard-metrics">
                <MetricCard
                    label="Total jobs"
                    value={formatMetric(totalJobs)}
                    description="Ingestion jobs recorded"
                />

                <MetricCard
                    label="Jobs loaded"
                    value={formatMetric(jobs.length)}
                    description={`Showing up to ${PAGE_SIZE} recent jobs`}
                />

                <MetricCard
                    label="Pending reviews"
                    value={formatMetric(totalReviews)}
                    description="Detections awaiting human review"
                    accent="amber"
                />

                <MetricCard
                    label="Completed in view"
            value={formatMetric(completedJobs)}
            description="Completed jobs in loaded results"
            accent="green"
        />
    </div>

    {/* Start ingestion comes first and occupies the full width. */}
    <section className="dashboard-panel dashboard-panel--wide">
        <SectionHeading
            title="Start an ingestion"
            description="Upload side-scan sonar imagery and initiate processing."
        />

        <UploadPanel
            onCreated={(job) => {
                void refreshWorkspace(false);
                setSelectedJobId(job.id);
            }}
        />
    </section>

    {/* Recent jobs stay at the bottom of the Overview. */}
    <section className="dashboard-panel dashboard-panel--wide">
        <SectionHeading
            title="Recent processing jobs"
            description="Latest ingestion activity"
            action={
                <button
                    type="button"
                    className="text-button"
                    onClick={() => navigate("/jobs")}
                >
                    View all →
                </button>
            }
        />

        {jobs.length > 0 ? (
            renderJobTable(jobs.slice(0, 5))
        ) : (
            <EmptyState
                title="No jobs yet"
                description="Upload sonar imagery to create your first ingestion job."
            />
        )}
    </section>
    </>
);

    const renderProjects = () => (
        <>
            <SectionHeading
                eyebrow="Sources"
                title="Projects"
                description="Browse ingestion jobs grouped by source."
            />

            {projectGroups.length === 0 ? (
                <EmptyState
                    title="No source projects found"
                    description="Projects appear here when ingestion jobs are available."
                />
            ) : (
                <div className="project-grid">
                    {projectGroups.map((group) => (
                        <article
                            className="project-card"
                            key={group.sourceId}
                        >
                            <div className="project-card__top">
                                <div className="project-card__icon">
                                    <Waves size={20} />
                                </div>

                                <StatusBadge
                                    status={group.latest?.status}
                                />
                            </div>

                            <span className="dashboard-eyebrow">
                                Source
                            </span>

                            <h3>
                                {group.sourceId === "unassigned"
                                    ? "Unassigned source"
                                    : `Source ${group.sourceId}`}
                            </h3>

                            <p>
                                {group.jobs.length} loaded{" "}
                                {group.jobs.length === 1
                                    ? "job"
                                    : "jobs"}
                            </p>

                            <div className="project-card__footer">
                                <span>
                                    Latest: #{group.latest?.id ?? "—"}
                                </span>

                                {group.latest && (
                                    <button
                                        type="button"
                                        className="text-button"
                                        onClick={() =>
                                            openAnalysis(group.latest!.id)
                                        }
                                    >
                                        Open analysis →
                                    </button>
                                )}
                            </div>
                        </article>
                    ))}
                </div>
            )}
        </>
    );

    const renderSonarAnalysis = () => (
        <>
            <SectionHeading
                eyebrow="Inspection workspace"
                title="Sonar analysis"
                description="Select an ingestion job to inspect frames, detections, and evidence."
            />

            {jobs.length > 0 ? (
                <div className="analysis-job-grid">
                    {jobs.map((job) => (
                        <button
                            type="button"
                            className="analysis-job-card"
                            key={job.id}
                            onClick={() => openAnalysis(job.id)}
                        >
                            <div className="analysis-job-card__top">
                                <span className="analysis-job-card__id">
                                    Job #{job.id}
                                </span>

                                <StatusBadge status={job.status} />
                            </div>

                            <h3>
                                {job.model_name || "Sonar inference"}
                            </h3>

                            <p>
                                Source {job.source_id ?? "—"} ·{" "}
                                {formatMetric(
                                    job.processed_frame_count ??
                                    job.frame_count,
                                )}{" "}
                                frames
                            </p>

                            <div className="analysis-job-card__footer">
                                <span>
                                    {formatMetric(job.detection_count)} detections
                                </span>

                                <span>Open workspace →</span>
                            </div>
                        </button>
                    ))}
                </div>
            ) : (
                <EmptyState
                    title="No analysis jobs available"
            description="Create an ingestion job before opening the sonar analysis workspace."
        />
        )}
        </>
    );

    const renderProcessingJobs = () => (
        <>
            <SectionHeading
                eyebrow="Ingestion"
                title="Processing jobs"
                description="Review job status, frame counts, detections, and model information."
            />

            {jobs.length > 0 ? (
                renderJobTable(jobs)
            ) : (
                <EmptyState
                    title="No processing jobs"
                    description="Your ingestion jobs will appear here."
                />
            )}
        </>
    );

    const renderReviewQueue = () => (
        <>
            <SectionHeading
                eyebrow="Human in the loop"
                title="Review queue"
                description="Inspect model detections and record human decisions."
            />

            {reviewError && (
                <div className="dashboard-alert dashboard-alert--error">
                    <div>
                        <strong>Review queue error</strong>
                        <p>{reviewError}</p>
                    </div>

                    <button
                        type="button"
                        className="text-button"
                        onClick={() => void refreshWorkspace(false)}
                    >
                        Retry
                    </button>
                </div>
            )}

            {reviewLoading ? (
                <div className="dashboard-loading">
                    <span className="dashboard-spinner" />
                    Loading review queue…
                </div>
            ) : reviews.length > 0 ? (
                <div className="review-grid">
                    {reviews.map((review) => (
                        <ReviewCard
                            key={review.id}
                            review={review}
                            compact={settings.compactReviewCards}
                            saving={busyReviewId === review.id}
                            onDecision={handleReviewDecision}
                        />
                    ))}
                </div>
            ) : (
                <EmptyState
            title="Review queue is clear"
            description="No pending detections were returned by the review queue."
        />
        )}
        </>
    );

    const renderReports = () => (
        <>
            <SectionHeading
                eyebrow="Reporting"
                title="Job reports"
                description="Open a job to inspect its report and available export actions."
            />

            {jobs.length > 0 ? (
                <div className="report-list">
                    {jobs.map((job) => (
                        <div className="report-row" key={job.id}>
                            <div className="report-row__identity">
                                <span className="report-row__icon">
                                    <Waves size={18} />
                                </span>

                                <div>
                                    <strong>Job #{job.id}</strong>

                                    <span>
                                        {formatDate(job.created_at)} · Source{" "}
                                        {job.source_id ?? "—"}
                                    </span>
                                </div>
                            </div>

                            <StatusBadge status={job.status} />

                            <button
                                type="button"
                                className="button button--secondary button--small"
                                onClick={() => openAnalysis(job.id)}
                            >
                                Open report
                            </button>
                        </div>
                    ))}
                </div>
            ) : (
                <EmptyState
            title="No reports available"
            description="Reports are associated with ingestion jobs."
        />
        )}
        </>
    );

    const renderSettings = () => (
        <>
            <SectionHeading
                eyebrow="Preferences"
                title="Workspace settings"
                description="Configure refresh behavior, detection display, and review defaults."
            />

            <section className="dashboard-panel dashboard-settings-panel">
                <SettingsPanel
                    settings={settings}
                    updateSettings={updateSettings}
                    resetSettings={resetSettings}
                />
            </section>
        </>
    );

    const renderSection = () => {
        switch (activeSection) {
            case "projects":
                return renderProjects();

            case "sonar-analysis":
                return renderSonarAnalysis();

            case "processing-jobs":
                return renderProcessingJobs();

            case "review-queue":
                return renderReviewQueue();

            case "reports":
                return renderReports();

            case "settings":
                return renderSettings();

            case "overview":
            default:
                return renderOverview();
        }
    };

    if (selectedJobId !== null) {
        return (
            <JobDetail
                jobId={selectedJobId}
                onClose={() => setSelectedJobId(null)}
            />
        );
    }

    return (
        <div className="dashboard">
            {error && (
                <div className="dashboard-alert dashboard-alert--error">
                    <div>
                        <strong>Unable to load ingestion jobs</strong>
                        <p>{error}</p>
                    </div>

                    <button
                        type="button"
                        className="text-button"
                        onClick={() => void refreshWorkspace(false)}
                    >
                        Retry
                    </button>
                </div>
            )}

            {loading ? (
                <div className="dashboard-loading dashboard-loading--page">
                    <span className="dashboard-spinner" />
                    Loading workspace…
                </div>
            ) : (
                <div className="dashboard-page-content">
                    {renderSection()}
                </div>
            )}
        </div>
    );
}