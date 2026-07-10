from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UpdateRunStatus


class UpdateRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One attempt to install a container update (Section 9.10).

    The backend never performs the privileged `podman pull` /
    `compose up -d` itself; it records the attempt here and delegates the
    actual work to a separate, minimally-privileged Updater process (see
    `app/services/updater_runner.py`), capturing its combined output for
    the admin update log.
    """

    __tablename__ = "update_runs"

    status: Mapped[UpdateRunStatus] = mapped_column(
        Enum(UpdateRunStatus, name="update_run_status"),
        nullable=False,
        default=UpdateRunStatus.PENDING,
    )
    from_version: Mapped[str] = mapped_column(String(64), nullable=False)
    to_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    log: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UpdateRun {self.from_version}->{self.to_version} {self.status.value}>"
