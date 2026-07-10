"""Upload handling: validate, store on disk, create DB records
(Section 9.3)."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import AuditAction, PrintJobStatus
from app.models.print_job import PrintJob
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.services.audit_service import log_action
from app.services.stl_validation import InvalidStlError, validate_stl_bytes

settings = get_settings()


class UploadValidationError(Exception):
    """Raised for any user-facing upload validation failure."""


def _normalized_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def create_upload_and_job(
    db: Session,
    *,
    owner: User,
    original_filename: str,
    content_type: str | None,
    data: bytes,
    title: str,
    student_note: str | None,
) -> PrintJob:
    if not original_filename:
        raise UploadValidationError("A filename is required.")

    extension = _normalized_extension(original_filename)
    if extension not in settings.allowed_upload_extensions:
        allowed = ", ".join(settings.allowed_upload_extensions)
        raise UploadValidationError(f"Only {allowed} files are allowed.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) == 0:
        raise UploadValidationError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise UploadValidationError(
            f"File exceeds the maximum allowed size of {settings.max_upload_size_mb} MB."
        )

    try:
        validate_stl_bytes(data)
    except InvalidStlError as exc:
        raise UploadValidationError(str(exc)) from exc

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}{extension}"
    storage_path = settings.uploads_dir / stored_filename
    storage_path.write_bytes(data)

    sha256 = hashlib.sha256(data).hexdigest()
    safe_original_name = Path(original_filename).name

    uploaded_file = UploadedFile(
        owner_id=owner.id,
        original_filename=safe_original_name,
        stored_filename=stored_filename,
        storage_path=str(storage_path),
        content_type=content_type,
        file_size_bytes=len(data),
        sha256=sha256,
    )
    db.add(uploaded_file)
    db.flush()

    job = PrintJob(
        owner_id=owner.id,
        uploaded_file_id=uploaded_file.id,
        title=title.strip() or safe_original_name,
        status=PrintJobStatus.SUBMITTED,
        student_note=student_note,
    )
    db.add(job)
    db.flush()

    log_action(
        db,
        actor_id=owner.id,
        action=AuditAction.JOB_SUBMITTED,
        entity_type="print_job",
        entity_id=job.id,
        metadata={"title": job.title, "original_filename": safe_original_name},
    )
    db.commit()
    db.refresh(job)
    return job
