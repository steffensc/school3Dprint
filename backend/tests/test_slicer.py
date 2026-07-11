from __future__ import annotations

import io

from app.models.user import User


def _upload_and_approve(
    client_as, admin_user: User, normal_user: User, filename: str, marker: bytes = b""
) -> str:
    data = (b"schoolprint-test-" + marker).ljust(80, b"\0") + (0).to_bytes(4, "little")
    upload_response = client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": "Sliceable"},
        files={"file": (filename, io.BytesIO(data), "application/octet-stream")},
    )
    job_id = upload_response.json()["id"]
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/approve")
    return job_id


def test_slice_success_creates_artifact_and_estimates(
    client_as, admin_user: User, normal_user: User, tmp_storage, fake_slicer
) -> None:
    job_id = _upload_and_approve(client_as, admin_user, normal_user, "robot.stl")

    response = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/slice")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SLICED"
    assert body["estimated_print_time_seconds"] == 3723  # 1h2m3s
    assert body["estimated_filament_grams"] == 12.5


def test_slice_failure_marks_job_failed(
    client_as, admin_user: User, normal_user: User, tmp_storage, fake_slicer
) -> None:
    job_id = _upload_and_approve(
        client_as, admin_user, normal_user, "corrupt.stl", marker=b"MARKER_CORRUPT"
    )

    response = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/slice")
    assert response.status_code == 502

    job = client_as(normal_user).get(f"/api/user/jobs/{job_id}")
    assert job.json()["status"] == "FAILED"


def test_slice_timeout_marks_job_failed(
    client_as, admin_user: User, normal_user: User, tmp_storage, fake_slicer
) -> None:
    job_id = _upload_and_approve(
        client_as, admin_user, normal_user, "hangs.stl", marker=b"MARKER_HANGS"
    )

    response = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/slice")
    assert response.status_code == 502

    job = client_as(normal_user).get(f"/api/user/jobs/{job_id}")
    assert job.json()["status"] == "FAILED"


def test_cannot_slice_unapproved_job(
    client_as, admin_user: User, normal_user: User, tmp_storage, fake_slicer
) -> None:
    data = b"schoolprint-test".ljust(80, b"\0") + (0).to_bytes(4, "little")
    upload_response = client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": "Not approved"},
        files={"file": ("a.stl", io.BytesIO(data), "application/octet-stream")},
    )
    job_id = upload_response.json()["id"]

    response = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/slice")
    assert response.status_code == 409


def test_sliced_job_can_then_be_enqueued(
    client_as, admin_user: User, normal_user: User, tmp_storage, fake_slicer
) -> None:
    job_id = _upload_and_approve(client_as, admin_user, normal_user, "robot.stl")
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/slice")

    response = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")
    assert response.status_code == 200
    assert response.json()["status"] == "QUEUED"
