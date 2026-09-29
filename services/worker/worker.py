import logging
import time

from sqlalchemy import func, select, update

from services.api.db import SessionLocal, engine
from services.api.models import IngestionJob
from services.worker.job_runner import process_ingestion_job


POLL_INTERVAL_SECONDS = 1.0
WORKER_LOCK_KEY = 26057057

logger = logging.getLogger(__name__)


def acquire_worker_lock():
    connection = engine.connect()

    try:
        acquired = connection.scalar(
            select(
                func.pg_try_advisory_lock(
                    WORKER_LOCK_KEY
                )
            )
        )

        if not acquired:
            connection.close()
            raise RuntimeError(
                "Another marine ingestion worker is already running"
            )

        connection.commit()
        return connection
    except Exception:
        connection.close()
        raise


def release_worker_lock(connection) -> None:
    try:
        connection.scalar(
            select(
                func.pg_advisory_unlock(
                    WORKER_LOCK_KEY
                )
            )
        )
        connection.commit()
    finally:
        connection.close()


def recover_orphaned_jobs() -> int:
    db = SessionLocal()

    try:
        recovered_ids = db.scalars(
            update(IngestionJob)
            .where(IngestionJob.status == "running")
            .values(
                status="queued",
                started_at=None,
                completed_at=None,
                error_message=None,
            )
            .returning(IngestionJob.id)
        ).all()

        db.commit()
        return len(recovered_ids)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_next_queued_job_id() -> int | None:
    db = SessionLocal()

    try:
        queued_job_id = (
            select(IngestionJob.id)
            .where(IngestionJob.status == "queued")
            .order_by(IngestionJob.id)
            .limit(1)
            .scalar_subquery()
        )

        result = db.execute(
            update(IngestionJob)
            .where(
                IngestionJob.id == queued_job_id,
                IngestionJob.status == "queued",
            )
            .values(
                status="running",
                started_at=func.now(),
            )
            .returning(IngestionJob.id)
        )

        job_id = result.scalar_one_or_none()

        if job_id is None:
            db.rollback()
            return None

        db.commit()
        return job_id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_worker() -> None:
    worker_connection = acquire_worker_lock()

    try:
        recovered_count = recover_orphaned_jobs()

        if recovered_count:
            logger.warning(
                "Recovered %s orphaned ingestion job(s)",
                recovered_count,
            )

        logger.info("Marine ingestion worker started")

        while True:
            job_id = get_next_queued_job_id()

            if job_id is None:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            logger.info("Processing ingestion job %s", job_id)

            try:
                process_ingestion_job(job_id, already_claimed=True)
            except Exception:
                logger.exception("Ingestion job %s failed", job_id)
    finally:
        release_worker_lock(worker_connection)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    run_worker()
