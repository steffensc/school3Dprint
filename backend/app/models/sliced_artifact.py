from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SlicedArtifactType


class SlicedArtifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Output produced by the slicer service for a `PrintJob` (Section 9.6)."""

    __tablename__ = "sliced_artifacts"

    print_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("print_jobs.id"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    artifact_type: Mapped[SlicedArtifactType] = mapped_column(
        Enum(SlicedArtifactType, name="sliced_artifact_type"), nullable=False
    )
    slicer_name: Mapped[str] = mapped_column(String(64), nullable=False, default="orcaslicer")
    slicer_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    profile_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    print_job: Mapped[PrintJob] = relationship(back_populates="sliced_artifacts")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SlicedArtifact {self.artifact_type.value} for {self.print_job_id}>"
