from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PrintJobStatus


class PrintJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user's request to print an uploaded STL, moving through the
    status machine described in Section 9.4 of the design document."""

    __tablename__ = "print_jobs"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    uploaded_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=False
    )
    printer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("printers.id"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[PrintJobStatus] = mapped_column(
        Enum(PrintJobStatus, name="print_job_status"),
        nullable=False,
        default=PrintJobStatus.SUBMITTED,
        index=True,
    )
    queue_position: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    teacher_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    estimated_print_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_filament_grams: Mapped[float | None] = mapped_column(nullable=True)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[User] = relationship(  # noqa: F821
        back_populates="print_jobs", foreign_keys=[owner_id]
    )
    uploaded_file: Mapped[UploadedFile] = relationship(  # noqa: F821
        back_populates="print_jobs"
    )
    printer: Mapped[Printer | None] = relationship(back_populates="print_jobs")  # noqa: F821
    sliced_artifacts: Mapped[list[SlicedArtifact]] = relationship(  # noqa: F821
        back_populates="print_job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PrintJob {self.title} ({self.status.value})>"
