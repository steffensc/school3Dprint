from __future__ import annotations

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PrinterDriverType


class Printer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A physical (or dummy) printer known to the system.

    `access_code_encrypted` holds a driver-specific secret (e.g. the Bambu
    LAN access code) encrypted at rest; it is never returned to the
    frontend in plaintext.
    """

    __tablename__ = "printers"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    driver_type: Mapped[PrinterDriverType] = mapped_column(
        Enum(PrinterDriverType, name="printer_driver_type"), nullable=False
    )
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    access_code_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)

    print_jobs: Mapped[list[PrintJob]] = relationship(back_populates="printer")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Printer {self.name} ({self.driver_type.value})>"
