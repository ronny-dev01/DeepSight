
import { useCallback, useEffect, useState } from "react";
import {
  Waves,
  RefreshCw,
} from "lucide-react";

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

export type WorkspaceSection =
  | "overview"
  | "projects"
  | "sonar-analysis"
  | "processing-jobs"
  | "review-queue"
  | "reports"
  | "settings";

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

function getErrorMessage(error: unknown, fallback: string): string {
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
              {review.evidence_available ? "Available" : "Unavailable"}
            </strong>
          </div>
          <div>
            <span>Evidence index</span>
            <strong>{formatMetric(review.evidence_index)}</strong>
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

        <section className="review-evidence" aria-label="Detection evidence">
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
              <strong>{formatMetric(review.evidence_index)}</strong>
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
              <strong>{review.shadow_candidate_direction ?? "N/A"}</strong>
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
              <strong>{formatMetric(review.intensity_contrast)}</strong>
            </div>
            <div>
              <span>Edge density</span>
              <strong>{formatMetric(review.edge_density)}</strong>
            </div>
            <div>
              <span>Shape compactness</span>
              <strong>{formatMetric(review.shape_compactness)}</strong>
            </div>
            <div>
              <span>Shadow support</span>
              <strong>{formatMetric(review.shadow_candidate_score)}</strong>
            </div>
          </div>

          <p className="review-evidence__note">
            The heuristic evidence index is an engineering signal for review
            support, not a probability of object identity.
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
            onClick={() => onDecision(review.id, "accepted")}
          >
            {busy ? "Saving..." : "Accept detection"}
          </button>

          <button
            type="button"
            className="review-button review-button--reject"
            disabled={busy}
            onClick={() => onDecision(review.id, "rejected")}
          >
            {busy ? "Saving..." : "Reject detection"}
          </button>
        </div>
      </div>
    </article>
  );
}

const pageTitles: Record<
  WorkspaceSection,
  { eyebrow: string; title: string; description: string }
> = {
  overview: {
    eyebrow: "WORKSPACE / OVERVIEW",
    title: "Mission Overview",
    description:
      "A live operational view of your sonar ingestion and review workload.",
  },
  projects: {
    eyebrow: "WORKSPACE / PROJECTS",
    title: "Projects",
    description:
      "Explore survey sources represented by your recorded ingestion jobs.",
  },
  "sonar-analysis": {
    eyebrow: "WORKSPACE / SONAR ANALYSIS",
    title: "Sonar Analysis",
    description:
      "Inspect available frames, detections, evidence and job metadata.",
  },
  "processing-jobs": {
    eyebrow: "WORKSPACE / PROCESSING",
    title: "Processing Jobs",
    description:
      "Monitor persisted jobs from the marine sonar processing pipeline.",
  },
  "review-queue": {
    eyebrow: "WORKSPACE / HUMAN REVIEW",
    title: "Review Queue",
    description:
      "Inspect model findings and record human review decisions.",
  },
  reports: {
    eyebrow: "WORKSPACE / REPORTS",
    title: "Reports",
    description:
      "Open a processed job to inspect its available report and export options.",
  },
  settings: {
    eyebrow: "WORKSPACE / SETTINGS",
    title: "Settings",
    description:
      "Workspace information and current application capabilities.",
  },
};

export default function Dashboard({
  activeSection,
}: {
  activeSection: WorkspaceSection;
}) {
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
        getErrorMessage(decisionError, "Unable to update review."),
      );
    } finally {
      setBusyReviewId(null);
    }
  };

  const openAnalysis = (jobId: number) => {
    setSelectedJobId(jobId);
  };

  const latestJob = jobs[0] ?? null;

  const projectMap = new Map<string, IngestionJobSummary[]>();
  for (const job of jobs) {
    const source = job.source_id || "Unassigned source";
    const existing = projectMap.get(source) ?? [];
    existing.push(job);
    projectMap.set(source, existing);
  }
  const projects = Array.from(projectMap.entries());

  const page = pageTitles[activeSection];

  if (activeSection === "sonar-analysis" && selectedJobId !== null) {
    return (
      <div className="dashboard dashboard--analysis">
        <JobDetail
          jobId={selectedJobId}
          onClose={() => setSelectedJobId(null)}
        />
      </div>
    );
  }

  return (
    <div className={`dashboard dashboard--${activeSection}`}>
      <header className="workspace-page-heading">
        <div>
          <span className="panel-eyebrow">{page.eyebrow}</span>
          <h1>{page.title}</h1>
          <p>{page.description}</p>
        </div>

        <div className="workspace-page-heading__actions">
          <span className="workspace-live-status">
            <span className="workspace-live-status__dot" />
            API workspace
          </span>
          <button
            type="button"
            className="refresh-button"
            onClick={() => void loadDashboard()}
          >
            <RefreshCw size={15} aria-hidden="true" />
            Refresh
          </button>
        </div>
      </header>

      {error && (
        <div className="dashboard-error" role="alert">
          <strong>Ingestion jobs unavailable</strong>
          <span>{error}</span>
        </div>
      )}

      {activeSection === "overview" && (
        <>
          <section
            className="dashboard-summary"
            aria-label="Workspace summary"
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
              <span className="summary-card__label">Review pending</span>
              <strong>{reviewLoading ? "..." : pendingReviews.length}</strong>
              <span className="summary-card__footnote">
                Loaded review records
              </span>
            </article>

            <article className="summary-card summary-card--green">
              <span className="summary-card__label">Latest status</span>
              <strong className="summary-status">
                {latestJob?.status ?? (loading ? "..." : "N/A")}
              </strong>
              <span className="summary-card__footnote">
                {latestJob ? `Job #${latestJob.id}` : "No job available"}
              </span>
            </article>
          </section>

          <section className="dashboard-panel">
            <div className="panel-heading">
              <div className="panel-heading__copy">
                <span className="panel-eyebrow">DATA INGESTION</span>
                <h2>Upload sonar data</h2>
                <p>
                  Submit survey imagery through the existing ingestion
                  workflow.
                </p>
              </div>
            </div>
            <UploadPanel onCreated={() => void loadDashboard()} />
          </section>

          <section className="dashboard-panel">
            <div className="panel-heading">
              <div className="panel-heading__copy">
                <span className="panel-eyebrow">RECENT ACTIVITY</span>
                <h2>Recent processing jobs</h2>
                <p>
                  Select a job to open its sonar analysis workspace.
                </p>
              </div>
            </div>

            {loading ? (
              <div className="workspace-empty">Loading recorded jobs…</div>
            ) : jobs.length === 0 ? (
              <div className="workspace-empty">
                No jobs are recorded yet. Upload sonar imagery to begin.
              </div>
            ) : (
              <div className="workspace-job-list">
                {jobs.slice(0, 5).map((job) => (
                  <button
                    type="button"
                    className="workspace-job-item"
                    key={job.id}
                    onClick={() => openAnalysis(job.id)}
                  >
                    <span className="workspace-job-item__identity">
                      <strong>Job #{job.id}</strong>
                      <small>
                        {job.source_id} · {job.model_name}
                      </small>
                    </span>
                    <span
                      className={`status-pill ${statusClass(job.status)}`}
                    >
                      <span className="status-pill__dot" />
                      {job.status}
                    </span>
                    <span
                      className="workspace-job-item__arrow"
                      aria-hidden="true"
                    >
                      →
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {activeSection === "projects" && (
        <section className="dashboard-panel">
          <div className="panel-heading">
            <div className="panel-heading__copy">
              <span className="panel-eyebrow">SURVEY SOURCES</span>
              <h2>Available projects</h2>
              <p>
                Project groups are derived from source IDs in the currently
                loaded job records.
              </p>
            </div>
            <span className="review-count">{projects.length} sources</span>
          </div>

          {loading ? (
            <div className="workspace-empty">Loading project sources…</div>
          ) : projects.length === 0 ? (
            <div className="workspace-empty">
              No project sources are available yet. Create an ingestion job
              by uploading sonar data.
            </div>
          ) : (
            <div className="workspace-project-grid">
              {projects.map(([source, sourceJobs]) => {
                const latestSourceJob = sourceJobs[0];

                return (
                  <article
                    className="workspace-project-card"
                    key={source}
                  >
                    <div className="workspace-project-card__top">
                      <span className="workspace-project-card__icon">
                        <Waves size={19} aria-hidden="true" />
                      </span>
                      <span className="workspace-project-card__count">
                        {sourceJobs.length}{" "}
                        {sourceJobs.length === 1 ? "job" : "jobs"}
                      </span>
                    </div>

                    <h3>{source}</h3>
                    <p>
                      Survey source represented in recorded ingestion jobs.
                    </p>

                    <div className="workspace-project-card__meta">
                      <span>Latest job</span>
                      <strong>#{latestSourceJob?.id ?? "N/A"}</strong>
                    </div>

                    {latestSourceJob && (
                      <button
                        type="button"
                        className="workspace-text-button"
                        onClick={() => openAnalysis(latestSourceJob.id)}
                      >
                        Open latest analysis <span aria-hidden="true">→</span>
                      </button>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </section>
      )}

      {activeSection === "sonar-analysis" && (
        <section className="dashboard-panel">
          <div className="panel-heading">
            <div className="panel-heading__copy">
              <span className="panel-eyebrow">ANALYSIS WORKSPACE</span>
              <h2>Select a processing job</h2>
              <p>
                Choose a recorded job to open the frame viewer and detection
                inspector.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="workspace-empty">Loading available jobs…</div>
          ) : jobs.length === 0 ? (
            <div className="workspace-empty">
              No processing jobs are available for analysis.
            </div>
          ) : (
            <div className="workspace-job-list">
              {jobs.map((job) => (
                <button
                  type="button"
                  className="workspace-job-item"
                  key={job.id}
                  onClick={() => openAnalysis(job.id)}
                >
                  <span className="workspace-job-item__identity">
                    <strong>
                      Job #{job.id}{" "}
                      <span className="workspace-job-item__source">
                        {job.source_id}
                      </span>
                    </strong>
                    <small>
                      {job.frame_count} frames · {job.detection_count}{" "}
                      detections · {job.model_name}
                    </small>
                  </span>
                  <span
                    className={`status-pill ${statusClass(job.status)}`}
                  >
                    <span className="status-pill__dot" />
                    {job.status}
                  </span>
                  <span className="workspace-job-item__arrow">
                    Open →
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      {activeSection === "processing-jobs" && (
        <section className="dashboard-panel">
          <div className="panel-heading">
            <div className="panel-heading__copy">
              <span className="panel-eyebrow">PIPELINE MONITOR</span>
              <h2>Processing jobs</h2>
              <p>
                Choose a row to inspect its processing details and sonar
                output.
              </p>
            </div>
            <span className="review-count">{totalJobs} total jobs</span>
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
                      Loading ingestion jobs…
                    </td>
                  </tr>
                ) : jobs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="table-empty">
                      No ingestion jobs recorded.
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => (
                    <tr
                      key={job.id}
                      className="job-row-clickable"
                      tabIndex={0}
                      aria-label={`Open ingestion job ${job.id}`}
                      onClick={() => openAnalysis(job.id)}
                      onKeyDown={(event) => {
                        if (
                          event.key === "Enter" ||
                          event.key === " "
                        ) {
                          event.preventDefault();
                          openAnalysis(job.id);
                        }
                      }}
                    >
                      <td className="job-id-cell">#{job.id}</td>
                      <td>
                        <span
                          className={`status-pill ${statusClass(job.status)}`}
                        >
                          <span className="status-pill__dot" />
                          {job.status}
                        </span>
                      </td>
                      <td className="job-source-cell">{job.source_id}</td>
                      <td className="numeric-cell">{job.frame_count}</td>
                      <td className="numeric-cell">
                        {job.detection_count}
                      </td>
                      <td className="job-model-cell">{job.model_name}</td>
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
              The current API request loads up to 25 jobs.
            </span>
          </div>
        </section>
      )}

      {activeSection === "review-queue" && (
        <section className="dashboard-panel">
          <div className="panel-heading">
            <div className="panel-heading__copy">
              <span className="panel-eyebrow">HUMAN-IN-THE-LOOP</span>
              <h2>Pending detections</h2>
              <p>
                Review the available evidence and record a decision for each
                item.
              </p>
            </div>
            <span className="review-count">
              <span className="review-count__dot" />
              {reviewLoading
                ? "Loading…"
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
              <span>Retrieving available review records…</span>
            </div>
          ) : pendingReviews.length === 0 ? (
            <div className="review-empty">
              <span className="review-empty__mark">✓</span>
              <strong>No pending detections</strong>
              <span>
                {reviewError
                  ? "The review request failed. Use Refresh to try again."
                  : "There are currently no loaded detections requiring review."}
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
      )}

      {activeSection === "reports" && (
        <section className="dashboard-panel">
          <div className="panel-heading">
            <div className="panel-heading__copy">
              <span className="panel-eyebrow">JOB REPORTS</span>
              <h2>Available reports</h2>
              <p>
                Open a job to view its report using the existing report
                endpoint and supported export controls.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="workspace-empty">Loading report sources…</div>
          ) : jobs.length === 0 ? (
            <div className="workspace-empty">
              No job reports are available yet.
            </div>
          ) : (
            <div className="workspace-job-list">
              {jobs.map((job) => (
                <button
                  type="button"
                  className="workspace-job-item"
                  key={job.id}
                  onClick={() => openAnalysis(job.id)}
                >
                  <span className="workspace-job-item__identity">
                    <strong>Job #{job.id} report</strong>
                    <small>
                      {job.source_id} · {formatDate(job.created_at)}
                    </small>
                  </span>
                  <span
                    className={`status-pill ${statusClass(job.status)}`}
                  >
                    <span className="status-pill__dot" />
                    {job.status}
                  </span>
                  <span className="workspace-job-item__arrow">
                    View →
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      {activeSection === "settings" && (
        <section className="dashboard-panel workspace-settings">
          <div className="panel-heading">
            <div className="panel-heading__copy">
              <span className="panel-eyebrow">WORKSPACE DETAILS</span>
              <h2>Application information</h2>
              <p>Current capabilities exposed by this frontend.</p>
            </div>
          </div>

          <div className="workspace-settings__rows">
            <div>
              <span>Workspace</span>
              <strong>DeepSight · Marine Intelligence</strong>
            </div>
            <div>
              <span>Data source</span>
              <strong>Connected application API</strong>
            </div>
            <div>
              <span>Job refresh interval</span>
              <strong>5 seconds</strong>
            </div>
            <div>
              <span>Loaded job page size</span>
              <strong>Up to 25 records</strong>
            </div>
            <div>
              <span>Review workflow</span>
              <strong>Human accept / reject</strong>
            </div>
          </div>

          <p className="workspace-settings__note">
            These are informational details. Editable preferences are not
            shown here because no settings persistence endpoint has been
            established in the current frontend code.
          </p>
        </section>
      )}
    </div>
  );
}