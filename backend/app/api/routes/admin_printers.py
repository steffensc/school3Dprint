"""Admin printer management + connection test (Section 9.7)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.printer_drivers.base import PrinterDriverError
from app.printer_drivers.factory import UnsupportedDriverError, get_driver
from app.schemas.printer import (
    PrinterCreate,
    PrinterOut,
    PrinterStatusOut,
    PrinterTestResult,
    PrinterUpdate,
)
from app.services import printer_service

router = APIRouter(prefix="/api/admin/printers", tags=["admin-printers"])


def _get_printer_or_404(db: Session, printer_id: uuid.UUID):
    printer = printer_service.get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    return printer


def _to_out(printer) -> PrinterOut:
    out = PrinterOut.model_validate(printer)
    out.has_access_code = bool(printer.access_code_encrypted)
    return out


@router.get("", response_model=list[PrinterOut])
def list_printers(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [_to_out(p) for p in printer_service.list_printers(db)]


@router.post("", response_model=PrinterOut, status_code=status.HTTP_201_CREATED)
def create_printer(
    payload: PrinterCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    printer = printer_service.create_printer(db, payload, actor_id=admin.id)
    return _to_out(printer)


@router.get("/{printer_id}", response_model=PrinterOut)
def get_printer(
    printer_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    return _to_out(_get_printer_or_404(db, printer_id))


@router.patch("/{printer_id}", response_model=PrinterOut)
def update_printer(
    printer_id: uuid.UUID,
    payload: PrinterUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    printer = _get_printer_or_404(db, printer_id)
    printer = printer_service.update_printer(db, printer, payload, actor_id=admin.id)
    return _to_out(printer)


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_printer(
    printer_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    printer = _get_printer_or_404(db, printer_id)
    try:
        printer_service.delete_printer(db, printer, actor_id=admin.id)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Printer cannot be deleted while print jobs reference it.",
        ) from exc


@router.post("/{printer_id}/test-connection", response_model=PrinterTestResult)
def test_connection(
    printer_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    printer = _get_printer_or_404(db, printer_id)
    try:
        driver = get_driver(printer)
        ok = driver.test_connection()
        return PrinterTestResult(success=ok, message="Connected" if ok else "Not reachable")
    except UnsupportedDriverError as exc:
        return PrinterTestResult(success=False, message=str(exc))
    except PrinterDriverError as exc:
        return PrinterTestResult(success=False, message=str(exc))


@router.get("/{printer_id}/status", response_model=PrinterStatusOut)
def get_printer_status(
    printer_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    printer = _get_printer_or_404(db, printer_id)
    try:
        driver = get_driver(printer)
        temps = driver.get_temperatures()
        return PrinterStatusOut(
            status=driver.get_status().value,
            progress=driver.get_progress(),
            nozzle_actual=temps.nozzle_actual,
            nozzle_target=temps.nozzle_target,
            bed_actual=temps.bed_actual,
            bed_target=temps.bed_target,
        )
    except (UnsupportedDriverError, PrinterDriverError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
