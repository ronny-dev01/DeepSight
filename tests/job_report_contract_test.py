from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete

from services.api.db import SessionLocal
from services.api.main import app
from services.api.models import (
    AcousticEvidence,
    Detection,
    DetectionReview,
    IngestionJob,
    SonarFrame,
    Track,
)


TEST_SOURCE_ID = "report-contract-test"


def cleanup() -> None:
    db = SessionLocal()

    try:
        jobs = (
            db.query(IngestionJob)
            .filter(IngestionJob.source_id == TEST_SOURCE_ID)
            .all()
        )

        for job in jobs:
            frame_ids = [
                frame.id
                for frame in job.frames
            ]

            detection_ids = []

            if frame_ids:
                detection_ids = [
                    detection.id
                    for detection in db.query(Detection)
                    .filter(
                        Detection.frame_id.in_(frame_ids)
                    )
                    .all()
                ]

            if detection_ids:
                track_ids = [
                    detection.track_id
                    for detection in db.query(Detection)
                    .filter(
                        Detection.id.in_(detection_ids)
                    )
                    .all()
                    if detection.track_id is not None
                ]

                db.execute(
                    delete(AcousticEvidence).where(
                        AcousticEvidence.detection_id.in_(
                            detection_ids
                        )
                    )
                )

                db.execute(
                    delete(DetectionReview).where(
                        DetectionReview.detection_id.in_(
                            detection_ids
                        )
                    )
                )

                for track_id in set(track_ids):
                    db.execute(
                        delete(Track).where(
                            Track.id == track_id
                        )
                    )

            db.delete(job)

        db.commit()
    finally:
        db.close()


def run() -> None:
    cleanup()

    db = SessionLocal()

    try:
        job = IngestionJob(
            source_id=TEST_SOURCE_ID,
            source_checksum="report-contract-test",
            pipeline_version="report-test",
            model_name="report-test-model",
            model_version="report-test-version",
            modality="side_scan_sonar",
            status="succeeded",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            preprocessing_ms=1.0,
            inference_ms=2.0,
            evidence_ms=3.0,
            tracking_ms=4.0,
        )

        db.add(job)
        db.flush()

        frame = SonarFrame(
            job_id=job.id,
            source_id=TEST_SOURCE_ID,
            modality="side_scan_sonar",
            sequence_id="report-contract-sequence",
            frame_index=0,
            image_path="storage/uploads/report-contract-test/frame.jpg",
            image_sha256="a" * 64,
            width=640,
            height=480,
            quality_index=0.9,
            quality_status="usable",
            quality_usable=True,
            timestamp=datetime.now(timezone.utc),
            latitude=21.123,
            longitude=88.456,
            heading_deg=45.0,
            metadata_verified=True,
        )

        db.add(frame)
        db.flush()

        track = Track(
            sequence_id="report-contract-sequence",
            class_name="Crab-Pot",
            first_frame=0,
            last_frame=0,
            detection_count=1,
            mean_confidence=0.8,
            max_confidence=0.8,
            persistence_score=1.0,
        )

        db.add(track)
        db.flush()

        detection = Detection(
            frame_id=frame.id,
            class_name="Crab-Pot",
            class_id=0,
            confidence=0.8,
            x1=10.0,
            y1=20.0,
            x2=100.0,
            y2=120.0,
            inference_ms=2.0,
            model_name="report-test-model",
            model_version="report-test-version",
            track_id=track.id,
        )

        db.add(detection)
        db.flush()

        evidence = AcousticEvidence(
            detection_id=detection.id,
            evidence_available=True,
            evidence_index=0.75,
            interpretation="supported",
            intensity_contrast=0.5,
            edge_density=0.4,
            shape_compactness=0.8,
            shadow_candidate_score=0.7,
            shadow_candidate_direction="right",
            physical_shadow_direction_available=True,
        )

        db.add(evidence)

        review = DetectionReview(
            detection_id=detection.id,
            decision="pending",
        )

        db.add(review)
        db.commit()

        job_id = job.id
        review_id = review.id
    finally:
        db.close()

    client = TestClient(app)
    response = client.get(
        f"/reports/jobs/{job_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job_id
    assert data["frame_count"] == 1
    assert data["processed_frame_count"] == 1
    assert data["detection_count"] == 1
    assert data["pending_review_count"] == 1
    assert data["accepted_review_count"] == 0
    assert data["rejected_review_count"] == 0
    assert data["located_detection_count"] == 1

    assert len(data["frames"]) == 1
    assert data["frames"][0]["latitude"] == 21.123

    assert len(data["detections"]) == 1

    detection = data["detections"][0]

    assert detection["class_name"] == "Crab-Pot"
    assert detection["evidence"] is not None
    assert detection["review"] is not None
    assert detection["track"] is not None

    assert detection["evidence"]["evidence_available"] is True
    assert detection["review"]["decision"] == "pending"
    assert detection["track"]["persistence_score"] == 1.0

    decision_response = client.put(
        f"/reviews/{review_id}",
        json={"decision": "accepted"},
    )

    assert decision_response.status_code == 200
    assert decision_response.json()["decision"] == "accepted"

    accepted_report_response = client.get(
        f"/reports/jobs/{job_id}"
    )

    assert accepted_report_response.status_code == 200

    accepted_report = accepted_report_response.json()

    assert accepted_report["pending_review_count"] == 0
    assert accepted_report["accepted_review_count"] == 1
    assert accepted_report["rejected_review_count"] == 0
    assert (
        accepted_report["detections"][0]["review"]["decision"]
        == "accepted"
    )
    assert (
        accepted_report["detections"][0]["review"]["reviewed_at"]
        is not None
    )

    print("Job report endpoint: PASS")
    print("Report frame serialization: PASS")
    print("Report detection serialization: PASS")
    print("Report evidence serialization: PASS")
    print("Report review serialization: PASS")
    print("Report track serialization: PASS")
    print("Job report contract test: PASS")

    cleanup()


if __name__ == "__main__":
    run()
