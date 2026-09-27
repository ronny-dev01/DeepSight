"""create detection reviews

Revision ID: f3b7c8d91e20
Revises: e1a7c2d94f06
"""

from alembic import op
import sqlalchemy as sa


revision = "f3b7c8d91e20"
down_revision = "e1a7c2d94f06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "detection_reviews",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "detection_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "note",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["detection_id"],
            ["detections.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "decision IN ('pending', 'accepted', 'rejected')",
            name="ck_detection_reviews_decision",
        ),
        sa.UniqueConstraint(
            "detection_id",
            name="uq_detection_reviews_detection_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("detection_reviews")
