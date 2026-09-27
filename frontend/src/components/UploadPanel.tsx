import { useMemo, useState } from "react"

import {
    createIngestionJob,
} from "../api/client"

import type {
    IngestionJobResponse,
} from "../types/api"

import "./UploadPanel.css"

const MAX_UPLOAD_BYTES = 524288000
const MAX_FILES_PER_JOB = 200
const MAX_IMAGE_WIDTH = 12000
const MAX_IMAGE_HEIGHT = 12000

const ALLOWED_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
]

function formatBytes(bytes: number): string {
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getExtension(name: string): string {
    const dot = name.lastIndexOf(".")

    return dot === -1
        ? ""
        : name.slice(dot).toLowerCase()
}

function validateFiles(
    files: File[],
): string | null {
    if (files.length === 0) {
        return "Select at least one sonar image."
    }

    if (files.length > MAX_FILES_PER_JOB) {
        return `A job can contain at most ${MAX_FILES_PER_JOB} files.`
    }

    const totalBytes = files.reduce(
        (total, file) => total + file.size,
        0,
    )

    if (totalBytes > MAX_UPLOAD_BYTES) {
        return `Selected files exceed the ${formatBytes(MAX_UPLOAD_BYTES)} job limit.`
    }

    const filenames = files.map((file) => file.name)
    const uniqueNames = new Set(filenames)

    if (uniqueNames.size !== filenames.length) {
        return "Filenames must be unique within a job."
    }

    for (const file of files) {
        const extension = getExtension(file.name)

        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            return `Unsupported image type: ${file.name}`
        }

        if (file.size === 0) {
            return `Empty image file: ${file.name}`
        }
    }

    return null
}

export default function UploadPanel({
    onCreated,
}: {
    onCreated: (job: IngestionJobResponse) => void
}) {
    const [sourceId, setSourceId] = useState("")
    const [sequenceId, setSequenceId] = useState("")
    const [files, setFiles] = useState<File[]>([])
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] =
        useState<IngestionJobResponse | null>(null)
    const [submitting, setSubmitting] = useState(false)

    const totalBytes = useMemo(
        () =>
            files.reduce(
                (total, file) => total + file.size,
                0,
            ),
        [files],
    )

    const handleFiles = (
        event: React.ChangeEvent<HTMLInputElement>,
    ) => {
        const selected = Array.from(
            event.target.files ?? [],
        )

        setError(null)
        setSuccess(null)

        const validationError =
            validateFiles(selected)

        if (validationError) {
            setFiles([])
            setError(validationError)
            return
        }

        setFiles(selected)
    }

    const handleSubmit = async () => {
        setError(null)
        setSuccess(null)

        const cleanSourceId = sourceId.trim()
        const cleanSequenceId = sequenceId.trim()

        if (!cleanSourceId) {
            setError("Source ID is required.")
            return
        }

        if (!cleanSequenceId) {
            setError("Sequence ID is required.")
            return
        }

        const validationError =
            validateFiles(files)

        if (validationError) {
            setError(validationError)
            return
        }

        setSubmitting(true)

        try {
            const job = await createIngestionJob({
                sourceId: cleanSourceId,
                sequenceId: cleanSequenceId,
                files,
            })

            setSuccess(job)
            setFiles([])
            setSourceId("")
            setSequenceId("")

            onCreated(job)
        } catch (submitError) {
            setError(
                submitError instanceof Error
                    ? submitError.message
                    : "Unable to create ingestion job.",
            )
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <section className="upload-panel">
            <div className="upload-panel__header">
                <div>
                    <span className="upload-panel__eyebrow">
                        DATA INGESTION
                    </span>

                    <h2>Upload Sonar Data</h2>

                    <p>
                        Submit real side-scan sonar frames
                        to the processing pipeline.
                    </p>
                </div>

                <span className="upload-panel__limit">
                    Max {MAX_FILES_PER_JOB} files ·{" "}
                    {formatBytes(MAX_UPLOAD_BYTES)}
                </span>
            </div>

            <div className="upload-panel__form">
                <label>
                    <span>Source ID</span>

                    <input
                        type="text"
                        value={sourceId}
                        maxLength={255}
                        placeholder="e.g. vessel-alpha"
                        disabled={submitting}
                        onChange={(event) =>
                            setSourceId(
                                event.target.value,
                            )
                        }
                    />
                </label>

                <label>
                    <span>Sequence ID</span>

                    <input
                        type="text"
                        value={sequenceId}
                        maxLength={255}
                        placeholder="e.g. survey-2026-09-26-01"
                        disabled={submitting}
                        onChange={(event) =>
                            setSequenceId(
                                event.target.value,
                            )
                        }
                    />
                </label>

                <label className="upload-panel__file-field">
                    <span>Sonar frames</span>

                    <input
                        type="file"
                        multiple
                        accept=".jpg,.jpeg,.png,.tif,.tiff,image/jpeg,image/png,image/tiff"
                        disabled={submitting}
                        onChange={handleFiles}
                    />

                    <small>
                        JPG, JPEG, PNG, TIF or TIFF
                    </small>
                </label>
            </div>

            {files.length > 0 && (
                <div className="upload-panel__selection">
                    <div>
                        <strong>
                            {files.length} file
                            {files.length === 1
                                ? ""
                                : "s"} selected
                        </strong>

                        <span>
                            {formatBytes(totalBytes)}
                        </span>
                    </div>

                    <div className="upload-panel__files">
                        {files.slice(0, 8).map((file) => (
                            <span key={file.name}>
                                {file.name}
                            </span>
                        ))}

                        {files.length > 8 && (
                            <span>
                                +{files.length - 8} more
                            </span>
                        )}
                    </div>
                </div>
            )}

            {error && (
                <div className="upload-panel__error">
                    {error}
                </div>
            )}

            {success && (
                <div className="upload-panel__success">
                    <strong>
                        Job #{success.id} created.
                    </strong>

                    <span>
                        Status: {success.status}
                    </span>
                </div>
            )}

            <div className="upload-panel__footer">
                <span>
                    Image dimensions are validated by the
                    backend up to {MAX_IMAGE_WIDTH} ×{" "}
                    {MAX_IMAGE_HEIGHT} px.
                </span>

                <button
                    type="button"
                    disabled={submitting}
                    onClick={() => void handleSubmit()}
                >
                    {submitting
                        ? "Uploading..."
                        : "Create Ingestion Job"}
                </button>
            </div>
        </section>
    )
}
