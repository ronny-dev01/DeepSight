from datetime import datetime, timezone

from sqlalchemy import delete

from services.api.db import SessionLocal
from services.api.models import IngestionJob
from services.worker.worker import (
    acquire_worker_lock,
    get_next_queued_job_id,
    recover_orphaned_jobs,
    release_worker_lock,
)


TEST_SOURCE_ID = "worker-contract-test"


def cleanup_test_jobs() -> None:
    db = SessionLocal()

    try:
        db.execute(
            delete(IngestionJob).where(
                IngestionJob.source_id == TEST_SOURCE_ID
            )
        )
        db.commit()
    finally:
        db.close()


def run() -> None:
    cleanup_test_jobs()

    db = SessionLocal()

    try:
        job = IngestionJob(
            source_id=TEST_SOURCE_ID,
            source_checksum="worker-contract-test",
            pipeline_version="worker-test",
            model_name="worker-test",
            model_version="worker-test",
            modality="side_scan_sonar",
            status="running",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            error_message="orphaned worker test",
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id
    finally:
        db.close()

    worker_connection = acquire_worker_lock()

    try:
        try:
            acquire_worker_lock()
        except RuntimeError as exc:
            assert "already running" in str(exc)
        else:
            raise AssertionError(
                "A second worker unexpectedly acquired the advisory lock"
            )

        print("Worker advisory lock exclusivity: PASS")

        recovered_count = recover_orphaned_jobs()
        assert recovered_count == 1

        db = SessionLocal()

        try:
            recovered_job = db.get(IngestionJob, job_id)

            assert recovered_job is not None
            assert recovered_job.status == "queued"
            assert recovered_job.started_at is None
            assert recovered_job.completed_at is None
            assert recovered_job.error_message is None
        finally:
            db.close()

        print("Orphaned running-job recovery: PASS")

        claimed_id = get_next_queued_job_id()

        assert claimed_id == job_id

        db = SessionLocal()

        try:
            claimed_job = db.get(IngestionJob, job_id)

            assert claimed_job is not None
            assert claimed_job.status == "running"
            assert claimed_job.started_at is not None
        finally:
            db.close()

        print("Atomic queued-to-running claim: PASS")
        print("Atomic started_at claim timestamp: PASS")
        print("Worker contract test: PASS")

    finally:
        release_worker_lock(worker_connection)
        cleanup_test_jobs()


if __name__ == "__main__":
    run()
