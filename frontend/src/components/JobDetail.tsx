
import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent } from "react";

import {
    getIngestionJob,
    getJobReport,
    getJobReviews,
    getReviewImageUrl,
} from "../api/client";

import type { DetectionReview, IngestionJobStatus } from "../types/api";
import "./JobDetail.css";
import OperationalMap from "./OperationalMap";

const REFRESH_MS = 5000;

function formatMs(value: number | null): string {
    return value === null ? "N/A" : `${value.toFixed(1)} ms`;
}

function formatDate(value: string | null): string {
    if (!value) return "N/A";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "N/A" : date.toLocaleString();
}

function confidence(value: number): string {
    return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value: number | null, digits = 3): string {
    return value === null || !Number.isFinite(value) ? "N/A" : value.toFixed(digits);
}

function DecisionBadge({ decision }: { decision: DetectionReview["decision"] }) {
    return (
        <span className={`jd-decision jd-decision--${decision}`}>
            <span className="jd-decision__dot" />
            {decision}
        </span>
    );
}

function DataField({
    label,
    value,
}: {
    label: string;
    value: string | number;
}) {
    return (
        <div className="jd-field">
            <span className="jd-field__label">{label}</span>
            <strong className="jd-field__value">{value}</strong>
        </div>
    );
}

export default function JobDetail({
    jobId,
    onClose,
}: {
    jobId: number;
    onClose: () => void;
}) {
    const [job, setJob] = useState<IngestionJobStatus | null>(null);
    const [reviews, setReviews] = useState<DetectionReview[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [reportLoading, setReportLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [reportError, setReportError] = useState<string | null>(null);
    const [imageError, setImageError] = useState(false);
    const [overlayVisible, setOverlayVisible] = useState(true);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [dragging, setDragging] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);

    const dragOrigin = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

    useEffect(() => {
        let active = true;

        async function load(showLoading = false) {
            try {
                if (showLoading) setLoading(true);

                const [jobResponse, reviewResponse] = await Promise.all([
                    getIngestionJob(jobId),
                    getJobReviews(jobId),
                ]);

                if (!active) return;

                setJob(jobResponse);
                setReviews(reviewResponse.items);
                setError(null);
                setSelectedId((current) =>
                    current !== null &&
                    reviewResponse.items.some((item) => item.id === current)
                        ? current
                        : reviewResponse.items[0]?.id ?? null,
                );
            } catch (loadError) {
                if (!active) return;
                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Unable to load job details.",
                );
            } finally {
                if (active) setLoading(false);
            }
        }

        void load(true);
        const timer = window.setInterval(() => void load(), REFRESH_MS);

        return () => {
            active = false;
            window.clearInterval(timer);
        };
    }, [jobId, refreshKey]);

    const selected = useMemo(
        () => reviews.find((review) => review.id === selectedId) ?? reviews[0] ?? null,
        [reviews, selectedId],
    );

    const selectedIndex = selected
        ? reviews.findIndex((review) => review.id === selected.id)
        : -1;

    useEffect(() => {
        setImageError(false);
        setZoom(1);
        setPan({ x: 0, y: 0 });
    }, [selected?.id]);

    const chooseDetection = (review: DetectionReview) => {
        setSelectedId(review.id);
        setZoom(1);
        setPan({ x: 0, y: 0 });
        setImageError(false);
    };

    const moveSelection = (direction: -1 | 1) => {
        if (reviews.length === 0 || selectedIndex < 0) return;
        const nextIndex = Math.min(
            reviews.length - 1,
            Math.max(0, selectedIndex + direction),
        );
        chooseDetection(reviews[nextIndex]);
    };

    const downloadReport = async () => {
        setReportLoading(true);
        setReportError(null);

        try {
            const report = await getJobReport(jobId);
            const blob = new Blob([JSON.stringify(report, null, 2)], {
                type: "application/json",
            });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `deepsight-job-${jobId}-report.json`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (reportLoadError) {
            setReportError(
                reportLoadError instanceof Error
                    ? reportLoadError.message
                    : "Unable to download job report.",
            );
        } finally {
            setReportLoading(false);
        }
    };

    const zoomBy = (amount: number) => {
        setZoom((current) => {
            const next = Math.min(4, Math.max(1, current + amount));
            if (next === 1) setPan({ x: 0, y: 0 });
            return next;
        });
    };

    const resetViewer = () => {
        setZoom(1);
        setPan({ x: 0, y: 0 });
    };

    const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
        if (zoom <= 1) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        dragOrigin.current = {
            x: event.clientX,
            y: event.clientY,
            panX: pan.x,
            panY: pan.y,
        };
        setDragging(true);
    };

    const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
        if (!dragging) return;
        setPan({
            x: dragOrigin.current.panX + event.clientX - dragOrigin.current.x,
            y: dragOrigin.current.panY + event.clientY - dragOrigin.current.y,
        });
    };

    const onPointerUp = () => setDragging(false);
    const imageUrl = selected ? getReviewImageUrl(selected) : "";

    return (
        <section className="job-detail" aria-label={`Sonar analysis workspace for job ${jobId}`}>
            <header className="jd-header">
                <div className="jd-header__identity">
                    <div className="jd-brand-mark" aria-hidden="true">
                        <span />
                        <span />
                        <span />
                    </div>
                    <div>
                        <div className="jd-eyebrow">DEEPSIGHT / ANALYSIS WORKSPACE</div>
                        <h2>Sonar inspection <span>· Job #{jobId}</span></h2>
                        <p>Inspect model detections, acoustic evidence and available frame metadata.</p>
                    </div>
                </div>

                <div className="jd-header__actions">
                    {job && (
                        <span className={`jd-status jd-status--${job.status}`}>
                            <span className="jd-status__dot" />
                            {job.status}
                        </span>
                    )}
                    <button
                        type="button"
                        className="jd-button jd-button--secondary"
                        disabled={loading || reportLoading}
                        onClick={() => void downloadReport()}
                    >
                        {reportLoading ? "Preparing…" : "Export JSON"}
                    </button>
                    <button type="button" className="jd-button jd-button--close" onClick={onClose}>
                        Close <span aria-hidden="true">×</span>
                    </button>
                </div>
            </header>

            {reportError && (
                <div className="jd-alert" role="alert">
                    <strong>Report unavailable</strong>
                    <span>{reportError}</span>
                </div>
            )}

            {loading ? (
                <div className="jd-state">
                    <span className="jd-loader" />
                    <strong>Loading analysis data</strong>
                    <p>Connecting to the DeepSight API…</p>
                </div>
            ) : error ? (
                <div className="jd-state jd-state--error" role="alert">
                    <div className="jd-state__icon">!</div>
                    <strong>Unable to load job details</strong>
                    <p>{error}</p>
                    <button
                        type="button"
                        className="jd-button jd-button--secondary"
                        onClick={() => {
                            setLoading(true);
                            setRefreshKey((key) => key + 1);
                        }}
                    >
                        Try again
                    </button>
                </div>
            ) : job ? (
                <>
                    <section className="jd-overview" aria-label="Processing summary">
                        <div className="jd-overview__top">
                            <div>
                                <span className="jd-eyebrow">JOB SUMMARY</span>
                                <h3>Processing overview</h3>
                            </div>
                            <span className="jd-live-indicator">
                                <span /> Live · refreshes every 5 sec
                            </span>
                        </div>

                        <div className="jd-metrics">
                            <div className="jd-metric jd-metric--primary">
                                <span className="jd-metric__label">Detections</span>
                                <strong>{job.detection_count.toLocaleString()}</strong>
                                <small>Reported by job</small>
                            </div>
                            <div className="jd-metric">
                                <span className="jd-metric__label">Frames processed</span>
                                <strong>
                                    {job.processed_frame_count.toLocaleString()}
                                    <small> / {job.frame_count.toLocaleString()}</small>
                                </strong>
                                <div
                                    className="jd-progress"
                                    aria-label={`${
                                        job.frame_count > 0
                                            ? Math.min(100, (job.processed_frame_count / job.frame_count) * 100).toFixed(0)
                                            : 0
                                    }% frames processed`}
                                >
                                    <span
                                        style={{
                                            width: `${
                                                job.frame_count > 0
                                                    ? Math.min(100, (job.processed_frame_count / job.frame_count) * 100)
                                                    : 0
                                            }%`,
                                        }}
                                    />
                                </div>
                            </div>
                            <div className="jd-metric">
                                <span className="jd-metric__label">Preprocessing</span>
                                <strong>{formatMs(job.preprocessing_ms)}</strong>
                                <small>Pipeline timing</small>
                            </div>
                            <div className="jd-metric">
                                <span className="jd-metric__label">Inference</span>
                                <strong>{formatMs(job.inference_ms)}</strong>
                                <small>Model timing</small>
                            </div>
                            <div className="jd-metric">
                                <span className="jd-metric__label">Evidence</span>
                                <strong>{formatMs(job.evidence_ms)}</strong>
                                <small>Evidence timing</small>
                            </div>
                        </div>

                        <div className="jd-provenance">
                            <DataField label="Source" value={job.source_id} />
                            <DataField label="Sequence" value={job.sequence_id ?? "N/A"} />
                            <DataField label="Pipeline" value={job.pipeline_version} />
                            <DataField label="Model" value={job.model_name} />
                            <DataField label="Version" value={job.model_version} />
                            <DataField label="Completed" value={formatDate(job.completed_at)} />
                        </div>
                    </section>

                    <div className="jd-workspace">
                        <main className="jd-analysis">
                            <div className="jd-analysis__heading">
                                <div className="jd-analysis__title">
                                    <span className="jd-eyebrow">SONAR FRAME / SPATIAL INSPECTION</span>
                                    <h3>{selected ? `Frame ${selected.frame_index}` : "Sonar image viewer"}</h3>
                                    <p>
                                        {selected
                                            ? `${selected.source_id} / ${selected.sequence_id}`
                                            : "Select a detection to inspect its available image."}
                                    </p>
                                </div>

                                <div className="jd-viewer-tools">
                                    <div className="jd-zoom-control" aria-label="Image zoom controls">
                                        <button type="button" onClick={() => zoomBy(-0.25)} disabled={zoom <= 1} aria-label="Zoom out">−</button>
                                        <span>{Math.round(zoom * 100)}%</span>
                                        <button type="button" onClick={() => zoomBy(0.25)} disabled={zoom >= 4} aria-label="Zoom in">+</button>
                                    </div>
                                    <button type="button" className="jd-tool-button" onClick={resetViewer}>Reset</button>
                                    <button
                                        type="button"
                                        className={`jd-tool-button${overlayVisible ? " is-active" : ""}`}
                                        onClick={() => setOverlayVisible((visible) => !visible)}
                                        aria-pressed={overlayVisible}
                                    >
                                        <span className="jd-overlay-icon" />
                                        Overlay
                                    </button>
                                </div>
                            </div>

                            <div
                                className={`jd-canvas${dragging ? " is-dragging" : ""}`}
                                onPointerDown={onPointerDown}
                                onPointerMove={onPointerMove}
                                onPointerUp={onPointerUp}
                                onPointerCancel={onPointerUp}
                            >
                                {selected && !imageError && imageUrl ? (
                                    <div
                                        className="jd-image-transform"
                                        style={{
                                            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                                        }}
                                    >
                                        <img
                                            className="jd-source-image"
                                            src={imageUrl}
                                            alt={`Available sonar image for detection ${selected.detection_id}, frame ${selected.frame_index}`}
                                            draggable={false}
                                            onError={() => setImageError(true)}
                                        />
                                        {overlayVisible &&
                                            selected.image_width > 0 &&
                                            selected.image_height > 0 && (
                                                <div
                                                    className="jd-bbox"
                                                    style={{
                                                        left: `${(selected.x1 / selected.image_width) * 100}%`,
                                                        top: `${(selected.y1 / selected.image_height) * 100}%`,
                                                        width: `${((selected.x2 - selected.x1) / selected.image_width) * 100}%`,
                                                        height: `${((selected.y2 - selected.y1) / selected.image_height) * 100}%`,
                                                    }}
                                                >
                                                    <span>
                                                        {selected.class_name} · {confidence(selected.confidence)}
                                                    </span>
                                                </div>
                                            )}
                                    </div>
                                ) : (
                                    <div className="jd-canvas-empty">
                                        <div className="jd-canvas-empty__mark">⌁</div>
                                        <strong>
                                            {imageError
                                                ? "Image could not be loaded"
                                                : selected
                                                  ? "Image unavailable"
                                                  : "No frame selected"}
                                        </strong>
                                        <p>
                                            {imageError
                                                ? "Check the image URL and backend image endpoint."
                                                : selected
                                                  ? "No usable image URL is available for this review record."
                                                  : "Choose a review-linked detection from the queue."}
                                        </p>
                                    </div>
                                )}
                                <div className="jd-canvas-label">
                                    <span className="jd-canvas-label__dot" />
                                    {selected ? `FRAME ${selected.frame_index}` : "NO FRAME"}
                                </div>
                                <div className="jd-canvas-scale">ZOOM {Math.round(zoom * 100)}%</div>
                            </div>

                            <div className="jd-analysis__footer">
                                <span>
                                    {selected
                                        ? `Detection ${selected.detection_id} · ${selected.image_width} × ${selected.image_height}px`
                                        : "Awaiting detection selection"}
                                </span>
                                <div className="jd-pagination">
                                    <button
                                        type="button"
                                        onClick={() => moveSelection(-1)}
                                        disabled={selectedIndex <= 0}
                                    >
                                        ‹ <span>Previous</span>
                                    </button>
                                    <strong>{selected ? `${selectedIndex + 1} / ${reviews.length}` : "0 / 0"}</strong>
                                    <button
                                        type="button"
                                        onClick={() => moveSelection(1)}
                                        disabled={selectedIndex < 0 || selectedIndex >= reviews.length - 1}
                                    >
                                        <span>Next</span> ›
                                    </button>
                                </div>
                            </div>
                        </main>

                        <aside className="jd-navigator">
                            <div className="jd-panel-heading">
                                <div>
                                    <span className="jd-eyebrow">REVIEW QUEUE</span>
                                    <h3>Detections</h3>
                                </div>
                                <span className="jd-count">
                                    {String(reviews.length).padStart(2, "0")}
                                </span>
                            </div>
                            <div className="jd-navigator__summary">
                                <span>Review-linked records</span>
                                <span>{reviews.length} items</span>
                            </div>

                            {reviews.length === 0 ? (
                                <div className="jd-empty">
                                    <div className="jd-empty__symbol">⌁</div>
                                    <strong>No review-linked detections</strong>
                                    <p>
                                        This job may have detections that do not
                                        have review records.
                                    </p>
                                </div>
                            ) : (
                                <div className="jd-detection-list">
                                    {reviews.map((review, index) => (
                                        <button
                                            type="button"
                                            key={review.id}
                                            className={`jd-detection${
                                                selected?.id === review.id ? " is-selected" : ""
                                            }`}
                                            onClick={() => chooseDetection(review)}
                                            aria-pressed={selected?.id === review.id}
                                        >
                                            <span className="jd-detection__index">
                                                {String(index + 1).padStart(2, "0")}
                                            </span>
                                            <span className="jd-detection__body">
                                                <strong>{review.class_name}</strong>
                                                <small>
                                                    Detection {review.detection_id} · Frame {review.frame_index}
                                                </small>
                                                <span className="jd-detection__score">
                                                    <span className="jd-score-track">
                                                        <span
                                                            style={{
                                                                width: `${Math.max(0, Math.min(100, review.confidence * 100))}%`,
                                                            }}
                                                        />
                                                    </span>
                                                    {confidence(review.confidence)}
                                                </span>
                                            </span>
                                            <span className="jd-detection__chevron" aria-hidden="true">›</span>
                                        </button>
                                    ))}
                                </div>
                            )}

                            <div className="jd-navigator__footer">
                                <span className="jd-status__dot" />
                                Records supplied by review API
                            </div>
                        </aside>

                        <aside className="jd-inspector">
                            <div className="jd-panel-heading">
                                <div>
                                    <span className="jd-eyebrow">DETECTION RECORD</span>
                                    <h3>Inspector</h3>
                                </div>
                                {selected && <DecisionBadge decision={selected.decision} />}
                            </div>

                            {selected ? (
                                <div className="jd-inspector__content">
                                    <section className="jd-object">
                                        <span className="jd-object__id">OBJECT / {selected.detection_id}</span>
                                        <h3>{selected.class_name}</h3>
                                        <span className="jd-object__class">Class ID {selected.class_id}</span>
                                    </section>

                                    <section className="jd-confidence">
                                        <div className="jd-confidence__heading">
                                            <span>MODEL SCORE</span>
                                            <strong>{confidence(selected.confidence)}</strong>
                                        </div>
                                        <div className="jd-confidence__track">
                                            <span style={{ width: `${Math.max(0, Math.min(100, selected.confidence * 100))}%` }} />
                                        </div>
                                        <p>Model output; not necessarily a calibrated probability.</p>
                                    </section>

                                    <section className="jd-inspector-section">
                                        <h4>Acoustic evidence</h4>
                                        <div className="jd-field-grid">
                                            <DataField label="Interpretation" value={selected.interpretation ?? "N/A"} />
                                            <DataField label="Evidence" value={selected.evidence_available === null ? "N/A" : selected.evidence_available ? "Available" : "Unavailable"} />
                                            <DataField label="Evidence index" value={formatNumber(selected.evidence_index)} />
                                            <DataField label="Intensity contrast" value={formatNumber(selected.intensity_contrast)} />
                                            <DataField label="Edge density" value={formatNumber(selected.edge_density)} />
                                            <DataField label="Shape compactness" value={formatNumber(selected.shape_compactness)} />
                                            <DataField label="Shadow score" value={formatNumber(selected.shadow_candidate_score)} />
                                            <DataField label="Shadow direction" value={selected.shadow_candidate_direction ?? "N/A"} />
                                        </div>
                                        {selected.physical_shadow_direction_available !== null && (
                                            <div className="jd-evidence-note">
                                                Physical shadow direction:{" "}
                                                <strong>
                                                    {selected.physical_shadow_direction_available
                                                        ? "Available"
                                                        : "Not available"}
                                                </strong>
                                            </div>
                                        )}
                                    </section>

                                    <section className="jd-inspector-section">
                                        <h4>Frame metadata</h4>
                                        <div className="jd-field-grid">
                                            <DataField label="Source" value={selected.source_id} />
                                            <DataField label="Sequence" value={selected.sequence_id} />
                                            <DataField label="Frame index" value={selected.frame_index} />
                                            <DataField label="Frame ID" value={selected.frame_id} />
                                            <DataField label="Image size" value={`${selected.image_width} × ${selected.image_height}`} />
                                            <DataField label="Timestamp" value={formatDate(selected.timestamp)} />
                                            <DataField label="Latitude" value={selected.latitude ?? "Unavailable"} />
                                            <DataField label="Longitude" value={selected.longitude ?? "Unavailable"} />
                                            <DataField label="Heading" value={selected.heading_deg === null ? "N/A" : `${selected.heading_deg}°`} />
                                            <DataField label="Metadata verified" value={selected.metadata_verified ? "Yes" : "No"} />
                                            <DataField label="Track ID" value={selected.track_id ?? "N/A"} />
                                        </div>
                                    </section>

                                    <section className="jd-inspector-section">
                                        <h4>Model provenance</h4>
                                        <div className="jd-provenance-card">
                                            <span className="jd-provenance-card__icon">M</span>
                                            <div>
                                                <strong>{selected.model_name}</strong>
                                                <small>Version {selected.model_version}</small>
                                            </div>
                                        </div>
                                    </section>

                                    <section className="jd-inspector-section">
                                        <h4>Review record</h4>
                                        <div className="jd-review-record">
                                            <div>
                                                <span>Decision</span>
                                                <DecisionBadge decision={selected.decision} />
                                            </div>
                                            <div>
                                                <span>Created</span>
                                                <strong>{formatDate(selected.created_at)}</strong>
                                            </div>
                                            <div>
                                                <span>Reviewed</span>
                                                <strong>{formatDate(selected.reviewed_at)}</strong>
                                            </div>
                                            <div className="jd-review-record__note">
                                                <span>Reviewer note</span>
                                                <p>{selected.note?.trim() || "No reviewer note recorded."}</p>
                                            </div>
                                        </div>
                                    </section>
                                </div>
                            ) : (
                                <div className="jd-empty">
                                    <div className="jd-empty__symbol">⌁</div>
                                    <strong>No object selected</strong>
                                    <p>Select a detection to inspect its available evidence and metadata.</p>
                                </div>
                            )}
                        </aside>
                    </div>

                    <div className="jd-map-section">
                        <div className="jd-map-section__heading">
                            <div>
                                <span className="jd-eyebrow">GEOSPATIAL CONTEXT</span>
                                <h3>Operational map</h3>
                            </div>
                            <span>Based on available review metadata</span>
                        </div>
                        <OperationalMap reviews={reviews} />
                    </div>
                </>
            ) : null}
        </section>
    );
}