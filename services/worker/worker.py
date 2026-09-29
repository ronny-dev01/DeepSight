import logging
import time

from sqlalchemy import select, update

from services.api.db import SessionLocal
from services.api.models import IngestionJob
from services.worker.job_runner import process_ingestion_job


POLL_INTERVAL_SECONDS = 1.0

logger = logging.getLogger(__name__)


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
            .values(status="running")
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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    run_worker()
