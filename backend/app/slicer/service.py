"""Slicer orchestration: STL -> `.gcode.3mf` (Section 9.6 / 11).

Flow: an approved job is sliced synchronously when a teacher triggers it
(`APPROVED -> SLICING -> SLICED`, or `-> FAILED` on error). The resulting
`.gcode.3mf` becomes a `SlicedArtifact`, and estimated print
time/filament usage are extracted on a best-effort basis.
"""

from __future__ import annotations

import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import AuditAction, SlicedArtifactType
from app.models.enums import PrintJobStatus as Status
from app.models.print_job import PrintJob
from app.models.sliced_artifact import SlicedArtifact
from app.services.audit_service import log_action
from app.services.job_status import assert_transition_allowed
from app.slicer.gcode_metadata import (
    parse_estimated_filament_grams,
    parse_estimated_print_time_seconds,
)
from app.slicer.runner import (
    SlicerBinaryNotFoundError,
    SlicerExecutionError,
    SlicerTimeoutError,
    run_slicer,
)

settings = get_settings()


class SlicingFailedError(Exception):
    pass


def slice_print_job(db: Session, job: PrintJob, *, actor_id: uuid.UUID) -> PrintJob:
    assert_transition_allowed(job.status, Status.SLICING)
    job.status = Status.SLICING
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.SLICING_STARTED,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()

    settings.sliced_dir.mkdir(parents=True, exist_ok=True)
    job_output_dir = settings.sliced_dir / str(job.id)
    job_output_dir.mkdir(parents=True, exist_ok=True)
    output_3mf = job_output_dir / f"{job.id}.gcode.3mf"
    log_path = job_output_dir / "slicer.log"

    input_path = Path(job.uploaded_file.storage_path)

    try:
        with tempfile.TemporaryDirectory(prefix=f"schoolprint-slice-{job.id}-") as work_dir:
            work_input = Path(work_dir) / input_path.name
            shutil.copyfile(input_path, work_input)
            stdout = run_slicer(work_input, output_3mf)
            log_path.write_text(stdout)
    except (SlicerTimeoutError, SlicerExecutionError, SlicerBinaryNotFoundError) as exc:
        log_path.write_text(str(exc))
        job.status = Status.FAILED
        job.failed_at = datetime.now(UTC)
        log_action(
            db,
            actor_id=actor_id,
            action=AuditAction.SLICING_FAILED,
            entity_type="print_job",
            entity_id=job.id,
            metadata={"error": str(exc)},
        )
        db.commit()
        db.refresh(job)
        raise SlicingFailedError(str(exc)) from exc

    artifact = SlicedArtifact(
        print_job_id=job.id,
        file_path=str(output_3mf),
        artifact_type=SlicedArtifactType.GCODE_3MF,
        slicer_name="orcaslicer",
        profile_name="bambu_a1_mini_0.4n_print",
    )
    db.add(artifact)

    estimated_seconds: int | None = None
    estimated_grams: float | None = None
    try:
        artifact_text = output_3mf.read_text(errors="ignore")
        estimated_seconds = parse_estimated_print_time_seconds(artifact_text)
        estimated_grams = parse_estimated_filament_grams(artifact_text)
    except OSError:
        pass

    job.estimated_print_time_seconds = estimated_seconds
    job.estimated_filament_grams = estimated_grams
    job.status = Status.SLICED

    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.SLICING_SUCCEEDED,
        entity_type="print_job",
        entity_id=job.id,
        metadata={
            "estimated_print_time_seconds": estimated_seconds,
            "estimated_filament_grams": estimated_grams,
        },
    )
    db.commit()
    db.refresh(job)
    return job
