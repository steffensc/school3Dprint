"""Printer CRUD (Section 9.7)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_secret
from app.models.enums import AuditAction
from app.models.printer import Printer
from app.schemas.printer import PrinterCreate, PrinterUpdate
from app.services.audit_service import log_action


def list_printers(db: Session) -> list[Printer]:
    return list(db.execute(select(Printer).order_by(Printer.name)).scalars())


def get_printer(db: Session, printer_id: uuid.UUID) -> Printer | None:
    return db.get(Printer, printer_id)


def create_printer(db: Session, data: PrinterCreate, *, actor_id: uuid.UUID) -> Printer:
    printer = Printer(
        name=data.name,
        driver_type=data.driver_type,
        host=data.host,
        port=data.port,
        serial_number=data.serial_number,
        location=data.location,
        access_code_encrypted=encrypt_secret(data.access_code) if data.access_code else None,
    )
    db.add(printer)
    db.flush()
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.PRINTER_CREATED,
        entity_type="printer",
        entity_id=printer.id,
        metadata={"name": printer.name, "driver_type": printer.driver_type.value},
    )
    db.commit()
    db.refresh(printer)
    return printer


def update_printer(
    db: Session, printer: Printer, data: PrinterUpdate, *, actor_id: uuid.UUID
) -> Printer:
    changed: dict[str, object] = {}
    for field in ("name", "host", "port", "serial_number", "location", "is_active"):
        value = getattr(data, field)
        if value is not None and getattr(printer, field) != value:
            setattr(printer, field, value)
            changed[field] = value

    if data.access_code is not None:
        printer.access_code_encrypted = (
            encrypt_secret(data.access_code) if data.access_code else None
        )
        changed["access_code"] = "updated"

    if changed:
        log_action(
            db,
            actor_id=actor_id,
            action=AuditAction.PRINTER_UPDATED,
            entity_type="printer",
            entity_id=printer.id,
            metadata=changed,
        )
    db.commit()
    db.refresh(printer)
    return printer


def delete_printer(db: Session, printer: Printer, *, actor_id: uuid.UUID) -> None:
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.PRINTER_UPDATED,
        entity_type="printer",
        entity_id=printer.id,
        metadata={"deleted": True, "name": printer.name},
    )
    db.delete(printer)
    db.commit()
