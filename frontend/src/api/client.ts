import type {
    DetectionReview,
    DetectionReviewListResponse,
    DetectionReviewUpdate,
    IngestionJobListResponse,
    IngestionJobStatus,
} from "../types/api"

const REQUEST_TIMEOUT_MS = 8000

async function requestJson<T>(
    url: string,
    options: RequestInit = {},
): Promise<T> {
    const controller = new AbortController()

    const timeout = window.setTimeout(
        () => controller.abort(),
        REQUEST_TIMEOUT_MS,
    )

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                Accept: "application/json",
                ...(options.headers ?? {}),
            },
            cache: "no-store",
            signal: controller.signal,
        })

        if (!response.ok) {
            let message = `Request failed: HTTP ${response.status}`

            try {
                const body = await response.json()

                if (
                    body &&
                    typeof body.detail === "string"
                ) {
                    message = body.detail
                }
            } catch {
                // Keep the HTTP status message.
            }

            throw new Error(message)
        }

        return (await response.json()) as T
    } catch (error) {
        if (
            error instanceof DOMException &&
            error.name === "AbortError"
        ) {
            throw new Error("Request timed out.", { cause: error })
        }

        throw error
    } finally {
        window.clearTimeout(timeout)
    }
}

export async function getIngestionJobs(
    page = 1,
    pageSize = 25,
): Promise<IngestionJobListResponse> {
    return requestJson<IngestionJobListResponse>(
        `/ingestion/jobs?page=${page}&page_size=${pageSize}`,
    )
}

export async function getIngestionJob(
    jobId: number,
): Promise<IngestionJobStatus> {
    return requestJson<IngestionJobStatus>(
        `/ingestion/jobs/${jobId}`,
    )
}

export async function getPendingReviews(
    page = 1,
    pageSize = 25,
): Promise<DetectionReviewListResponse> {
    return requestJson<DetectionReviewListResponse>(
        `/reviews?decision=pending&page=${page}&page_size=${pageSize}`,
    )
}

export async function getReview(
    reviewId: number,
): Promise<DetectionReview> {
    return requestJson<DetectionReview>(
        `/reviews/${reviewId}`,
    )
}

export async function updateReview(
    reviewId: number,
    payload: DetectionReviewUpdate,
): Promise<DetectionReview> {
    return requestJson<DetectionReview>(
        `/reviews/${reviewId}`,
        {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        },
    )
}

export function getReviewImageUrl(
    review: DetectionReview,
): string {
    return review.image_url
}

export async function getJobReviews(
    jobId: number,
    page = 1,
    pageSize = 25,
): Promise<DetectionReviewListResponse> {
    return requestJson<DetectionReviewListResponse>(
        `/reviews/job/${jobId}?page=${page}&page_size=${pageSize}`,
    )
}
import type { IngestionJobResponse } from "../types/api"

export interface CreateIngestionJobInput {
    sourceId: string
    sequenceId: string
    files: File[]
}

async function requestFormData<T>(
    url: string,
    formData: FormData,
): Promise<T> {
    const controller = new AbortController()

    const timeout = window.setTimeout(
        () => controller.abort(),
        REQUEST_TIMEOUT_MS,
    )

    try {
        const response = await fetch(url, {
            method: "POST",
            body: formData,
            cache: "no-store",
            signal: controller.signal,
        })

        if (!response.ok) {
            let message = `Request failed: HTTP ${response.status}`

            try {
                const body = await response.json()

                if (
                    body &&
                    typeof body.detail === "string"
                ) {
                    message = body.detail
                }
            } catch {
                // Keep the HTTP status message.
            }

            throw new Error(message)
        }

        return (await response.json()) as T
    } catch (error) {
        if (
            error instanceof DOMException &&
            error.name === "AbortError"
        ) {
            throw new Error("Request timed out.", { cause: error })
        }

        throw error
    } finally {
        window.clearTimeout(timeout)
    }
}

export async function createIngestionJob(
    input: CreateIngestionJobInput,
): Promise<IngestionJobResponse> {
    if (input.files.length === 0) {
        throw new Error("Select at least one sonar image.")
    }

    const manifest = {
        schema_version: "1",
        modality: "side_scan_sonar",
        source_id: input.sourceId.trim(),
        sequence_id: input.sequenceId.trim(),
        frames: input.files.map((file, index) => ({
            filename: file.name,
            frame_index: index,
        })),
    }

    const manifestBlob = new Blob(
        [JSON.stringify(manifest)],
        {
            type: "application/json",
        },
    )

    const formData = new FormData()

    formData.append(
        "manifest",
        manifestBlob,
        "manifest.json",
    )

    for (const file of input.files) {
        formData.append("files", file, file.name)
    }

    return requestFormData<IngestionJobResponse>(
        "/ingestion/jobs",
        formData,
    )
}
