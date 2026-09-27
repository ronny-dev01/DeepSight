import pytest
from pydantic import ValidationError

from services.api.main import app
from services.api.models.domain import Detection
from services.api.schemas.review import DetectionReviewUpdate


def test_human_review_routes_are_registered_in_openapi():
    paths = app.openapi()["paths"]

    assert "/reviews" in paths
    assert "get" in paths["/reviews"]

    assert "/reviews/job/{job_id}" in paths
    assert "get" in paths["/reviews/job/{job_id}"]

    assert "/reviews/{review_id}" in paths
    assert "get" in paths["/reviews/{review_id}"]
    assert "put" in paths["/reviews/{review_id}"]


def test_review_image_endpoint_is_hidden_from_openapi():
    paths = app.openapi()["paths"]

    assert "/reviews/{review_id}/image" not in paths


def test_review_update_accepts_only_final_decisions():
    assert DetectionReviewUpdate(decision="accepted").decision == "accepted"
    assert DetectionReviewUpdate(decision="rejected").decision == "rejected"

    with pytest.raises(ValidationError):
        DetectionReviewUpdate(decision="pending")


def test_review_note_has_maximum_length():
    DetectionReviewUpdate(
        decision="accepted",
        note="x" * 2000,
    )

    with pytest.raises(ValidationError):
        DetectionReviewUpdate(
            decision="accepted",
            note="x" * 2001,
        )


def test_detection_review_relationship_is_one_to_one():
    relationship = Detection.review.property

    assert relationship.uselist is False
    assert relationship.back_populates == "detection"
