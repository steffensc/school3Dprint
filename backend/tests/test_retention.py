from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.print_job import PrintJob
from app.models.uploaded_file import UploadedFile
from app.models.user import User


def _upload_and_reject(client_as, admin_user: User, normal_user: User, marker: bytes) -> str:
    data = (b"schoolprint-test-" + marker).ljust(80, b"\0") + (0).to_bytes(4, "little")
    upload = client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": "Retention test"},
        files={"file": (f"{uuid.uuid4()}.stl", io.BytesIO(data), "application/octet-stream")},
    )
    job_id = upload.json()["id"]
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/reject")
    return job_id


def _backdate_rejected_at(db_session: Session, job_id: str, days_ago: int) -> None:
    job = db_session.execute(select(PrintJob).where(PrintJob.id == uuid.UUID(job_id))).scalar_one()
    job.rejected_at = datetime.now(UTC) - timedelta(days=days_ago)
    db_session.commit()


def test_get_default_retention_settings(client_as, admin_user: User) -> None:
    response = client_as(admin_user).get("/api/admin/settings/retention")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "retention_days_finished": 90,
        "retention_days_rejected": 30,
        "retention_days_failed": 30,
    }


def test_update_retention_settings_persists(client_as, admin_user: User) -> None:
    response = client_as(admin_user).put(
        "/api/admin/settings/retention", json={"retention_days_rejected": 7}
    )
    assert response.status_code == 200
    assert response.json()["retention_days_rejected"] == 7
    # other fields are left at their defaults when omitted from the request
    assert response.json()["retention_days_finished"] == 90

    refetched = client_as(admin_user).get("/api/admin/settings/retention")
    assert refetched.json()["retention_days_rejected"] == 7


def test_run_retention_deletes_old_rejected_job_file(
    client_as, admin_user: User, normal_user: User, tmp_storage, db_session: Session
) -> None:
    job_id = _upload_and_reject(client_as, admin_user, normal_user, marker=b"OLD")
    _backdate_rejected_at(db_session, job_id, days_ago=31)  # past the 30-day default

    uploaded_file = db_session.execute(
        select(UploadedFile).join(PrintJob).where(PrintJob.id == uuid.UUID(job_id))
    ).scalar_one()
    file_path = Path(uploaded_file.storage_path)
    assert file_path.exists()

    response = client_as(admin_user).post("/api/admin/retention/run")
    assert response.status_code == 200
    assert response.json()["deleted_job_count"] == 1
    assert response.json()["bytes_freed"] > 0

    assert not file_path.exists()
    job = client_as(admin_user).get(f"/api/admin/jobs/{job_id}")
    assert job.json()["status"] == "DELETED"


def test_run_retention_leaves_recent_rejected_job_alone(
    client_as, admin_user: User, normal_user: User, tmp_storage, db_session: Session
) -> None:
    job_id = _upload_and_reject(client_as, admin_user, normal_user, marker=b"RECENT")
    # rejected_at defaults to "now" - well within the retention window

    response = client_as(admin_user).post("/api/admin/retention/run")
    assert response.status_code == 200
    assert response.json()["deleted_job_count"] == 0

    job = client_as(admin_user).get(f"/api/admin/jobs/{job_id}")
    assert job.json()["status"] == "REJECTED"


def test_run_retention_respects_updated_settings(
    client_as, admin_user: User, normal_user: User, tmp_storage, db_session: Session
) -> None:
    job_id = _upload_and_reject(client_as, admin_user, normal_user, marker=b"SHORT")
    _backdate_rejected_at(db_session, job_id, days_ago=10)

    # Still within the 30-day default, so nothing happens yet.
    client_as(admin_user).post("/api/admin/retention/run")
    assert client_as(admin_user).get(f"/api/admin/jobs/{job_id}").json()["status"] == "REJECTED"

    # Shorten the window to 5 days; now the job qualifies.
    client_as(admin_user).put("/api/admin/settings/retention", json={"retention_days_rejected": 5})
    response = client_as(admin_user).post("/api/admin/retention/run")
    assert response.json()["deleted_job_count"] == 1
    assert client_as(admin_user).get(f"/api/admin/jobs/{job_id}").json()["status"] == "DELETED"


def test_storage_overview_reports_pending_retention(
    client_as, admin_user: User, normal_user: User, tmp_storage, db_session: Session
) -> None:
    job_id = _upload_and_reject(client_as, admin_user, normal_user, marker=b"PENDING")
    _backdate_rejected_at(db_session, job_id, days_ago=31)

    response = client_as(admin_user).get("/api/admin/storage/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["jobs_pending_retention"] == 1
    assert body["uploads_bytes"] > 0
    assert body["disk_total_bytes"] > 0


def test_non_admin_cannot_access_retention_endpoints(client_as, normal_user: User) -> None:
    assert client_as(normal_user).get("/api/admin/settings/retention").status_code == 403
    assert client_as(normal_user).post("/api/admin/retention/run").status_code == 403
    assert client_as(normal_user).get("/api/admin/storage/overview").status_code == 403
